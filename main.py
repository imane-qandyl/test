# main.py
import os
import pandas as pd
from src.config import DICTIONNAIRE_CATEGORIES
from src.classifiers import recategoriser_dataset
from src.extractors import extraire_dimensions, extraire_couleurs

def main():
    # Chemins de fichiers de l'arborescence
    fichier_entree = "data/raw/20210614 Ecommerce sales.xlsb"
    dossier_sortie = "data/processed"
    fichier_sortie = os.path.join(dossier_sortie, "20210614 Ecommerce sales CLEAN.xlsx")
    
    print("--- Début du traitement du test technique ---")
    
    # 1. Lecture robuste du fichier Excel binaire (.xlsb)
    if not os.path.exists(fichier_entree):
        raise FileNotFoundError(f"Le fichier source est introuvable dans {fichier_entree}. Veuillez vérifier son emplacement.")
        
    print("📥 Chargement du dataset binaire...")
    # Note : Nécessite l'installation du moteur 'pyxlsb'
    df = pd.read_excel(fichier_entree, engine='pyxlsb')
    
    # 2. Exécution de l'algorithme de recatégorisation de la Nature
    print("🔄 Recherche des anomalies de catégories...")
    df = recategoriser_dataset(df, DICTIONNAIRE_CATEGORIES)
    
    # 3. Application des extracteurs intelligents
    print("🎨 Extraction des dimensions et des couleurs en cours...")
    df['Dimension_Extraite'] = df['Libellé produit'].apply(extraire_dimensions)
    df['Couleur_Extraite'] = df['Libellé produit'].apply(extraire_couleurs)

    df['Cod_cmd'] = df['Cod_cmd'].astype(str)

    df['Date de commande'] = pd.to_datetime(df['Date de commande'], unit='D', origin='1899-12-30', errors='coerce').dt.strftime('%d/%m/%Y')    
    # 4. Sauvegarde finale au format standard Excel
    print("💾 Enregistrement du fichier de données nettoyé...")
    os.makedirs(dossier_sortie, exist_ok=True)
    df.to_excel(fichier_sortie, index=False, engine='openpyxl')
    
    print(f"✨ Succès ! Le fichier propre est disponible ici : {fichier_sortie}")

if __name__ == "__main__":
    main()