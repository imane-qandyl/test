import re
import unicodedata
from typing import Dict, List, Optional, Pattern, Tuple
import pandas as pd

from src.config import LISTE_COULEURS, NORMALISATION_COULEURS


def _normalize_text(text: str) -> str:
    t = str(text or '').lower()
    t = unicodedata.normalize('NFKD', t)
    return ''.join(ch for ch in t if not unicodedata.combining(ch))


def _build_color_matcher() -> Tuple[Dict[str, str], Optional[Pattern[str]]]:
    mapping: Dict[str, str] = {}
    keys: List[str] = []
    for keyword, canon in NORMALISATION_COULEURS.items():
        nk = _normalize_text(keyword)
        if not nk:
            continue
        if nk not in mapping:
            mapping[nk] = canon
        keys.append(nk)

    uniq_keys = sorted(set(keys), key=len, reverse=True)
    if not uniq_keys:
        return mapping, None

    pattern = re.compile(r"\b(?:" + "|".join(re.escape(k) for k in uniq_keys) + r")\b")
    return mapping, pattern


_COLOR_MAP, _COLOR_PATTERN = _build_color_matcher()


def _extract_colors_from_normalized_text(text: str) -> str:
    found: List[str] = []
    seen = set()
    if not _COLOR_PATTERN:
        return 'Non spécifiée'

    for match in _COLOR_PATTERN.finditer(str(text or '')):
        canon = _COLOR_MAP.get(match.group(0), match.group(0).capitalize())
        if canon not in seen:
            seen.add(canon)
            found.append(canon)

    return ' - '.join(found) if found else 'Non spécifiée'


NON_DIMENSION_WORDS = {
    'niveaux', 'couches', 'tiroirs', 'portes', 'personnes', 'compartiments', 'cubes',
    'zones', 'ampoules', 'etageres', 'etages', 'litres', 'litre', 'l', 'kg', 'gr', 'g', 'ml',
    'x', 'xx', 'xxx'
}


def _build_dimension_output(values: List[str]) -> str:
    return " / ".join(values) if values else "Non spécifiée"


def _looks_like_dimension_context(text: str, start: int, end: int) -> bool:
    snippet = text[max(0, start - 20):min(len(text), end + 20)].lower()
    return any(token in snippet for token in ['cm', 'hauteur', 'largeur', 'longueur', 'profondeur', 'dimension', 'dimensions'])


def _should_skip_candidate(text: str, match: re.Match[str]) -> bool:
    after = text[match.end():]
    after = after.lstrip()
    if not after:
        return False

    if after.startswith(('cm', 'c', 'l', 'g', 'm', 'k')) and len(after) <= 2:
        return True

    token_match = re.match(r"([a-z]+)", after)
    if token_match and token_match.group(1).lower() in NON_DIMENSION_WORDS:
        return True

    before = text[:match.start()].rstrip().split()[-1] if text[:match.start()].split() else ''
    if before.lower() in NON_DIMENSION_WORDS:
        return True

    return False


def extraire_dimensions(libelle: str) -> str:
    """Retourne une ou plusieurs dimensions lisibles ou 'Non spécifiée'."""
    s = _normalize_text(libelle)
    if not s:
        return "Non spécifiée"

    has_dimension_signal = bool(re.search(r"(?<![a-z0-9])\d+(?:[.,]\d+)?\s*(?:cm|\+|x|\*)(?![a-z0-9])", s))
    patterns = [
        (re.compile(r"(?<![a-z0-9])(\d+(?:[.,]\d+)?)\s*(?:x|\*)\s*(\d+(?:[.,]\d+)?)\s*(?:x|\*)\s*(\d+(?:[.,]\d+)?)(?:\s*cm)?(?![a-z0-9])"), 'triple'),
        (re.compile(r"(?<![a-z0-9])(\d+(?:[.,]\d+)?)\s*(?:x|\*)\s*(\d+(?:[.,]\d+)?)(?:\s*cm)?(?![a-z0-9])"), 'double'),
        (re.compile(r"(?<![a-z0-9])(\d+(?:[.,]\d+)?)\s*cm(?![a-z0-9])"), 'cm'),
        (re.compile(r"(?<![a-z0-9])(\d+(?:[.,]\d+)?)\s*\+(?![a-z0-9])"), 'plus'),
    ]

    candidates: List[Tuple[int, int, str]] = []
    spans: List[Tuple[int, int]] = []
    triple_matches = [match for pattern, kind in patterns if kind == 'triple' for match in pattern.finditer(s)]
    for pattern, kind in patterns:
        for match in pattern.finditer(s):
            if _should_skip_candidate(s, match):
                continue
            if triple_matches and kind != 'triple':
                continue
            if kind == 'double' and match.group(0).endswith('cm'):
                value = f"{match.group(1)}x{match.group(2)}"
            elif kind == 'double':
                value = f"{match.group(1)}x{match.group(2)}"
            elif kind == 'triple':
                value = f"{match.group(1)}x{match.group(2)}x{match.group(3)}"
            elif kind == 'cm':
                value = f"{match.group(1)} cm"
            else:
                value = f"{match.group(1)}+"
            candidates.append((match.start(), match.end(), value))
            spans.append((match.start(), match.end()))

    if has_dimension_signal:
        for match in re.finditer(r"(?<![a-z0-9])(\d+(?:[.,]\d+)?)(?![a-z0-9])", s):
            if _should_skip_candidate(s, match):
                continue
            if any(match.start() < end and match.end() > start for start, end in spans):
                continue
            if not _looks_like_dimension_context(s, match.start(), match.end()):
                if not re.search(r"(?:^|\s)\d+(?:[.,]\d+)?\s+\d+(?:[.,]\d+)?", s[max(0, match.start()-20):match.end()+20]):
                    continue
            if len(match.group(1)) <= 2 and triple_matches:
                continue
            candidates.append((match.start(), match.end(), match.group(1)))

    candidates.sort(key=lambda item: item[0])

    values: List[str] = []
    for _, _, value in candidates:
        if value in values:
            continue
        values.append(value)

    return _build_dimension_output(values)


def extraire_couleurs(libelle: str) -> str:
    """Renvoie 'Couleur1 - Couleur2' ou 'Non spécifiée'."""
    return _extract_colors_from_normalized_text(_normalize_text(libelle))


def extract_dimensions_series(series: pd.Series) -> pd.Series:
    return series.fillna('').astype(str).map(extraire_dimensions)


def extract_couleurs_series(series: pd.Series) -> pd.Series:
    s_norm = series.fillna('').astype(str).map(_normalize_text)
    if not LISTE_COULEURS or not _COLOR_PATTERN:
        return pd.Series('Non spécifiée', index=s_norm.index)

    found = s_norm.str.findall(_COLOR_PATTERN)

    def map_colors_norm(lst):
        seen = []
        seen_set = set()
        for x in lst:
            canon = _COLOR_MAP.get(x, x.capitalize())
            if canon not in seen_set:
                seen_set.add(canon)
                seen.append(canon)
        return ' - '.join(seen) if seen else 'Non spécifiée'

    return found.apply(map_colors_norm)