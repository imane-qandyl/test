#!/usr/bin/env python3
"""Entry point for cleaning the ecommerce dataset.

Usage:
  python main.py [input.xlsb] --out data/processed

This script reads a binary Excel file (.xlsb), applies category corrections
and extractors, then writes a cleaned .xlsx file.
"""
from pathlib import Path
import argparse
import pandas as pd

from src.config import DICTIONNAIRE_CATEGORIES
from src.classifiers import recategoriser_dataset
from src.extractors import extraire_dimensions, extraire_couleurs, extract_dimensions_series, extract_couleurs_series

def process_file(input_path: Path, output_dir: Path) -> None:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Source file not found: {input_path}")

    print("📥 Chargement du dataset...")
    # Requires 'pyxlsb' engine for .xlsb files
    df = pd.read_excel(input_path, engine='pyxlsb')

    print("🔄 Recherche des anomalies de catégories...")
    df = recategoriser_dataset(df, DICTIONNAIRE_CATEGORIES)

    print("🎨 Extraction des dimensions et des couleurs en cours...")
    # vectorized extractors (much faster on large DataFrames)
    df['Dimension_Extraite'] = extract_dimensions_series(df['Libellé produit'])
    df['Couleur_Extraite'] = extract_couleurs_series(df['Libellé produit'])

    # Ensure expected types/format
    if 'Cod_cmd' in df.columns:
        df['Cod_cmd'] = df['Cod_cmd'].astype(str)

    if 'Date de commande' in df.columns:
        df['Date de commande'] = pd.to_datetime(
            df['Date de commande'], unit='D', origin='1899-12-30', errors='coerce'
        ).dt.strftime('%d/%m/%Y')

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{input_path.stem} CLEAN.xlsx"

    print("💾 Enregistrement du fichier de données nettoyé...")
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"✨ Succès ! Le fichier propre est disponible ici : {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean ecommerce dataset")
    parser.add_argument(
        "input",
        nargs='?',
        default="data/raw/20210614 Ecommerce sales.xlsb",
        help="Input .xlsb file path",
    )
    parser.add_argument("--out", "-o", default="data/processed", help="Output directory")
    args = parser.parse_args()

    process_file(Path(args.input), Path(args.out))


if __name__ == "__main__":
    main()