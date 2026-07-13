"""Algorithmes d'extraction lisibles (dimensions & couleurs).

Les fonctions sont conçues pour être simples et explicites — faciles à
modifier ou étendre pour de nouveaux formats.
"""
import re
from typing import List

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