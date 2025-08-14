from panda3d.core import DirectionalLight
import logging
import json
import os

logger = logging.getLogger(__name__)


class LightingMode:
    HEMISPHERIC = "hemispheric"
    BRIGHT = "bright"
    SOFT = "soft"
    DRAMATIC = "dramatic"
    SUNSET = "sunset"


LIGHTING_PRESETS = {
    LightingMode.HEMISPHERIC: {
        "name": "Полусферическое (по умолчанию)",
        "main_intensity": 1.5,
        "fill_intensity": 0.8,
        "main_hpr": (-45, -45, 0),
        "fill_hpr": (135, 45, 0)
    },
    LightingMode.BRIGHT: {
        "name": "Яркое студийное",
        "main_intensity": 2.2,
        "fill_intensity": 1.8,
        "main_hpr": (-30, -60, 0),
        "fill_hpr": (150, 30, 0)
    },
    LightingMode.SOFT: {
        "name": "Мягкое рассеянное",
        "main_intensity": 1.0,
        "fill_intensity": 1.2,
        "main_hpr": (-60, -30, 0),
        "fill_hpr": (120, 60, 0)
    },
    LightingMode.DRAMATIC: {
        "name": "Драматическое",
        "main_intensity": 2.8,
        "fill_intensity": 0.3,
        "main_hpr": (-90, -45, 0),
        "fill_hpr": (90, 45, 0)
    },
    LightingMode.SUNSET: {
        "name": "Закатное",
        "main_intensity": 1.8,
        "fill_intensity": 0.6,
        "main_hpr": (-15, -75, 0),
        "fill_hpr": (165, 15, 0)
    }
}


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

    def save_to_file(self, filepath="graphics_settings.json"):
        """Сохранить настройки в файл"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Graphics settings saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save graphics settings: {e}")

    def load_from_file(self, filepath="graphics_settings.json"):
        """Загрузить настройки из файла"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.from_dict(data)
                logger.info(f"Graphics settings loaded from {filepath}")
                return True
        except Exception as e:
            logger.error(f"Failed to load graphics settings: {e}")
        return False


