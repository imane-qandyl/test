import re
import unicodedata
from typing import Dict, List, Optional, Pattern, Tuple
import pandas as pd

from src.config import COLOR_NAMES, COLOR_NORMALIZATION

def normalize_text(text: str) -> str:
    value = str(text or '').lower()
    value = unicodedata.normalize('NFKD', value)
    return ''.join(ch for ch in value if not unicodedata.combining(ch))


def build_color_matcher() -> Tuple[Dict[str, str], Optional[Pattern[str]]]:
    mapping: Dict[str, str] = {}
    keys: List[str] = []
    for keyword, canon in COLOR_NORMALIZATION.items():
        normalized_key = normalize_text(keyword)
        if not normalized_key:
            continue
        if normalized_key not in mapping:
            mapping[normalized_key] = canon
        keys.append(normalized_key)

    unique_keys = sorted(set(keys), key=len, reverse=True)
    if not unique_keys:
        return mapping, None

    pattern = re.compile(r"\b(?:" + "|".join(re.escape(key) for key in unique_keys) + r")\b")
    return mapping, pattern

COLOR_MAP, COLOR_PATTERN = build_color_matcher()

def extract_colors_from_normalized_text(text: str) -> str:
    found: List[str] = []
    seen = set()
    if not COLOR_PATTERN:
        return 'Non spécifiée'

    for match in COLOR_PATTERN.finditer(str(text or '')):
        canon = COLOR_MAP.get(match.group(0), match.group(0).capitalize())
        if canon not in seen:
            seen.add(canon)
            found.append(canon)

    return ' - '.join(found) if found else 'Non spécifiée'

NON_DIMENSION_WORDS = {
    'niveaux', 'couches', 'tiroirs', 'portes', 'personnes', 'compartiments', 'cubes',
    'zones', 'ampoules', 'etageres', 'etages', 'litres', 'litre', 'l', 'kg', 'gr', 'g', 'ml',
    'x', 'xx', 'xxx'
}

# Pre-compile dimension patterns at module load time
_PATTERN_TRIPLE = re.compile(r"(?<![a-z0-9])(\d+(?:[.,]\d+)?)\s*(?:x|\*)\s*(\d+(?:[.,]\d+)?)\s*(?:x|\*)\s*(\d+(?:[.,]\d+)?)(?:\s*cm)?(?![a-z0-9])")
_PATTERN_DOUBLE = re.compile(r"(?<![a-z0-9])(\d+(?:[.,]\d+)?)\s*(?:x|\*)\s*(\d+(?:[.,]\d+)?)(?:\s*cm)?(?![a-z0-9])")
_PATTERN_CM = re.compile(r"(?<![a-z0-9])(\d+(?:[.,]\d+)?)\s*cm(?![a-z0-9])")
_PATTERN_PLUS = re.compile(r"(?<![a-z0-9])(\d+(?:[.,]\d+)?)\s*\+(?![a-z0-9])")
_PATTERN_SIGNAL = re.compile(r"(?<![a-z0-9])\d+(?:[.,]\d+)?\s*(?:cm|\+|x|\*)(?![a-z0-9])")
_PATTERN_NUMBER = re.compile(r"(?<![a-z0-9])(\d+(?:[.,]\d+)?)(?![a-z0-9])")

def build_dimension_output(values: List[str]) -> str:
    return " / ".join(values) if values else "Non spécifiée"

def looks_like_dimension_context(text: str, start: int, end: int) -> bool:
    snippet = text[max(0, start - 20):min(len(text), end + 20)].lower()
    return any(token in snippet for token in ['cm', 'hauteur', 'largeur', 'longueur', 'profondeur', 'dimension', 'dimensions'])

def should_skip_candidate(text: str, match: re.Match[str]) -> bool:
    next_text = text[match.end():].lstrip()
    if not next_text:
        return False

    if next_text.startswith(('cm', 'c', 'l', 'g', 'm', 'k')) and len(next_text) <= 2:
        return True

    token_match = re.match(r"([a-z]+)", next_text)
    if token_match and token_match.group(1).lower() in NON_DIMENSION_WORDS:
        return True

    previous_token = text[:match.start()].rstrip().split()[-1] if text[:match.start()].split() else ''
    if previous_token.lower() in NON_DIMENSION_WORDS:
        return True

    return False

