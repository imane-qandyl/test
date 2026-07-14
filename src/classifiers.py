import pandas as pd
from typing import Dict, List, Pattern, Tuple
import re
import unicodedata


def normalize_text(s: str) -> str:
    s = str(s or '')
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    return ''.join(ch for ch in s if not unicodedata.combining(ch))


def build_patterns(dictionnaire_mots_cles: Dict[str, List[str]]) -> List[Tuple[str, Pattern]]:
    patterns: List[Tuple[str, Pattern]] = []
    for cat, mots in dictionnaire_mots_cles.items():
        if not mots:
            continue
        # normalize and escape keywords
        keys = []
        for m in mots:
            nm = normalize_text(m)
            if not nm:
                continue
            keys.append(re.escape(nm))
        if not keys:
            continue
        # word-boundary pattern to avoid partial matches
        pat = re.compile(r"\b(?:" + "|".join(keys) + r")\b")
        patterns.append((cat, pat))
    return patterns


def recategoriser_dataset(df: pd.DataFrame, dictionnaire_mots_cles: Dict[str, List[str]]) -> pd.DataFrame:
    categories_autorisees = set(df['Nature'].dropna().unique())
    patterns = [(cat, pat) for cat, pat in build_patterns(dictionnaire_mots_cles) if cat in categories_autorisees]

    labels = df['Libellé produit'].fillna('').astype(str).map(normalize_text)
    current_nature = df['Nature']

    assigned = pd.Series(pd.NA, index=df.index, dtype='object')
    for cat, pat in patterns:
        can_assign = assigned.isna()
        if not can_assign.any():
            break
        matches = labels.str.contains(pat, na=False)
        assigned.loc[can_assign & matches] = cat

    should_update = assigned.notna() & (assigned != current_nature)
    compteur = int(should_update.sum())
    if compteur:
        df.loc[should_update, 'Nature'] = assigned.loc[should_update]

    print(f"✅ Recatégorisation effectuée : {compteur} lignes corrigées.")
    return df