import re
import unicodedata
from typing import Dict, List, Optional, Pattern, Tuple

import pandas as pd


def normalize_text(value: str) -> str:
    value = str(value or '')
    value = value.lower().strip()
    value = unicodedata.normalize('NFKD', value)
    return ''.join(ch for ch in value if not unicodedata.combining(ch))


def build_keyword_patterns(keyword_dictionary: Dict[str, List[str]]) -> Dict[str, Pattern]:
    """Build a single pattern per category (no escaping needed for word boundaries)."""
    patterns: Dict[str, Pattern] = {}
    for category, keywords in keyword_dictionary.items():
        if not keywords:
            continue

        keys = []
        for keyword in keywords:
            normalized = normalize_text(keyword)
            if normalized:
                keys.append(re.escape(normalized))

        if not keys:
            continue

        # Single regex per category, faster than multiple checks
        pattern = re.compile(r"\b(?:" + "|".join(keys) + r")\b")
        patterns[category] = pattern
    return patterns


# Module-level pattern cache
_PATTERN_CACHE: Dict[int, Dict[str, Pattern]] = {}


def recategorize_dataset(df: pd.DataFrame, keyword_dictionary: Dict[str, List[str]]) -> pd.DataFrame:
    """Fast recategorization using vectorized string operations."""
    if 'Nature' not in df.columns or 'Libellé produit' not in df.columns:
        return df
    
    allowed_categories = set(df['Nature'].dropna().unique())
    
    # Build and cache patterns
    dict_key = id(keyword_dictionary)
    if dict_key not in _PATTERN_CACHE:
        _PATTERN_CACHE[dict_key] = build_keyword_patterns(keyword_dictionary)
    
    all_patterns = _PATTERN_CACHE[dict_key]
    patterns = {cat: pat for cat, pat in all_patterns.items() if cat in allowed_categories}

    if not patterns:
        return df

    # Normalize labels once
    labels = df['Libellé produit'].fillna('').astype(str).map(normalize_text)
    current_nature = df['Nature'].copy()

    # Use boolean indexing for speed
    assigned = pd.Series(False, index=df.index)
    result_nature = current_nature.copy()

    # Process categories in order
    for category, pattern in patterns.items():
        # Find unassigned rows that match this category
        not_yet_assigned = ~assigned
        matches = labels.str.contains(pattern, na=False, regex=True)
        new_matches = not_yet_assigned & matches & (current_nature != category)

        # Assign matching rows
        if new_matches.any():
            result_nature.loc[new_matches] = category
            assigned.loc[new_matches] = True

    # Update the dataframe only where changes occurred
    changed = result_nature != current_nature
    if changed.any():
        df.loc[changed, 'Nature'] = result_nature.loc[changed]
        updated_count = int(changed.sum())
        print(f"✅ Recatégorisation effectuée : {updated_count} lignes corrigées.")
    else:
        print(f"✅ Recatégorisation effectuée : 0 lignes corrigées.")

    return df


def recategoriser_dataset(df: pd.DataFrame, keyword_dictionary: Dict[str, List[str]]) -> pd.DataFrame:
    return recategorize_dataset(df, keyword_dictionary)