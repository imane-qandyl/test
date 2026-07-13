# Contient l'algo RegEx (extraction dimensions & couleurs)
import re
from src.config import LISTE_COULEURS, NORMALISATION_COULEURS

def extraire_dimensions(libelle):
    """
    Parcourt le libellé pour trouver les dimensions :
    1. Cherche d'abord un format double (ex: 140x190) -> Renvoie '140*190'
    2. Si absent, cherche une dimension unique en cm (ex: 140 cm) -> Renvoie '140'
    """
    libelle_clean = str(libelle).lower()
    
    # --- RÈGLE 1 : Recherche d'une double dimension (Largeur x Longueur) ---
    pattern_double = r'(\d{2,3})\s*(?:x|\*)\s*(\d{2,3})'
    match_double = re.search(pattern_double, libelle_clean)
    if match_double:
        return f"{match_double.group(1)}*{match_double.group(2)}"
        
    pattern_single = r'\b(\d{2,3})\s*cm\b'
    match_single = re.search(pattern_single, libelle_clean)
    if match_single:
        return match_single.group(1)
        
    return "Non spécifiée"

def extraire_couleurs(libelle):
    """
    Identifie TOUTES les couleurs présentes dans le texte dans leur ordre d'apparition
    et les rassemble (ex: 'Blanc - Gris').
    """
    libelle_clean = str(libelle).lower()
    couleurs_trouvees = []
    
    # On parcourt le texte mot par mot ou par blocs pour trouver toutes les correspondances
    for couleur in LISTE_COULEURS:
        if re.search(r'\b' + couleur + r'\b', libelle_clean):
            nom_propre = NORMALISATION_COULEURS.get(couleur, couleur.capitalize())
            # Évite d'ajouter des doublons (ex: si le libellé contient "blanc" et "blanche")
            if nom_propre not in couleurs_trouvees:
                couleurs_trouvees.append(nom_propre)
                
    if couleurs_trouvees:
        # On les fusionne proprement avec un séparateur
        return " - ".join(couleurs_trouvees)
        
    return "Non spécifiée"