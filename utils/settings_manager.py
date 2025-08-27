import json
import os
from typing import Any, Dict

from utils.setting_deploy import get_resource_path


class SettingsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_singleton()
        return cls._instance

    def _init_singleton(self):
        self.settings_path = get_resource_path('config/settings.json')
        self.data: Dict[str, Any] = {}
        self._ensure_loaded()

    def _ensure_loaded(self):
        if os.path.exists(self.settings_path):
            self._load()
            return
        self._bootstrap_from_legacy()
        self._save()

    def _load(self):
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception:
            self.data = {}

    def _save(self):
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _bootstrap_from_legacy(self):
        self.data = {
            'language': {'language': 'ru'},
            'units': {'distance_unit': 'cm', 'weight_unit': 'kg'},
            'load_calculation': {},
            'graphics': {}
        }

        try:
            lang_path = get_resource_path('language_settings.json')
            if os.path.exists(lang_path):
                with open(lang_path, 'r', encoding='utf-8') as f:
                    self.data['language'] = json.load(f)
        except Exception:
            pass

        try:
            units_path = get_resource_path('units_settings.json')
            if os.path.exists(units_path):
                with open(units_path, 'r', encoding='utf-8') as f:
                    self.data['units'] = json.load(f)
        except Exception:
            pass

        try:
            lc_path = get_resource_path('load_calculation_settings.json')
            if os.path.exists(lc_path):
                with open(lc_path, 'r', encoding='utf-8') as f:
                    self.data['load_calculation'] = json.load(f)
        except Exception:
            pass

        try:
            gfx_path = get_resource_path('config/graphics_settings.json')
            if os.path.exists(gfx_path):
                with open(gfx_path, 'r', encoding='utf-8') as f:
                    self.data['graphics'] = json.load(f)
        except Exception:
            pass

    def get_section(self, section: str) -> Dict[str, Any]:
        return dict(self.data.get(section, {}))

    def update_section(self, section: str, values: Dict[str, Any]):
        current = self.data.get(section, {})
        current.update(values or {})
        self.data[section] = current
        self._save()

    def set_value(self, section: str, key: str, value: Any):
        sec = self.data.get(section, {})
        sec[key] = value
        self.data[section] = sec
        self._save()


