import logging

from panda3d.core import DirectionalLight

from graphics.graphics_settings import GraphicsSettings, LIGHTING_PRESETS, LightingMode
from utils.settings_manager import SettingsManager

logger = logging.getLogger(__name__)


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

    def load_settings(self, filepath="config/graphics_settings.json"):
        data = SettingsManager().get_section('graphics')
        if data:
            self.settings.from_dict(data)
            self.apply_all_settings()

    def save_settings(self, filepath="config/graphics_settings.json"):
        SettingsManager().update_section('graphics', self.settings.to_dict())

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

            self._apply_grid()

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

        if any(key in kwargs for key in ['grid_enabled', 'grid_opacity', 'grid_color', 'grid_spacing_x_cm', 'grid_spacing_y_cm']):
            self._apply_grid()

        # Автосохранение настроек
        self.save_settings()

    def reset_graphics_settings(self):
        """Сбросить настройки графики до заводских"""
        self.settings = GraphicsSettings()

        # Применить сброшенные настройки
        self.apply_all_settings()

        # Сохранить сброшенные настройки
        self.save_settings()

    def _apply_grid(self):
        try:
            if not hasattr(self.app, 'scene') or not self.app.scene:
                return
            s = self.settings
            if hasattr(self.app.scene, 'update_grid'):
                self.app.scene.update_grid(
                    enabled=bool(s.grid_enabled),
                    color=tuple(s.grid_color),
                    opacity=float(s.grid_opacity),
                    spacing_x_cm=int(s.grid_spacing_x_cm),
                    spacing_y_cm=int(s.grid_spacing_y_cm)
                )
        except Exception as e:
            logger.error(f"Failed to apply grid settings: {e}")

    def set_grid_enabled(self, enabled: bool):
        self.settings.grid_enabled = bool(enabled)
        self._apply_grid()
        self.save_settings()

    def set_grid_opacity(self, opacity: float):
        self.settings.grid_opacity = max(0.0, min(1.0, float(opacity)))
        self._apply_grid()
        self.save_settings()

    def set_grid_color(self, r: float, g: float, b: float):
        self.settings.grid_color = (float(r), float(g), float(b))
        self._apply_grid()
        self.save_settings()

    def set_grid_spacing(self, spacing_x_cm: int, spacing_y_cm: int):
        self.settings.grid_spacing_x_cm = max(1, int(spacing_x_cm))
        self.settings.grid_spacing_y_cm = max(1, int(spacing_y_cm))
        self._apply_grid()
        self.save_settings()

    def reset_grid_settings(self):
        self.settings.grid_enabled = False
        self.settings.grid_opacity = 0.3
        self.settings.grid_color = (0.2, 0.6, 1.0)
        self.settings.grid_spacing_x_cm = 10
        self.settings.grid_spacing_y_cm = 10
        self._apply_grid()
        self.save_settings()