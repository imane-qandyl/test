from pathlib import Path
import json


def is_hex_color_key(value: str) -> bool:
    if not value:
        return False
    if value.startswith('#'):
        value = value[1:]
    if len(value) != 6:
        return False
    return all(ch in '0123456789abcdefABCDEF' for ch in value)


def load_colors():
    root = Path(__file__).resolve().parents[1]
    json_path = root / 'data' / 'dictionaries' / 'colors.json'
    if json_path.exists():
        try:
            with json_path.open(encoding='utf-8') as fh:
                data = json.load(fh)

            color_mapping = {}
            color_names = []
            for raw_key, canon in data.items():
                if not canon:
                    continue
                alias_key = str(raw_key).strip().lower()
                canon_name = str(canon).strip()
                if not canon_name:
                    continue

                canonical_key = canon_name.lower()

                if is_hex_color_key(alias_key):
                    if canonical_key not in color_mapping:
                        color_mapping[canonical_key] = canon_name
                    if canonical_key not in color_names:
                        color_names.append(canonical_key)
                    continue

                if alias_key not in color_mapping:
                    color_mapping[alias_key] = canon_name
                if alias_key not in color_names:
                    color_names.append(alias_key)

                if canonical_key not in color_mapping:
                    color_mapping[canonical_key] = canon_name
                if canonical_key not in color_names:
                    color_names.append(canonical_key)

            return color_names, color_mapping
        except Exception:
            return [], {}
    return [], {}


COLOR_NAMES, COLOR_NORMALIZATION = load_colors()
LISTE_COULEURS = COLOR_NAMES
NORMALISATION_COULEURS = COLOR_NORMALIZATION


def load_categories():
    root = Path(__file__).resolve().parents[1]
    json_path = root / 'data' / 'dictionaries' / 'categories.json'
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
            for category, keywords in data.items():
                if isinstance(keywords, list):
                    cleaned[category] = [str(keyword).strip().lower() for keyword in keywords if str(keyword).strip()]
                else:
                    cleaned[category] = [keyword.strip().lower() for keyword in str(keywords).split(',') if keyword.strip()]
            return cleaned
        except Exception:
            return fallback
    return fallback


CATEGORY_DICTIONARY = load_categories()
DICTIONNAIRE_CATEGORIES = CATEGORY_DICTIONARY