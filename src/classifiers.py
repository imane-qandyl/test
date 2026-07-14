import re
import unicodedata
from typing import Dict, List, Optional, Pattern, Tuple

import pandas as pd


def normalize_text(value: str) -> str:
    value = str(value or '')
    value = value.lower().strip()
    value = unicodedata.normalize('NFKD', value)
    return ''.join(ch for ch in value if not unicodedata.combining(ch))


def build_keyword_patterns(keyword_dictionary: Dict[str, List[str]]) -> Tuple[List[Tuple[str, Pattern]], Optional[Pattern]]:
    """Build category patterns and a combined pattern for fast matching."""
    patterns: List[Tuple[str, Pattern]] = []
    all_keys = []
    category_map: Dict[str, str] = {}

    for category, keywords in keyword_dictionary.items():
        if not keywords:
            continue

        keys = []
        for keyword in keywords:
            normalized = normalize_text(keyword)
            if normalized:
                escaped = re.escape(normalized)
                keys.append(escaped)
                category_map[escaped] = category

        if not keys:
            continue

        pattern = re.compile(r"\b(?:" + "|".join(keys) + r")\b")
        patterns.append((category, pattern))
        all_keys.extend(keys)

    # Pre-compile a combined pattern for faster matching
    combined_pattern = None
    if all_keys:
        unique_keys = sorted(set(all_keys), key=len, reverse=True)
        combined_pattern = re.compile(r"\b(?:" + "|".join(unique_keys) + r")\b")

    return patterns, combined_pattern


# Module-level pattern cache
_PATTERN_CACHE: Dict[str, Tuple[List[Tuple[str, Pattern]], Optional[Pattern]]] = {}

def recategorize_dataset(df: pd.DataFrame, keyword_dictionary: Dict[str, List[str]]) -> pd.DataFrame:
    """Recategorization that only touches rows whose current Nature does NOT
    match its own keywords — genuinely correct rows are left untouched."""
    allowed_categories = set(df['Nature'].dropna().unique())
    dict_key = id(keyword_dictionary)
    if dict_key not in _PATTERN_CACHE:
        _PATTERN_CACHE[dict_key] = build_keyword_patterns(keyword_dictionary)
    all_patterns, _ = _PATTERN_CACHE[dict_key]
    category_pattern_map = {cat: pat for cat, pat in all_patterns if cat in allowed_categories}

    if not category_pattern_map:
        return df

    labels = df['Libellé produit'].fillna('').astype(str).map(normalize_text)
    current_nature = df['Nature']

    # 1) Check whether each row's CURRENT category still matches its own keywords.
    #    Grouping by current Nature keeps this vectorized (one .str.contains per category,
    #    only on that category's own rows) instead of a Python loop over 525k rows.
    already_ok = pd.Series(False, index=df.index)
    for category, idx in current_nature.dropna().groupby(current_nature).groups.items():
        pattern = category_pattern_map.get(category)
        if pattern is None:
            continue  # category has no keywords defined -> can't verify, leave as-is
        matches = labels.loc[idx].str.contains(pattern, na=False, regex=True)
        already_ok.loc[idx[matches]] = True

    # Rows with no keywords for their category at all -> also leave untouched (can't verify -> trust it)
    has_verifiable_category = current_nature.isin(category_pattern_map.keys())
    needs_check = ~already_ok & (has_verifiable_category | current_nature.isna())

    # 2) Only for rows that failed their own category's check (or have no Nature),
    #    search for a better match — first match by dict order, as before.
    assigned = pd.Series(pd.NA, index=df.index, dtype='object')
    remaining = needs_check.copy()
    for category, pattern in all_patterns:
        if category not in allowed_categories or not remaining.any():
            continue
        matches = labels.loc[remaining].str.contains(pattern, na=False, regex=True)
        matched_idx = matches[matches].index
        assigned.loc[matched_idx] = category
        remaining.loc[matched_idx] = False

    should_update = assigned.notna() & (assigned != current_nature)
    updated_count = int(should_update.sum())
    if updated_count:
        df.loc[should_update, 'Nature'] = assigned.loc[should_update]

    print(f"✅ Recatégorisation effectuée : {updated_count} lignes corrigées.")
    return df

def recategoriser_dataset(df: pd.DataFrame, keyword_dictionary: Dict[str, List[str]]) -> pd.DataFrame:
    return recategorize_dataset(df, keyword_dictionary)