class GraphicsManager:
    def __init__(self, app):
        self.app = app
        self.settings = GraphicsSettings()
        self.main_light = None
        self.fill_light = None
        self.main_light_np = None
        self.fill_light_np = None

        # Попытаться загрузить настройки при инициализации
        self.load_settings()

    def load_settings(self, filepath="graphics_settings.json"):
        """Загрузить настройки из файла"""
        if self.settings.load_from_file(filepath):
            # Применить загруженные настройки
            self.apply_all_settings()

    def save_settings(self, filepath="graphics_settings.json"):
        """Сохранить текущие настройки в файл"""
        self.settings.save_to_file(filepath)

    def apply_all_settings(self):
        try:
            self.setup_lighting()

            r, g, b = self.settings.background_color
            self.app.setBackgroundColor(r, g, b)

            if hasattr(self.app, 'wheel_model') and self.app.wheel_model and not self.app.wheel_model.isEmpty():
                self._update_model_specular(self.app.wheel_model, self.settings.enable_specular)
                r, g, b = self.settings.truck_color
                self._update_truck_model_color(self.app.wheel_model, r, g, b)

            if hasattr(self.app, 'lorry_model') and self.app.lorry_model and not self.app.lorry_model.isEmpty():
                self._update_model_specular(self.app.lorry_model, self.settings.enable_specular)
                r, g, b = self.settings.truck_color
                self._update_truck_model_color(self.app.lorry_model, r, g, b)

            logger.info("All graphics settings applied successfully")

        except Exception as e:
            logger.error(f"Failed to apply all graphics settings: {e}")

    def setup_lighting(self):
        self.app.render.clearLight()

        if self.settings.lighting_enabled:
            preset = LIGHTING_PRESETS.get(self.settings.lighting_mode, LIGHTING_PRESETS[LightingMode.HEMISPHERIC])

            self.main_light = DirectionalLight('hemispheric_main')
            self.main_light.setColor((preset["main_intensity"], preset["main_intensity"], preset["main_intensity"], 1))
            self.main_light_np = self.app.render.attachNewNode(self.main_light)
            self.main_light_np.setHpr(*preset["main_hpr"])
            self.app.render.setLight(self.main_light_np)

            self.fill_light = DirectionalLight('hemispheric_fill')
            self.fill_light.setColor((preset["fill_intensity"], preset["fill_intensity"], preset["fill_intensity"], 1))
            self.fill_light_np = self.app.render.attachNewNode(self.fill_light)
            self.fill_light_np.setHpr(*preset["fill_hpr"])
            self.app.render.setLight(self.fill_light_np)

    def set_lighting_mode(self, mode):
        self.settings.lighting_mode = mode
        self.setup_lighting()
        self.save_settings()

    def update_lighting(self):
        """Обновить освещение с текущими настройками"""
        self.setup_lighting()

    def set_lighting_enabled(self, enabled):
        """Включить/выключить освещение"""
        self.settings.lighting_enabled = enabled
        self.update_lighting()

    def set_light_intensity(self, main_intensity, fill_intensity):
        """Установить интенсивность освещения"""
        self.settings.main_light_intensity = main_intensity
        self.settings.fill_light_intensity = fill_intensity
        self.update_lighting()

    def set_background_color(self, r, g, b):
        """Установить цвет фона"""
        self.settings.background_color = (r, g, b)
        self.app.setBackgroundColor(r, g, b)

    def set_specular_enabled(self, enabled):
        """Включить/выключить блики для всех моделей"""
        self.settings.enable_specular = enabled

        # Обновить блики для колеса
        if hasattr(self.app, 'wheel_model') and self.app.wheel_model:
            self._update_model_specular(self.app.wheel_model, enabled)

        # Обновить блики для кабины
        if hasattr(self.app, 'lorry_model') and self.app.lorry_model:
            self._update_model_specular(self.app.lorry_model, enabled)

    def set_truck_color(self, r, g, b):
        """Установить цвет тягача (материал M_Body)"""
        self.settings.truck_color = (r, g, b)

        # Обновить цвет кабины
        if hasattr(self.app, 'lorry_model') and self.app.lorry_model:
            self._update_truck_model_color(self.app.lorry_model, r, g, b)

        # Обновить цвет колеса (если тоже использует M_Body)
        if hasattr(self.app, 'wheel_model') and self.app.wheel_model:
            self._update_truck_model_color(self.app.wheel_model, r, g, b)

    def _update_model_specular(self, model, enabled):
        """Обновить блики для конкретной модели"""
        if not model or model.isEmpty():
            return

        from panda3d.core import Vec4

        specular_value = Vec4(1, 1, 1, 1) if enabled else Vec4(0, 0, 0, 1)

        # Обновить все материалы модели
        materials = model.findAllMaterials()
        for material in materials:
            material.setSpecular(specular_value)

        # Обновить материалы всех узлов
        for node in model.findAllMatches("**"):
            if node.hasMaterial():
                mat = node.getMaterial()
                mat.setSpecular(specular_value)

    def _update_truck_model_color(self, model, r, g, b):
        """Обновить цвет тягача для конкретной модели"""
        if not model or model.isEmpty():
            return

        from panda3d.core import Vec4

        # Ищем материал M_Body и обновляем его диффузный цвет
        materials = model.findAllMaterials()
        updated = False
        for material in materials:
            try:
                # Проверяем по текущему цвету (голубо-синий M_Body материал)
                current_diffuse = material.getDiffuse()
                if (abs(current_diffuse.x - 0.185151) < 0.01 and
                        abs(current_diffuse.y - 0.322308) < 0.01 and
                        abs(current_diffuse.z - 0.535714) < 0.01):
                    material.setDiffuse(Vec4(r, g, b, 1))
                    logger.info(f"Updated truck color for material to RGB({r:.3f}, {g:.3f}, {b:.3f})")
                    updated = True
            except Exception as e:
                logger.warning(f"Could not check material diffuse color: {e}")
                continue

        # Также обновляем узлы с более тщательной проверкой
        for node in model.findAllMatches("**"):
            if node.hasMaterial():
                mat = node.getMaterial()
                try:
                    # Проверяем по диффузному цвету (голубо-синий M_Body материал)
                    current_diffuse = mat.getDiffuse()
                    if (abs(current_diffuse.x - 0.185151) < 0.01 and
                            abs(current_diffuse.y - 0.322308) < 0.01 and
                            abs(current_diffuse.z - 0.535714) < 0.01):
                        mat.setDiffuse(Vec4(r, g, b, 1))
                        logger.info(f"Updated truck color for node material to RGB({r:.3f}, {g:.3f}, {b:.3f})")
                        updated = True
                except Exception as e:
                    logger.warning(f"Could not check node material diffuse color: {e}")
                    continue

        if not updated:
            logger.warning(f"No truck materials found to update (looking for RGB(47, 82, 137))")

        # Дополнительная попытка поиска по имени материала для OBJ/MTL файлов
        try:
            from panda3d.core import RenderState
            # Попробуем найти узлы с именами, содержащими "Body" или "body"
            body_nodes = model.findAllMatches("**/+RenderState")
            for node in body_nodes:
                node_name = node.getName().lower()
                if 'body' in node_name or 'm_body' in node_name:
                    if node.hasMaterial():
                        mat = node.getMaterial()
                        mat.setDiffuse(Vec4(r, g, b, 1))
                        logger.info(
                            f"Updated truck color for named node '{node.getName()}' to RGB({r:.3f}, {g:.3f}, {b:.3f})")
                        updated = True
        except Exception as e:
            logger.debug(f"Could not search by node names: {e}")

    def get_graphics_settings(self):
        """Получить текущие настройки графики"""
        return self.settings

    def update_graphics_settings(self, **kwargs):
        """Обновить настройки графики"""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)

        # Применить изменения
        if 'background_color' in kwargs:
            r, g, b = self.settings.background_color
            self.set_background_color(r, g, b)

        if 'enable_specular' in kwargs:
            self.set_specular_enabled(self.settings.enable_specular)

        if 'truck_color' in kwargs:
            r, g, b = self.settings.truck_color
            self.set_truck_color(r, g, b)

        if any(key in kwargs for key in ['main_light_intensity', 'fill_light_intensity', 'lighting_enabled']):
            self.update_lighting()

        # Автосохранение настроек
        self.save_settings()

    def reset_graphics_settings(self):
        """Сбросить настройки графики до заводских"""
        self.settings = GraphicsSettings()

        # Применить сброшенные настройки
        self.apply_all_settings()

        # Сохранить сброшенные настройки
        self.save_settings()
