import json
import os
from flask import current_app, session, request

_translations = {}

def load_translations():
    """Loads translation files from locales/ directory."""
    global _translations
    locales_dir = os.path.join(os.getcwd(), 'locales')
    for lang in ['fr', 'en']:
        file_path = os.path.join(locales_dir, f'{lang}.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                _translations[lang] = json.load(f)
        else:
            _translations[lang] = {}

def get_text(key, lang=None):
    """
    Retrieves the translation for the given dotted key (e.g., 'auth.login_btn').
    Uses 'lang' if provided, otherwise checks session or defaults to 'fr'.
    """
    if not _translations:
        load_translations()

    if lang is None:
        # Try to get from session, fallback to 'fr'
        lang = session.get('lang', 'fr')

    # Recursive lookup
    keys = key.split('.')

    # Try requested language
    value = _translations.get(lang, {})
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            value = None
            break

    if value is not None:
        return value

    # Fallback to French
    if lang != 'fr':
        value = _translations.get('fr', {})
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
        if value is not None:
            return value

    # Fallback to key
    return key
