# Contient l'algo de recatégorisation (correction de la colonne Nature)
# Ce script analyse le libellé produit et corrige la colonne Nature si elle contient une erreur ou une valeur manquante.

import pandas as pd

def recategoriser_dataset(df, dictionnaire_mots_cles):
    """
    Détecte les anomalies de catégorisation et applique les corrections automatiques.
    Ne crée aucune nouvelle catégorie (utilise uniquement les catégories présentes).
    """
    categories_autorisees = set(df['Nature'].dropna().unique())
    
    compteur_corrections = 0
    
    # Parcours ligne par ligne du DataFrame
    for index, row in df.iterrows():
        libelle_clean = str(row['Libellé produit']).lower()
        categorie_actuelle = row['Nature']
        nouvelle_categorie = None
        
        # Recherche d'une correspondance par mot-clé
        for categorie_cible, mots_cles in dictionnaire_mots_cles.items():
            if any(mot in libelle_clean for mot in mots_cles):
                # Sécurité réglementaire du test : Vérifier que la catégorie existe déjà
                if categorie_cible in categories_autorisees:
                    nouvelle_categorie = categorie_cible
                    break
        
        # Si une catégorie est détectée et qu'elle diffère de l'ancienne (ou si l'ancienne est vide)
        if nouvelle_categorie and nouvelle_categorie != categorie_actuelle:
            df.at[index, 'Nature'] = nouvelle_categorie
            compteur_corrections += 1
            
    print(f"✅ Recatégorisation effectuée avec succès : {compteur_corrections} lignes corrigées.")
    return df