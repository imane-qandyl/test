# Script de recatégorisation — conçu pour rester lisible et facile à suivre.
"""Détecte et corrige les anomalies de la colonne `Nature` en se basant
sur un dictionnaire de mots-clés.

Le code n'ajoute pas de nouvelles catégories : il n'assigne que des
catégories déjà présentes dans le jeu de données.
"""
import pandas as pd
from typing import Dict, List, Pattern, Tuple
import re
import unicodedata


def _normalize_text(s: str) -> str:
    s = str(s or '')
    s = s.lower().strip()
    s = unicodedata.normalize('NFKD', s)
    return ''.join(ch for ch in s if not unicodedata.combining(ch))


def _build_patterns(dictionnaire_mots_cles: Dict[str, List[str]]) -> List[Tuple[str, Pattern]]:
    patterns: List[Tuple[str, Pattern]] = []
    for cat, mots in dictionnaire_mots_cles.items():
        if not mots:
            continue
        # normalize and escape keywords
        keys = []
        for m in mots:
            nm = _normalize_text(m)
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
    """Parcourt le DataFrame et corrige `Nature` en utilisant des regex normalisés.

    Matching uses accent-stripped, lowercased keywords with word boundaries to
    reduce false positives. Categories are only assigned if they already exist
    in the dataset (preserves previous behavior).
    """
    categories_autorisees = set(df['Nature'].dropna().unique())
    compteur = 0

    patterns = _build_patterns(dictionnaire_mots_cles)

    for idx, row in df.iterrows():
        libelle = _normalize_text(row.get('Libellé produit', ''))
        categorie_actuelle = row.get('Nature')
        nouvelle = None

        for cat, pat in patterns:
            if pat.search(libelle):
                if cat in categories_autorisees:
                    nouvelle = cat
                    break

        if nouvelle and nouvelle != categorie_actuelle:
            df.at[idx, 'Nature'] = nouvelle
            compteur += 1

    print(f"✅ Recatégorisation effectuée : {compteur} lignes corrigées.")
    return df