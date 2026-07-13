"""Algorithmes d'extraction lisibles (dimensions & couleurs).

Les fonctions sont conçues pour être simples et explicites — faciles à
modifier ou étendre pour de nouveaux formats.
"""
import re
from typing import List
import pandas as pd

from src.config import LISTE_COULEURS, NORMALISATION_COULEURS


def extraire_dimensions(libelle: str) -> str:
    """Retourne une dimension extraite ou 'Non spécifiée'.

    Exemples reconnus : '140x190', '140 x 190', '140 cm'.
    """
    s = str(libelle).lower()

    # Recherche width x height
    m = re.search(r"(\d{2,3})\s*(?:x|\*)\s*(\d{2,3})", s)
    if m:
        return f"{m.group(1)}*{m.group(2)}"

    # Recherche d'une seule valeur en cm
    m = re.search(r"\b(\d{2,3})\s*cm\b", s)
    if m:
        return m.group(1)

    return "Non spécifiée"


def extraire_couleurs(libelle: str) -> str:
    """Liste et normalise les couleurs trouvées (ordre d'apparition).

    Renvoie 'Couleur1 - Couleur2' ou 'Non spécifiée'.
    """
    s = str(libelle).lower()
    trouvees: List[str] = []

    for couleur in LISTE_COULEURS:
        if re.search(r"\b" + re.escape(couleur) + r"\b", s):
            nom = NORMALISATION_COULEURS.get(couleur, couleur.capitalize())
            if nom not in trouvees:
                trouvees.append(nom)

    return " - ".join(trouvees) if trouvees else "Non spécifiée"


def extract_dimensions_series(series: pd.Series) -> pd.Series:
    s = series.fillna('').astype(str).str.lower()
    # double dimension
    m = s.str.extract(r"(\d{2,3})\s*(?:x|\*)\s*(\d{2,3})")
    res = pd.Series(pd.NA, index=s.index)
    mask_double = m[0].notna()
    if mask_double.any():
        res.loc[mask_double] = m.loc[mask_double, 0].astype(str) + '*' + m.loc[mask_double, 1].astype(str)

    # single cm
    single = s.str.extract(r"\b(\d{2,3})\s*cm\b")[0]
    res = res.fillna(single)

    return res.fillna("Non spécifiée")


def extract_couleurs_series(series: pd.Series) -> pd.Series:
    # normalize function: lowercase + strip accents
    def _norm(text: str) -> str:
        t = str(text or '').lower()
        t = __import__('unicodedata').normalize('NFKD', t)
        return ''.join(ch for ch in t if not __import__('unicodedata').combining(ch))

    s_norm = series.fillna('').astype(str).map(_norm)
    if not LISTE_COULEURS:
        return pd.Series("Non spécifiée", index=s_norm.index)

    # build mapping from normalized keyword -> canonical name
    mapping_norm = {}
    norm_keys = []
    for k, canon in NORMALISATION_COULEURS.items():
        nk = _norm(k)
        mapping_norm[nk] = canon
        norm_keys.append(nk)

    pattern = r"\b(?:" + "|".join(re.escape(c) for c in sorted(set(norm_keys), key=len, reverse=True)) + r")\b"
    found = s_norm.str.findall(pattern)

    def map_colors_norm(lst):
        seen = []
        for x in lst:
            canon = mapping_norm.get(x, x.capitalize())
            if canon not in seen:
                seen.append(canon)
        return " - ".join(seen) if seen else "Non spécifiée"

    return found.apply(map_colors_norm)