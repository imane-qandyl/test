# Ecommerce Dataset Cleaning

This repository contains a small data-cleaning pipeline for an ecommerce
sales dataset. It reads a binary Excel file (.xlsb), applies category
corrections and text extractors (dimensions and colors), and writes a
cleaned Excel file (.xlsx).

Prerequisites
 - Python 3.8+
 - See `requirements.txt` for required packages

Quickstart

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the cleaner (uses defaults if no arguments provided):

```bash
python main.py data/raw/20210614\ Ecommerce\ sales.xlsb --out data/processed
```

Files of interest
 - `main.py`: CLI entrypoint and workflow
 - `src/classifiers.py`: category correction logic
 - `src/extractors.py`: regex-based extractors for dimensions/colors
 - `src/config.py`: keyword lists and normalization maps

Notes
 - The .xlsb reader requires the `pyxlsb` engine.
 - Processed files are written to `data/processed/` by default.
