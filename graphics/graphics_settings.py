import json
import logging
import os
from core.i18n import tr
from utils.setting_deploy import get_resource_path

logger = logging.getLogger(__name__)


class LightingMode:
    HEMISPHERIC = "hemispheric"
    BRIGHT = "bright"
    SOFT = "soft"
    DRAMATIC = "dramatic"
    SUNSET = "sunset"


def get_lighting_presets():
    """Получить переводы для режимов освещения"""
    return {
        LightingMode.HEMISPHERIC: {
            "name": tr("Полусферическое (по умолчанию)"),
            "main_intensity": 1.5,
            "fill_intensity": 0.8,
            "main_hpr": (-45, -45, 0),
            "fill_hpr": (135, 45, 0)
        },
        LightingMode.BRIGHT: {
            "name": tr("Яркое студийное"),
            "main_intensity": 2.2,
            "fill_intensity": 1.8,
            "main_hpr": (-30, -60, 0),
            "fill_hpr": (150, 30, 0)
        },
        LightingMode.SOFT: {
            "name": tr("Мягкое рассеянное"),
            "main_intensity": 1.0,
            "fill_intensity": 1.2,
            "main_hpr": (-60, -30, 0),
            "fill_hpr": (120, 60, 0)
        },
        LightingMode.DRAMATIC: {
            "name": tr("Драматическое"),
            "main_intensity": 2.8,
            "fill_intensity": 0.3,
            "main_hpr": (-90, -45, 0),
            "fill_hpr": (90, 45, 0)
        },
        LightingMode.SUNSET: {
            "name": tr("Закатное"),
            "main_intensity": 1.8,
            "fill_intensity": 0.6,
            "main_hpr": (-15, -75, 0),
            "fill_hpr": (165, 15, 0)
        }
    }

# Для обратной совместимости
LIGHTING_PRESETS = get_lighting_presets()


class GraphicsSettings:
    def __init__(self):
        self.lighting_mode = LightingMode.HEMISPHERIC
        self.enable_specular = False

        # Цвет фона (текущий серый)
        self.background_color = (0.35, 0.35, 0.35)

        # Цвет тягача (голубо-синий из M_Body материала)
        self.truck_color = (0.185151, 0.322308, 0.535714)

        # Интенсивность освещения
        self.main_light_intensity = 1.5
        self.fill_light_intensity = 0.8

        # Углы освещения
        self.main_light_hpr = (-45, -45, 0)
        self.fill_light_hpr = (135, 45, 0)

        # Включено ли освещение
        self.lighting_enabled = True

    def to_dict(self):
        """Сериализация настроек в словарь"""
        return {
            'enable_specular': self.enable_specular,
            'background_color': self.background_color,
            'truck_color': self.truck_color,
            'main_light_intensity': self.main_light_intensity,
            'fill_light_intensity': self.fill_light_intensity,
            'main_light_hpr': self.main_light_hpr,
            'fill_light_hpr': self.fill_light_hpr,
            'lighting_enabled': self.lighting_enabled
        }

    def from_dict(self, data):
        """Десериализация настроек из словаря"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def save_to_file(self, filepath="config/graphics_settings.json"):
        """Сохранить настройки в файл"""
        try:
            abs_path = get_resource_path(filepath)
            with open(abs_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Graphics settings saved to {abs_path}")
        except Exception as e:
            logger.error(f"Failed to save graphics settings: {e}")

    def load_from_file(self, filepath="config/graphics_settings.json"):
        """Загрузить настройки из файла"""
        try:
            abs_path = get_resource_path(filepath)
            if os.path.exists(abs_path):
                with open(abs_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.from_dict(data)
                logger.info(f"Graphics settings loaded from {abs_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to load graphics settings: {e}")
        return False
