"""Project configuration: categories and color maps.

This module exposes `DICTIONNAIRE_CATEGORIES`, `LISTE_COULEURS` and
`NORMALISATION_COULEURS`. If `data/dictionaries/colors.json` exists it
will be loaded to provide a large, maintainable color dictionary.
"""
from pathlib import Path
import json

# Minimal fallback list of color synonyms (lowercased). The normalization
# mapping is built dynamically from this list to avoid maintaining two
# duplicated constants.
_FALLBACK_LISTE = [
    'noire', 'noires', 'noir',
    'blanche', 'blanches', 'blanc',
    'grise', 'grises', 'gris',
    'bleue', 'bleu',
    'verte', 'vert',
    'rouge', 'jaune', 'bois'
]


def _load_colors():
    root = Path(__file__).resolve().parents[1]
    json_path = root / 'data' / 'dictionaries' / 'colors.json'
    if json_path.exists():
        try:
            with json_path.open(encoding='utf-8') as fh:
                data = json.load(fh)
            # The JSON maps codes (hex/RAL) -> canonical French names.
            # Build a usable mapping for text matching: include the
            # canonical name (lowercased) and its word tokens as keys
            # so product labels containing 'blanc' or 'bois' will match.
            import re

            normal = {}
            liste = []
            for code, canon in data.items():
                if not canon:
                    continue
                key = str(canon).strip().lower()
                # add full canonical name
                normal[key] = canon
                if key not in liste:
                    liste.append(key)
                # add constituent words (e.g. 'blanc' from 'Blanc gris')
                # but avoid adding generic stopwords (de, et, pour...) or
                # non-color tokens like 'salle' unless they are present as
                # explicit keys in the source JSON or equal a canonical name.
                stopwords = {'de', 'et', 'la', 'le', 'les', 'pour', 'avec', 'sans', 'en', 'du', 'au', 'aux', 'a'}
                data_keys = {str(k).strip().lower() for k in data.keys()}
                for tok in re.findall(r"[\wÀ-ÿ]+", key):
                    tok = tok.strip()
                    if not tok or len(tok) <= 2:
                        continue
                    if tok in stopwords:
                        continue
                    # only add token if it appears as an explicit synonym key
                    # in the JSON, or if it equals the canonical name, or if
                    # it is in the fallback shortlist
                    if tok in data_keys or tok == key or tok in _FALLBACK_LISTE:
                        if tok not in normal:
                            normal[tok] = tok.capitalize()
                        if tok not in liste:
                            liste.append(tok)

            # ensure basic fallbacks are present
            for fb in _FALLBACK_LISTE:
                if fb not in normal:
                    normal[fb] = fb.capitalize()
                    if fb not in liste:
                        liste.append(fb)

            return liste, normal
        except Exception:
            # Fall back to defaults on any error
            return _FALLBACK_LISTE, {k: k.capitalize() for k in _FALLBACK_LISTE}
    return _FALLBACK_LISTE, {k: k.capitalize() for k in _FALLBACK_LISTE}


LISTE_COULEURS, NORMALISATION_COULEURS = _load_colors()


def _load_categories():
    root = Path(__file__).resolve().parents[1]
    json_path = root / 'data' / 'dictionaries' / 'categories.json'
    # fallback curated mapping
    fallback = {
        "Table basse": ["table basse", "table de salon", "table basse carree"],
        "Canapé": ["canape", "sofa", "clic clac", "convertible"],
        "Chaise": ["chaise", "chaises", "tabouret"],
        "Matelas": ["matelas", "sommier", "literie"],
    }

    if json_path.exists():
        try:
            with json_path.open(encoding='utf-8') as fh:
                data = json.load(fh)
            cleaned = {}
            for cat, kws in data.items():
                if isinstance(kws, list):
                    cleaned[cat] = [str(k).strip().lower() for k in kws if str(k).strip()]
                else:
                    cleaned[cat] = [p.strip().lower() for p in str(kws).split(',') if p.strip()]
            return cleaned
        except Exception:
            return fallback
    return fallback


DICTIONNAIRE_CATEGORIES = _load_categories()