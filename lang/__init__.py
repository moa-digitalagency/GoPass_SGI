import json
import os

class Translator:
    def __init__(self, default_lang='fr'):
        self.default_lang = default_lang
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        lang_dir = os.path.dirname(__file__)
        for filename in os.listdir(lang_dir):
            if filename.endswith('.json'):
                lang_code = filename[:-5]
                filepath = os.path.join(lang_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
    
    def get(self, key, lang=None):
        if lang is None:
            lang = self.default_lang
        
        if lang in self.translations:
            keys = key.split('.')
            value = self.translations[lang]
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return key
            return value
        return key

translator = Translator()

def t(key, lang=None):
    return translator.get(key, lang)