def extract_dimensions(label: str) -> str:
    """Return one or more readable dimensions or 'Non spécifiée'."""
    # Early exit for empty or numeric-less labels
    if not label or not any(c.isdigit() for c in str(label)):
        return "Non spécifiée"
    
    normalized_text = normalize_text(label)
    if not normalized_text:
        return "Non spécifiée"

    has_dimension_signal = bool(_PATTERN_SIGNAL.search(normalized_text))
    
    candidates: List[Tuple[int, int, str]] = []
    spans: List[Tuple[int, int]] = []
    
    # Check for triple dimensions
    triple_matches = list(_PATTERN_TRIPLE.finditer(normalized_text))
    
    if triple_matches:
        for match in triple_matches:
            if not should_skip_candidate(normalized_text, match):
                value = f"{match.group(1)}x{match.group(2)}x{match.group(3)}"
                candidates.append((match.start(), match.end(), value))
                spans.append((match.start(), match.end()))
    else:
        # Check for double dimensions
        for match in _PATTERN_DOUBLE.finditer(normalized_text):
            if not should_skip_candidate(normalized_text, match):
                value = f"{match.group(1)}x{match.group(2)}"
                candidates.append((match.start(), match.end(), value))
                spans.append((match.start(), match.end()))
        
        # Check for cm values
        for match in _PATTERN_CM.finditer(normalized_text):
            if not should_skip_candidate(normalized_text, match):
                value = f"{match.group(1)} cm"
                candidates.append((match.start(), match.end(), value))
                spans.append((match.start(), match.end()))
        
        # Check for plus values
        for match in _PATTERN_PLUS.finditer(normalized_text):
            if not should_skip_candidate(normalized_text, match):
                value = f"{match.group(1)}+"
                candidates.append((match.start(), match.end(), value))
                spans.append((match.start(), match.end()))

    # If dimension signal detected, also check for standalone numbers
    if has_dimension_signal and not candidates:
        for match in _PATTERN_NUMBER.finditer(normalized_text):
            if should_skip_candidate(normalized_text, match):
                continue
            if any(match.start() < end and match.end() > start for start, end in spans):
                continue
            if not looks_like_dimension_context(normalized_text, match.start(), match.end()):
                if not re.search(r"(?:^|\s)\d+(?:[.,]\d+)?\s+\d+(?:[.,]\d+)?", normalized_text[max(0, match.start()-20):match.end()+20]):
                    continue
            if len(match.group(1)) <= 2 and triple_matches:
                continue
            candidates.append((match.start(), match.end(), match.group(1)))

    if not candidates:
        return "Non spécifiée"

    candidates.sort(key=lambda item: item[0])

    values: List[str] = []
    for _, _, value in candidates:
        if value not in values:
            values.append(value)

    return build_dimension_output(values)

def extract_colors(label: str) -> str:
    """Return 'Color1 - Color2' or 'Non spécifiée'."""
    return extract_colors_from_normalized_text(normalize_text(label))

def extraire_dimensions(label: str) -> str:
    return extract_dimensions(label)

def extraire_couleurs(label: str) -> str:
    return extract_colors(label)

def extract_dimensions_series(series: pd.Series) -> pd.Series:
    """Fast vectorized dimension extraction with early filtering."""
    labels = series.fillna('').astype(str)
    
    # Early filter: skip rows without digits
    has_digits = labels.str.contains(r'\d', regex=True, na=False)
    
    result = pd.Series('Non spécifiée', index=labels.index)
    
    if has_digits.any():
        result.loc[has_digits] = labels.loc[has_digits].map(extract_dimensions)
    
    return result

def extract_colors_series(series: pd.Series) -> pd.Series:
    normalized_series = series.fillna('').astype(str)
    
    # Early filter: skip empty or very short values
    has_content = normalized_series.str.len() > 2
    
    if not COLOR_NAMES or not COLOR_PATTERN:
        return pd.Series('Non spécifiée', index=normalized_series.index)

    # Only process non-empty values
    result = pd.Series('Non spécifiée', index=normalized_series.index)
    
    if has_content.any():
        # Normalize only the non-empty values
        normalized_filtered = normalized_series[has_content].map(normalize_text)
        found = normalized_filtered.str.findall(COLOR_PATTERN)

        def map_colors_norm(items):
            seen = []
            seen_set = set()
            for item in items:
                canon = COLOR_MAP.get(item, item.capitalize())
                if canon not in seen_set:
                    seen_set.add(canon)
                    seen.append(canon)
            return ' - '.join(seen) if seen else 'Non spécifiée'

        result.loc[has_content] = found.apply(map_colors_norm)
    
    return result