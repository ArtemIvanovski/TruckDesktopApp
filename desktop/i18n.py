# i18n.py
import json
import os


class Translator:
    def __init__(self):
        self.translations = {}
        self.current_lang = 'ru'

    def load_translations(self, lang):
        self.current_lang = lang
        try:
            with open(f'locales/{lang}.json', 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            self.translations = {}

    def tr(self, key):
        return self.translations.get(key, key)


translator = Translator()
translator.load_translations('ru')
