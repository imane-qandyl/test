# Centralise les listes de couleurs et dictionnaires de catégories

# Configuration des catégories et de leurs mots-clés associés
DICTIONNAIRE_CATEGORIES = {
    "Table basse": ["table basse", "table de salon", "table basse carree"],
    "Canapé": ["canape", "sofa", "clic clac", "convertible"],
    "Chaise": ["chaise", "chaises", "tabouret"],
    "Matelas": ["matelas", "sommier", "literie"]
}

# Liste des couleurs prises en charge
LISTE_COULEURS = [
    'noir', 'noire', 'noires', 'blanc', 'blanche', 'blanches', 
    'gris', 'grise', 'grises', 'bleu', 'rouge', 'vert', 'jaune', 'bois'
]

# Dictionnaire de normalisation des couleurs
NORMALISATION_COULEURS = {
    'noire': 'Noir', 'noires': 'Noir', 'noir': 'Noir',
    'blanche': 'Blanc', 'blanches': 'Blanc', 'blanc': 'Blanc',
    'grise': 'Gris', 'grises': 'Gris', 'gris': 'Gris',
    'bleue': 'Bleu', 'bleu': 'Bleu',
    'verte': 'Vert', 'vert': 'Vert',
    'rouge': 'Rouge', 'jaune': 'Jaune', 'bois': 'Bois'
}