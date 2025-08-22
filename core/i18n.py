import json
import os
from typing import Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal


class TranslationManager(QObject):
    language_changed = pyqtSignal(str)
    
    _instance: Optional['TranslationManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        super().__init__()
        if hasattr(self, '_initialized'):
            return
        self._translations_cache: Dict[str, Dict[str, str]] = {}
        self._current_language = 'ru'
        self._settings_file = 'language_settings.json'
        self._available_languages = {
            'ru': 'Русский',
            'en': 'English'
        }
        self._load_settings()
        self._load_language(self._current_language)
        self._initialized = True
    
    def _load_settings(self):
        if os.path.exists(self._settings_file):
            try:
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                self._current_language = settings.get('language', 'ru')
            except:
                pass
    
    def _save_settings(self):
        settings = {'language': self._current_language}
        with open(self._settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f)
    
    def _load_language(self, language: str):
        if language in self._translations_cache:
            return
        
        file_path = f'locales/{language}.json'
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._translations_cache[language] = json.load(f)
            except:
                self._translations_cache[language] = {}
        else:
            self._translations_cache[language] = {}
    
    def set_language(self, language: str):
        if language == self._current_language:
            return
        
        if language not in self._available_languages:
            return
        
        self._load_language(language)
        self._current_language = language
        self._save_settings()
        self.language_changed.emit(language)
    
    def get_current_language(self) -> str:
        return self._current_language
    
    def get_available_languages(self) -> Dict[str, str]:
        return self._available_languages.copy()
    
    def tr(self, key: str) -> str:
        if self._current_language not in self._translations_cache:
            self._load_language(self._current_language)
        
        return self._translations_cache.get(self._current_language, {}).get(key, key)


translation_manager = TranslationManager()


def tr(key: str) -> str:
    return translation_manager.tr(key)


class TranslatableMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        translation_manager.language_changed.connect(self.retranslate_ui)
    
    def retranslate_ui(self):
        pass
