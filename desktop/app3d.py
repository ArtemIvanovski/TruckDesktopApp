#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import sys
import traceback
from typing import Optional, Tuple

from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Filename, Material
from panda3d.core import (
    WindowProperties,
    AntialiasAttrib,
    TextNode,
)

from camera import ArcCamera
from config import BACKGROUND_COLOR, LANG, WHEEL_CABIN_HEIGHT
from i18n import t
from graphics_settings import GraphicsManager
from truck import TruckScene

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_gltf_support():
    try:
        logger.info("Доступные загрузчики моделей:")
        for ext in ['.glb', '.gltf', '.bam', '.egg']:
            logger.info(f"  {ext}: supported")
        return True
    except Exception as e:
        logger.error(f"Error checking glTF support: {e}")
        return False


class TruckLoadingApp(ShowBase):
    def __init__(self,
                 window_type: str = 'onscreen',
                 embed_parent_window: Optional[int] = None,
                 embed_size: Optional[Tuple[int, int]] = None,
                 enable_direct_gui: bool = True):
        self.graphics_manager = None  # Заменили lighting_manager на graphics_manager
        try:
            logger.info("Starting application...")
            if embed_parent_window is not None or window_type == 'none':
                ShowBase.__init__(self, windowType='none')
            else:
                ShowBase.__init__(self)
            logger.info("ShowBase initialized")
            self.is_embedded = embed_parent_window is not None or window_type == 'none'

            logger.info("Active language: %s; sample 'exit': %s", LANG, t(LANG, 'exit'))

            if embed_parent_window is not None:
                logger.info("Opening embedded Panda3D window...")
                self._open_embedded_window(embed_parent_window, embed_size)
            else:
                logger.info("Setting up standalone window...")
                self._setup_window_standalone()
            logger.info("Window configured")

            logger.info("Setting up scene...")
            self.setup_scene()
            logger.info("Scene configured")

            logger.info("Setting up camera...")
            self.setup_camera()
            logger.info("Camera configured")

            logger.info("Setting up graphics...")
            self.setup_graphics()
            self.graphics_manager.apply_all_settings()
            logger.info("Graphics configured")

            logger.info("Setting up truck...")
            self.setup_truck()
            logger.info("Truck configured")

            logger.info("Checking format support...")
            check_gltf_support()
            logger.info("Format support check completed")

            logger.info("Loading models...")
            self.load_models()
            logger.info("Models loaded")

            logger.info("Setting up controls...")
            self.setup_controls()
            self.current_truck_index = 0
            self.trucks = []
            self.boxes = []
            self.selected_box = None
            self.is_shift_down = False
            logger.info("Controls configured")

            logger.info("Initializing first truck...")
            self.init_first_truck()
            logger.info("First truck initialized")

            logger.info("Initialization completed")
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)

    def _setup_window_standalone(self):
        self.windowType = 'onscreen'
        props = WindowProperties()
        props.setTitle("Загрузка грузовика")
        props.setSize(1280, 800)
        self.win.requestProperties(props)
        self.setBackgroundColor(*BACKGROUND_COLOR)
        try:
            if not getattr(self, 'mouseWatcherNode', None):
                self.setupMouse(self.win)
        except Exception:
            pass

    def _open_embedded_window(self, parent_handle: int, size: Optional[Tuple[int, int]]):
        props = WindowProperties()
        props.setParentWindow(int(parent_handle))
        props.setOrigin(0, 0)
        if size:
            w, h = size
            props.setSize(int(w), int(h))
        else:
            props.setSize(1280, 800)
        logger.info(f"[Panda] openWindow in parent={parent_handle}, size={props.getXSize()}x{props.getYSize()}")
        self.win = self.openWindow(props=props)
        self.setBackgroundColor(*BACKGROUND_COLOR)
        try:
            if not getattr(self, 'mouseWatcherNode', None):
                self.setupMouse(self.win)
        except Exception:
            pass

    def resize_window(self, width: int, height: int):
        if self.win:
            props = WindowProperties()
            props.setOrigin(0, 0)
            props.setSize(int(width), int(height))
            self.win.requestProperties(props)

    def remove_material_specular(self, model):
        if not model or model.isEmpty():
            return

        from panda3d.core import Vec4

        if self.graphics_manager:
            enabled = self.graphics_manager.settings.enable_specular
            self.graphics_manager._update_model_specular(model, enabled)

    def load_models(self):
        logger.info("Starting models loading...")

        model_formats = [
            ("models/weel.obj", "models/lorry.obj"),
            ("weel.obj", "lorry.obj"),
        ]

        wheel_path = None
        lorry_path = None

        # Ищем доступные файлы моделей
        for wheel_file, lorry_file in model_formats:
            if os.path.exists(wheel_file) and os.path.exists(lorry_file):
                wheel_path = wheel_file
                lorry_path = lorry_file
                logger.info(f"Found model files: {wheel_file}, {lorry_file}")
                break

        if not wheel_path:
            logger.warning("No model files found, using placeholders")
            wheel_path = "weel.glb"
            lorry_path = "lorry.glb"

        self.wheel_model = None
        try:
            logger.info(f"Loading wheel model from {wheel_path}...")

            if wheel_path.endswith('.obj'):
                mtl_path = wheel_path.replace('.obj', '.mtl')
                if os.path.exists(mtl_path):
                    logger.info(f"Found wheel material file: {mtl_path}")
                else:
                    logger.warning(f"Wheel material file not found: {mtl_path}")

            self.wheel_model = self.loader.loadModel(wheel_path)

            if self.wheel_model and not self.wheel_model.isEmpty():
                logger.info("Wheel model loaded successfully!")
            else:
                logger.error("Wheel model is empty or invalid")
                self.wheel_model = None
        except Exception as e:
            logger.error(f"Error loading wheel model: {e}")

        if self.wheel_model and not self.wheel_model.isEmpty():
            logger.info("Configuring wheel model...")

            self.box_weel_move = self.render.attachNewNode("boxWeelMove")
            truck_long = max(1000, self.truck_width)
            weel_position = 50
            self.box_weel_move.setPos(weel_position - truck_long / 2, WHEEL_CABIN_HEIGHT, 0)

            self.wheel_model.reparentTo(self.box_weel_move)
            self.wheel_model.setScale(100, 100, 100)
            self.wheel_model.setTwoSided(True)
            self.wheel_model.setHpr(0, 90, 0)
            self.wheel_model.setPos(0, 125, 0)

            materials = self.wheel_model.findAllMaterials()
            if materials:
                logger.info(f"Wheel has {len(materials)} materials, keeping original")
            else:
                logger.warning("No materials found for wheel, creating default")
                wheel_mat = Material()
                wheel_mat.setShininess(12.8)
                wheel_mat.setSpecular((0.3, 0.3, 0.3, 1))
                wheel_mat.setDiffuse((0.2, 0.2, 0.2, 1))
                wheel_mat.setEmission((0.36, 0.36, 0.36, 1))
                self.wheel_model.setMaterial(wheel_mat, 1)
            self.remove_material_specular(self.wheel_model)
            logger.info("Wheel configured successfully")

        self.lorry_model = None
        try:
            logger.info(f"Loading cabin model from {lorry_path}...")

            if lorry_path.endswith('.obj'):
                mtl_path = lorry_path.replace('.obj', '.mtl')
                if os.path.exists(mtl_path):
                    logger.info(f"Found cabin material file: {mtl_path}")
                else:
                    logger.warning(f"Cabin material file not found: {mtl_path}")

            self.lorry_model = self.loader.loadModel(lorry_path)

            if self.lorry_model and not self.lorry_model.isEmpty():
                logger.info("Cabin model loaded successfully!")
            else:
                logger.error("Cabin model is empty or invalid")
                self.lorry_model = None
        except Exception as e:
            logger.error(f"Error loading cabin model: {e}")

        if self.lorry_model and not self.lorry_model.isEmpty():
            logger.info("Configuring cabin model...")

            self.box_lorry_move = self.render.attachNewNode("boxLorryMove")
            truck_long = max(1000, self.truck_width)
            lorry_position = -400
            self.box_lorry_move.setPos(lorry_position + truck_long / 2, WHEEL_CABIN_HEIGHT, 0)

            self.lorry_model.reparentTo(self.box_lorry_move)
            self.lorry_model.setScale(100, 100, 100)
            self.lorry_model.setTwoSided(True)
            self.lorry_model.setHpr(0, 90, 0)
            self.lorry_model.setPos(0, 125, 0)

            materials = self.lorry_model.findAllMaterials()
            if materials:
                logger.info(f"Cabin has {len(materials)} materials, keeping original")
            else:
                logger.warning("No materials found for cabin, creating default")
                cabin_mat = Material()
                cabin_mat.setShininess(12.8)
                cabin_mat.setSpecular((0.3, 0.3, 0.3, 1))
                cabin_mat.setDiffuse((0.3, 0.35, 0.4, 1))
                cabin_mat.setEmission((0.54, 0.63, 0.72, 1))
                self.lorry_model.setMaterial(cabin_mat, 1)
            self.remove_material_specular(self.lorry_model)
            logger.info("Cabin configured successfully")

        logger.info("Models loading completed")

        if self.graphics_manager:
            logger.info("Applying saved graphics settings to loaded models...")
            self.graphics_manager.apply_all_settings()

    def setup_scene(self):
        self.render.setAntialias(AntialiasAttrib.MMultisample)
        self.setBackgroundColor(*BACKGROUND_COLOR)
        self.disableMouse()

    def setup_camera(self):
        self.camLens.setFov(45.8)
        self.arc = ArcCamera(self)
        self.taskMgr.add(self.arc.tick, "camera_update")

    def setup_graphics(self):  # Заменили setup_lighting на setup_graphics
        self.graphics_manager = GraphicsManager(self)
        self.graphics_manager.setup_lighting()

    def setup_truck(self):
        self.scene = TruckScene(self)
        self.scene.build()
        self.truck_width = self.scene.truck_width
        self.truck_height = self.scene.truck_height
        self.truck_depth = self.scene.truck_depth

    def set_tent_alpha(self, alpha: float):
        self.scene.set_tent_alpha(alpha)

    def switch_truck(self, t_w: int, t_h: int, t_d: int):
        self.truck_width = t_w
        self.truck_height = t_h
        self.truck_depth = t_d
        self.scene.resize(t_w, t_h, t_d)

        truck_long = max(1000, t_w)
        weel_position = 50
        lorry_position = -400

        if hasattr(self, 'box_weel_move'):
            self.box_weel_move.setPos(weel_position - truck_long / 2, WHEEL_CABIN_HEIGHT, 0)
        if hasattr(self, 'box_lorry_move'):
            self.box_lorry_move.setPos(lorry_position + truck_long / 2, WHEEL_CABIN_HEIGHT, 0)

        # Preserve tent open/close state across size changes
        if hasattr(self.scene, 'tent_closed'):
            self.scene.set_tent_closed(self.scene.tent_closed)

    def set_background_color(self, r: float, g: float, b: float):
        """Установить цвет фона"""
        if self.graphics_manager:
            self.graphics_manager.set_background_color(r, g, b)

    def set_specular_enabled(self, enabled: bool):
        """Включить/выключить блики"""
        if self.graphics_manager:
            self.graphics_manager.set_specular_enabled(enabled)

    def set_truck_color(self, r: float, g: float, b: float):
        """Установить цвет тягача"""
        if self.graphics_manager:
            self.graphics_manager.set_truck_color(r, g, b)

    def set_lighting_intensity(self, main_intensity: float, fill_intensity: float):
        if self.graphics_manager:
            self.graphics_manager.set_light_intensity(main_intensity, fill_intensity)

    def set_lighting_mode(self, mode: str):
        if self.graphics_manager:
            self.graphics_manager.set_lighting_mode(mode)
    def setup_controls(self):
        print("Setting up controls...")

        self.accept("mouse1", self.arc.on_right_down)
        self.accept("mouse1-up", self.arc.on_right_up)
        self.accept("mouse3", self.arc.on_left_down)
        self.accept("mouse3-up", self.arc.on_left_up)
        self.accept("wheel_up", self.arc.on_wheel_in)
        self.accept("wheel_down", self.arc.on_wheel_out)
        self.accept("shift", self.shift_down)
        self.accept("shift-up", self.shift_up)

        print("Controls setup complete")

    def shift_down(self):
        """Нажатие Shift"""
        self.is_shift_down = True

    def shift_up(self):
        """Отпускание Shift"""
        self.is_shift_down = False

    def init_first_truck(self):
        """Инициализация первого грузовика"""
        first_truck = {
            'width': self.truck_width,
            'height': self.truck_height,
            'depth': self.truck_depth
        }
        self.trucks.append(first_truck)
