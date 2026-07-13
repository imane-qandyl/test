# Script de recatégorisation — conçu pour rester lisible et facile à suivre.
"""Détecte et corrige les anomalies de la colonne `Nature` en se basant
sur un dictionnaire de mots-clés.

Le code n'ajoute pas de nouvelles catégories : il n'assigne que des
catégories déjà présentes dans le jeu de données.
"""
import pandas as pd
from typing import Dict, List


def recategoriser_dataset(df: pd.DataFrame, dictionnaire_mots_cles: Dict[str, List[str]]) -> pd.DataFrame:
    """Parcourt le DataFrame et corrige `Nature` quand un mot-clé correspond.

    Retourne le DataFrame modifié et affiche un résumé succinct.
    """
    categories_autorisees = set(df['Nature'].dropna().unique())
    compteur = 0

    for idx, row in df.iterrows():
        libelle = str(row.get('Libellé produit', '')).lower()
        categorie_actuelle = row.get('Nature')
        nouvelle = None

        for cat, mots in dictionnaire_mots_cles.items():
            if any(m in libelle for m in mots):
                if cat in categories_autorisees:
                    nouvelle = cat
                    break

        if nouvelle and nouvelle != categorie_actuelle:
            df.at[idx, 'Nature'] = nouvelle
            compteur += 1

    print(f"✅ Recatégorisation effectuée : {compteur} lignes corrigées.")
    return df