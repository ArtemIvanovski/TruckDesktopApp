#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import math
import os
import sys
import traceback

from direct.gui.DirectGui import *
from direct.gui import DirectGuiGlobals as DGG
from panda3d.core import Filename
from panda3d.core import (
    WindowProperties,
    AntialiasAttrib,
    DirectionalLight,
    AmbientLight,
    TransparencyAttrib,
    Vec3,
    GeomVertexData, GeomVertexFormat, Geom, GeomVertexWriter, GeomLines, GeomNode,
    CardMaker,
    TextNode,
)
from direct.showbase.ShowBase import ShowBase
from typing import Optional, Tuple
from camera import ArcCamera
from truck import TruckScene
from config import BACKGROUND_COLOR, FLOOR_HEIGHT, LIGHTING_MODE, LANG
from i18n import t


# Настройка логирования в самом начале
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
        try:
            logger.info("Starting application...")
            # If embedding into Qt, we must avoid creating the default window
            if embed_parent_window is not None or window_type == 'none':
                ShowBase.__init__(self, windowType='none')
            else:
                ShowBase.__init__(self)
            logger.info("ShowBase initialized")
            self.is_embedded = embed_parent_window is not None or window_type == 'none'

            logger.info("Active language: %s; sample 'exit': %s", LANG, t(LANG, 'exit'))
            # Window setup: standalone vs embedded
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

            logger.info("Setting up lighting...")
            self.setup_lighting()
            logger.info("Lighting configured")

            logger.info("Setting up truck...")
            self.setup_truck()
            logger.info("Truck configured")

            logger.info("Checking format support...")
            check_gltf_support()
            logger.info("Format support check completed")

            logger.info("Loading models...")
            self.load_models()
            logger.info("Models loaded")

            # Optional Panda3D DirectGUI (disabled when using Qt)
            self.enable_direct_gui = enable_direct_gui
            if self.enable_direct_gui:
                logger.info("Setting up DirectGUI...")
                self.setup_gui()
                logger.info("DirectGUI configured")

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
            # Ensure mouse watcher exists
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
            # Ensure mouse watcher exists for embedded window
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

    def create_placeholder_wheel(self):
        """Создание простого колеса-заглушки"""
        logger.info("Creating placeholder wheel...")
        
        # Создаем простое колесо из круга
        from panda3d.core import CardMaker
        wheel_geom = CardMaker("wheel_placeholder")
        wheel_geom.setFrame(-1, 1, -1, 1)
        
        wheel = self.render.attachNewNode(wheel_geom.generate())
        wheel.setScale(100, 100, 100)
        wheel.setHpr(0, 0, 180)
        wheel.setPos(50 - self.truck_width / 2, -125, 0)
        wheel.setColor(0.8, 0.8, 0.8, 1)  # Светло-серый
        
        logger.info("Placeholder wheel created successfully")
        return wheel

    def create_placeholder_cabin(self):
        """Создание простой кабины-заглушки"""
        logger.info("Creating placeholder cabin...")
        
        # Создаем простую кабину из куба
        from panda3d.core import CardMaker
        cabin_geom = CardMaker("cabin_placeholder")
        cabin_geom.setFrame(-1, 1, -1, 1)
        
        cabin = self.render.attachNewNode(cabin_geom.generate())
        cabin.setScale(100, 100, 100)
        cabin.setHpr(0, 0, 180)
        cabin.setPos(-400 + self.truck_width / 2, -125, 0)
        cabin.setColor(0.6, 0.6, 0.8, 1)  # Сине-серый
        
        logger.info("Placeholder cabin created successfully")
        return cabin

    def load_models(self):
        """Loading .glb models"""
        logger.info("Starting .glb models loading...")

        # Check different model formats (prioritized like web version)
        model_formats = [
            ("models/weel.obj", "models/lorry.obj"),    # OBJ from models folder (primary)
            ("models/weel.egg", "models/lorry.egg"),    # Panda3D native format
            ("models/weel.bam", "models/lorry.bam"),    # Panda3D binary format
            ("weel.obj", "lorry.obj"),                  # OBJ in current folder (fallback)
            ("models/weel.glb", "models/lorry.glb")     # glTF format (backup)
        ]
        
        wheel_path = None
        lorry_path = None
        
        # Find available model files
        for wheel_file, lorry_file in model_formats:
            if os.path.exists(wheel_file) and os.path.exists(lorry_file):
                wheel_path = wheel_file
                lorry_path = lorry_file
                logger.info(f"Found model files: {wheel_file}, {lorry_file}")
                break
        
        if not wheel_path:
            logger.warning("No model files found, using placeholders")
            wheel_path = "weel.glb"  # fallback
            lorry_path = "lorry.glb"  # fallback

        # Try to load wheel model
        self.wheel_model = None
        try:
            if wheel_path.endswith('.egg') or wheel_path.endswith('.bam') or wheel_path.endswith('.obj'):
                logger.info(f"Loading wheel model from {wheel_path}...")
                
                # For OBJ files, check if MTL file exists
                if wheel_path.endswith('.obj'):
                    mtl_path = wheel_path.replace('.obj', '.mtl')
                    if os.path.exists(mtl_path):
                        logger.info(f"Found material file: {mtl_path}")
                
                self.wheel_model = self.loader.loadModel(wheel_path)
                if self.wheel_model and not self.wheel_model.isEmpty():
                    logger.info("Wheel model loaded successfully!")
                else:
                    logger.error("Wheel model is empty or invalid")
                    self.wheel_model = None
            else:
                logger.info("No supported wheel model found, creating placeholder...")
                self.wheel_model = self.create_placeholder_wheel()
        except Exception as e:
            logger.error(f"Error loading wheel model: {e}")
            logger.info("Creating placeholder wheel...")
            self.wheel_model = self.create_placeholder_wheel()

        # Configure wheel if loaded - match web version positioning exactly
        if self.wheel_model and not self.wheel_model.isEmpty():
            logger.info("Configuring wheel model...")
            
            # Create box parent for wheel movement (like boxWeelMove in web)
            self.box_weel_move = self.render.attachNewNode("boxWeelMove")
            
            # Position parent box exactly as in web version
            lorry_weel_x = self.truck_width / 2  # truck.getBoundingInfo().boundingBox.maximum.x
            weel_position = 50
            self.box_weel_move.setPos(weel_position - lorry_weel_x, 0, 0)
            
            # Attach wheel to parent and configure
            self.wheel_model.reparentTo(self.box_weel_move)
            # Avoid negative scale to prevent flipped normals/black look
            self.wheel_model.setScale(100, 100, 100)
            self.wheel_model.setTwoSided(True)
            # Rotation: preserved per user's requirement
            self.wheel_model.setHpr(0, 90, 0)
            # Local position relative to parent
            self.wheel_model.setPos(0, 0, 0)
            logger.info("Wheel configured successfully")

        # Try to load cabin model
        self.lorry_model = None
        try:
            if lorry_path.endswith('.egg') or lorry_path.endswith('.bam') or lorry_path.endswith('.obj'):
                logger.info(f"Loading cabin model from {lorry_path}...")
                
                # For OBJ files, check if MTL file exists
                if lorry_path.endswith('.obj'):
                    mtl_path = lorry_path.replace('.obj', '.mtl')
                    if os.path.exists(mtl_path):
                        logger.info(f"Found material file: {mtl_path}")
                
                self.lorry_model = self.loader.loadModel(lorry_path)
                if self.lorry_model and not self.lorry_model.isEmpty():
                    logger.info("Cabin model loaded successfully!")
                else:
                    logger.error("Cabin model is empty or invalid")
                    self.lorry_model = None
            else:
                logger.info("No supported cabin model found, creating placeholder...")
                self.lorry_model = self.create_placeholder_cabin()
        except Exception as e:
            logger.error(f"Error loading cabin model: {e}")
            logger.info("Creating placeholder cabin...")
            self.lorry_model = self.create_placeholder_cabin()

        if self.lorry_model and not self.lorry_model.isEmpty():
            logger.info("Configuring cabin model...")
            
            self.box_lorry_move = self.render.attachNewNode("boxLorryMove")
            
            lorry_weel_x = self.truck_width / 2  # truck.getBoundingInfo().boundingBox.maximum.x
            lorry_position = -400
            self.box_lorry_move.setPos(lorry_position + lorry_weel_x, 0, 0)
            
            self.lorry_model.reparentTo(self.box_lorry_move)
            # Avoid negative scale to prevent flipped normals/black look
            self.lorry_model.setScale(100, 100, 100)
            self.lorry_model.setTwoSided(True)
            self.lorry_model.setHpr(0, 90, 0)
            self.lorry_model.setPos(0, 0, 0)
            logger.info("Cabin configured successfully")

        logger.info("Models loading completed")

    def setup_scene(self):
        self.disableMouse()
        self.render.setAntialias(AntialiasAttrib.MMultisample)
        self.render.setShaderAuto()
        self.render.setTwoSided(True)
        self.setBackgroundColor(0.35, 0.35, 0.35, 1)
        self.win.setClearColorActive(True)
        self.render.setAntialias(AntialiasAttrib.MAuto)

    def setup_camera(self):
        self.camLens.setFov(45.8)
        self.arc = ArcCamera(self)
        self.taskMgr.add(self.arc.tick, "camera_update")

    def update_camera_position(self):
        pass

    def setup_lighting(self):
        self.render.setShaderAuto()  # Всегда включать шейдеры
    
        # Основной источник света (как в Babylon.js)
        dlight = DirectionalLight('main_light')
        dlight.setColor((1.5, 1.5, 1.5, 1))
        dlight.setDirection(Vec3(-1, 1, -1))
        dlnp = self.render.attachNewNode(dlight)
        self.render.setLight(dlnp)
    
        # Добавить окружающее освещение
        alight = AmbientLight('ambient')
        alight.setColor((0.3, 0.3, 0.3, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        for np in self.render.find_all_matches('**/+LightLensNode'):
            np.removeNode()

    def setup_truck(self):
        self.scene = TruckScene(self)
        self.scene.build()
        self.truck_width = self.scene.truck_width
        self.truck_height = self.scene.truck_height
        self.truck_depth = self.scene.truck_depth
        # DirectGUI panels are not used when Qt hosts the UI

    def create_truck_box(self):
        """Создание полупрозрачного куба грузовика"""
        vertex_data = GeomVertexData('truck', GeomVertexFormat.get_v3(), Geom.UHStatic)
        geom = Geom(vertex_data)
        vertex_data.setNumRows(8)
        vertex_writer = GeomVertexWriter(vertex_data, 'vertex')

        # 8 вершин куба
        vertices = [
            (-self.truck_width / 2, -self.truck_depth / 2, 0),
            (self.truck_width / 2, -self.truck_depth / 2, 0),
            (self.truck_width / 2, self.truck_depth / 2, 0),
            (-self.truck_width / 2, self.truck_depth / 2, 0),
            (-self.truck_width / 2, -self.truck_depth / 2, self.truck_height),
            (self.truck_width / 2, -self.truck_depth / 2, self.truck_height),
            (self.truck_width / 2, self.truck_depth / 2, self.truck_height),
            (-self.truck_width / 2, self.truck_depth / 2, self.truck_height)
        ]

        for vertex in vertices:
            vertex_writer.addData3f(*vertex)

        # Создаем грани куба (wireframe)
        geom_lines = GeomLines(Geom.UHStatic)

        # 12 ребер куба
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # нижнее основание
            (4, 5), (5, 6), (6, 7), (7, 4),  # верхнее основание
            (0, 4), (1, 5), (2, 6), (3, 7)  # вертикальные ребра
        ]

        for edge in edges:
            geom_lines.addVertex(edge[0])
            geom_lines.addVertex(edge[1])
            geom_lines.closePrimitive()

        geom.addPrimitive(geom_lines)

        truck_geom_node = GeomNode('truck_geom')
        truck_geom_node.addGeom(geom)

        self.truck = self.render.attachNewNode(truck_geom_node)
        self.truck.setPos(0, 0, self.truck_height / 2)

        self.truck.setColor(0.4, 0.4, 0.4, 0.3)  # Как в веб-версии
        
        # self.truck.setTransparency(TransparencyAttrib.MAlpha)
        # Включаем wireframe для имитации enableEdgesRendering() 
        self.truck.setRenderModeWireframe()
        self.truck.setTwoSided(True)

    def create_floor(self):
        # Непосредственно пол как в web: сплошная заливка #c3c3c3
        from config import FLOOR_COLOR, FLOOR_THICKNESS
        floor_geom = CardMaker("floor")
        floor_geom.setFrame(-self.truck_width / 2, self.truck_width / 2,
                            -FLOOR_THICKNESS / 2, FLOOR_THICKNESS / 2)

        self.floor = self.render.attachNewNode(floor_geom.generate())
        self.floor.setPos(0, 0, FLOOR_HEIGHT + FLOOR_THICKNESS/2)
        self.floor.setP(-90)
        self.floor.setColor(*FLOOR_COLOR)
        self.floor.clearRenderMode()
        self.floor.setTwoSided(True)

    def create_ground(self):
        """Создание земли с сеткой точно как в веб-версии"""
        # Ground как в веб-версии: размер 4800x4800
        ground_geom = CardMaker("ground")
        ground_geom.setFrame(-2400, 2400, -2400, 2400)  # 4800x4800

        self.ground = self.render.attachNewNode(ground_geom.generate())
        self.ground.setPos(0, 0, 0)
        self.ground.setP(-90)  # Поворачиваем чтобы лежала горизонтально
    
        self.ground.setTransparency(TransparencyAttrib.MAlpha)
        self.ground.setColor(0.2, 0.2, 0.2, 0.0)  # Полностью прозрачная как в веб-версии

    def set_tent_alpha(self, alpha: float):
        self.scene.set_tent_alpha(alpha)

    def switch_truck(self, t_w: int, t_h: int, t_d: int):
        self.truck_width = t_w
        self.truck_height = t_h
        self.truck_depth = t_d
        self.scene.resize(t_w, t_h, t_d)

        lorry_weel_x = self.truck_width / 2
        weel_position = 50
        if hasattr(self, 'box_weel_move'):
            self.box_weel_move.setPos(weel_position - lorry_weel_x, 0, 0)
        if hasattr(self, 'box_lorry_move'):
            lorry_position = -400
            self.box_lorry_move.setPos(lorry_position + lorry_weel_x, 0, 0)

        # Preserve tent open/close state across size changes
        if hasattr(self.scene, 'tent_closed'):
            self.scene.set_tent_closed(self.scene.tent_closed)

    def setup_gui(self):
        # Try to load a font with Cyrillic support, with extra logging and fallbacks
        try:
            fonts_dir = os.path.join(os.path.dirname(__file__), 'fonts')
            candidates = [
                os.path.join(fonts_dir, 'arial.ttf'),
                os.path.join(fonts_dir, 'NotoSans-Regular.ttf'),
                os.path.join(fonts_dir, 'NotoSans_Condensed-Regular.ttf'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arial.ttf'),
            ]
            self.ui_font = None
            for path in candidates:
                try:
                    # Normalize to Panda Filename (handles Windows paths)
                    panda_fn = Filename.fromOsSpecific(path)
                    panda_fn.makeTrueCase()
                    exists = panda_fn.exists() or os.path.exists(path)
                    if exists:
                        logger.info(f"Trying UI font: {path}")
                        font = self.loader.loadFont(panda_fn)
                        if font:
                            self.ui_font = font
                            logger.info(f"Using UI font: {path}")
                            break
                        else:
                            logger.warning(f"loadFont returned None for {path}")
                except Exception as e:
                    logger.error(f"Error loading font {path}: {e}")
            if not self.ui_font:
                logger.warning("No valid UI font found; Cyrillic may not render")
            else:
                try:
                    DGG.setDefaultFont(self.ui_font)
                    logger.info("Default GUI font set globally")
                except Exception as e:
                    logger.error(f"Failed to set default GUI font: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in setup_gui font selection: {e}")
            self.ui_font = None
        logger.debug(f"Creating Exit button with font: {self.ui_font}")
        self.exit_button = DirectButton(
            text=t(LANG, 'exit'),
            scale=0.05,
            pos=(1.7, 0, -0.9),
            command=self.exit_app,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.47, 0.59, 0.71, 1),  # #7796b4
            relief=DGG.RAISED,
            text_font=self.ui_font if self.ui_font else None
        )

        # Information text (updated to match web controls, сдвинут вниз под табы)
        logger.debug("Creating info_text. Using Cyrillic string? %s", t(LANG, 'controls_hint'))
        self.info_text = OnscreenText(
            text=t(LANG, 'controls_hint'),
            pos=(-1.7, 0.35),  # Сдвинут вниз под табы
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            font=self.ui_font if self.ui_font else None
        )

        # Zone load indicators (like in web version, сдвинуты вниз под табы)
        self.zone_indicators = []
        for i in range(4):
            zone_text = OnscreenText(
                text=t(LANG, 'zone', i=i + 1, w=0),
                pos=(0.0 + i * 0.4 - 0.6, 0.35),  # Сдвинуты вниз под табы
                scale=0.05,
                fg=(1, 1, 1, 1),
                align=TextNode.ACenter,
                font=self.ui_font if self.ui_font else None
            )
            self.zone_indicators.append(zone_text)

    def setup_controls(self):
        """Setup controls exactly like Babylon.js ArcRotateCamera"""
        # Mouse handlers for camera rotation and panning (like Babylon.js attachControl)
        self.accept("mouse1", self.arc.on_left_down)
        self.accept("mouse1-up", self.arc.on_left_up)
        self.accept("mouse2", self.arc.on_right_down)
        self.accept("mouse2-up", self.arc.on_right_up)
        self.accept("mouse3", self.arc.on_left_down)
        self.accept("mouse3-up", self.arc.on_left_up)
        
        # Wheel zoom with wheelDeltaPercentage = 0.02 like web
        self.accept("wheel_up", self.arc.on_wheel_in)
        self.accept("wheel_down", self.arc.on_wheel_out)

        # Keyboard
        self.accept("shift", self.shift_down)
        self.accept("shift-up", self.shift_up)
        if not getattr(self, 'is_embedded', False):
            self.accept("escape", self.exit_app)

        # tick already added in setup_camera

    def start_camera_rotate(self):
        pass
    def stop_camera_rotate(self):
        pass
    def start_camera_pan(self):
        pass
    def stop_camera_pan(self):
        pass
    def update_camera_task(self, task):
        return task.cont
    def zoom_in(self):
        self.arc.on_wheel_in()
    def zoom_out(self):
        self.arc.on_wheel_out()

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

    def exit_app(self):
        """Выход из приложения"""
        sys.exit()


# Qt5 launcher embedded here for single-entry design
if __name__ == "__main__":
    from PyQt5 import QtWidgets, QtCore, QtGui
    from hotkeys import HotkeyController

    class PandaWidget(QtWidgets.QWidget):
        ready = QtCore.pyqtSignal()
        def __init__(self, parent=None):
            super().__init__(parent)
            # Эксклюзивный нативный виджет без заливки фоном Qt
            self.setAttribute(QtCore.Qt.WA_NativeWindow)
            self.setAttribute(QtCore.Qt.WA_NoSystemBackground)
            self.setAutoFillBackground(False)
            self.setMinimumSize(800, 500)
            self.app3d = None
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self._step)
            self.timer.start(16)
            QtCore.QTimer.singleShot(0, self._init_panda)

        def _init_panda(self):
            try:
                handle = int(self.winId())
                dpr = 1.0
                wh = self.window().windowHandle()
                if wh:
                    dpr = float(wh.devicePixelRatio())
                w = int(max(1, round(self.width() * dpr)))
                h = int(max(1, round(self.height() * dpr)))
                logging.info(f"[Qt] Creating Panda3D with parent HWND={handle}, size=({w}x{h}), dpr={dpr}")
                self.app3d = TruckLoadingApp(
                    window_type='none',
                    embed_parent_window=handle,
                    embed_size=(w, h),
                    enable_direct_gui=False,
                )
                self.ready.emit()
            except Exception as e:
                logging.error(f"[Qt] Failed to init Panda3D: {e}")

        def _step(self):
            try:
                if self.app3d:
                    self.app3d.taskMgr.step()
            except Exception as e:
                logging.error(f"[Qt] taskMgr.step error: {e}")

        def resizeEvent(self, event):
            if self.app3d and hasattr(self.app3d, 'resize_window'):
                dpr = 1.0
                wh = self.window().windowHandle()
                if wh:
                    dpr = float(wh.devicePixelRatio())
                w = int(max(1, round(self.width() * dpr)))
                h = int(max(1, round(self.height() * dpr)))
                logging.info(f"[Qt] resizeEvent -> logical={self.width()}x{self.height()} physical={w}x{h} dpr={dpr}")
                self.app3d.resize_window(w, h)
            super().resizeEvent(event)

    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Загрузка грузовика — Qt UI + Panda3D 3D")
            self.viewer = PandaWidget(self)
            self.setCentralWidget(self.viewer)
            self.viewer.ready.connect(self._on_viewer_ready)
            self.hotkeys = HotkeyController(self)

            toolbar = self.addToolBar("Main")
            act_tent_open = toolbar.addAction("Открыть тент")
            act_tent_close = toolbar.addAction("Закрыть тент")
            toolbar.addSeparator()
            act_view_reset = toolbar.addAction("Сброс вида")
            act_fullscreen = toolbar.addAction("Полный экран")

            act_tent_open.triggered.connect(lambda: self.viewer.app3d.set_tent_alpha(0.0))
            act_tent_close.triggered.connect(lambda: self.viewer.app3d.set_tent_alpha(0.3))
            act_view_reset.triggered.connect(self._view_reset)
            act_fullscreen.triggered.connect(self._toggle_fullscreen)
            self.dock_r = None

            self.setStatusBar(None)

        def _apply_dims(self):
            try:
                w = int(float(self.ed_w.text()))
                h = int(float(self.ed_h.text()))
                d = int(float(self.ed_d.text()))
                self.viewer.app3d.switch_truck(w, h, d)
            except Exception:
                pass

        def _on_viewer_ready(self):
            logging.info("[Qt] Panda3D ready")

        def _view_top(self):
            cam = self.viewer.app3d.arc
            cam.radius = 1400
            cam.alpha = 3.14159265 / 2
            cam.beta = 0.00001
            cam.update()

        def _view_left(self):
            cam = self.viewer.app3d.arc
            cam.radius = 1400
            cam.alpha = 3.14159265 / 2
            cam.beta = 3.14159265 / 2
            cam.update()

        def _view_right(self):
            cam = self.viewer.app3d.arc
            cam.radius = 1400
            cam.alpha = -3.14159265 / 2
            cam.beta = 3.14159265 / 2
            cam.update()

        def _view_reset(self):
            cam = self.viewer.app3d.arc
            cam.radius = 2000
            cam.alpha = 3.14159265 / 2
            cam.beta = 3.14159265 / 3
            cam.target.set(0, 300, 0)
            cam.update()

        def _toggle_fullscreen(self):
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

    def _load_qt_fonts():
        try:
            base_dir = os.path.dirname(__file__)
            font_candidates = [
                os.path.join(base_dir, 'fonts', 'NotoSans_Condensed-Regular.ttf'),
                os.path.join(base_dir, 'fonts', 'NotoSans-Regular.ttf'),
                os.path.join(base_dir, 'fonts', 'arial.ttf'),
            ]
            for path in font_candidates:
                if os.path.exists(path):
                    QtGui.QFontDatabase.addApplicationFont(path)
        except Exception:
            pass

    qt_app = QtWidgets.QApplication(sys.argv)
    _load_qt_fonts()
    win = MainWindow()
    win.showMaximized()
    sys.exit(qt_app.exec_())
