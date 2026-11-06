"""Shared, reviewed-copy locale data; no model-generated customer-facing prose."""
import json
from pathlib import Path
LOCALES=json.loads((Path(__file__).resolve().parent/'public/locales.json').read_text())
LANGUAGES=tuple(dict.fromkeys(('en','hi',*LOCALES)))
def language_code(value):
    return value if value in LANGUAGES else 'en'
