from pathlib import Path
import json


def _is_hex_color_key(value: str) -> bool:
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

            normal = {}
            liste = []
            for raw_key, canon in data.items():
                if not canon:
                    continue
                alias_key = str(raw_key).strip().lower()
                canon_name = str(canon).strip()
                if not canon_name:
                    continue

                canonical_key = canon_name.lower()

                if _is_hex_color_key(alias_key):
                    if canonical_key not in normal:
                        normal[canonical_key] = canon_name
                    if canonical_key not in liste:
                        liste.append(canonical_key)
                    continue

                if alias_key not in normal:
                    normal[alias_key] = canon_name
                if alias_key not in liste:
                    liste.append(alias_key)

                if canonical_key not in normal:
                    normal[canonical_key] = canon_name
                if canonical_key not in liste:
                    liste.append(canonical_key)

            return liste, normal
        except Exception:
            # Fall back to empty mappings on any error.
            return [], {}
    return [], {}


LISTE_COULEURS, NORMALISATION_COULEURS = load_colors()


def load_categories():
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


DICTIONNAIRE_CATEGORIES = load_categories()