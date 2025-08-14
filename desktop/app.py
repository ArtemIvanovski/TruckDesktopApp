#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import sys
import traceback
from typing import Optional, Tuple

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectGui import *
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Filename, Material, TransparencyAttrib
from panda3d.core import (
    WindowProperties,
    AntialiasAttrib,
    DirectionalLight,
    AmbientLight,
    TextNode,
)

from camera import ArcCamera
from config import BACKGROUND_COLOR, LANG, WHEEL_CABIN_HEIGHT
from i18n import t
from truck import TruckScene

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

    def load_models(self):
        """Loading .obj models with materials from .mtl"""
        logger.info("Starting models loading...")

        model_formats = [
            ("models/weel.obj", "models/lorry.obj"),
            ("models/weel.egg", "models/lorry.egg"),
            ("models/weel.bam", "models/lorry.bam"),
            ("weel.obj", "lorry.obj"),
            ("models/weel.glb", "models/lorry.glb")
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

        # Пробуем загрузить модель колеса
        self.wheel_model = None
        try:
            logger.info(f"Loading wheel model from {wheel_path}...")

            # Для OBJ проверяем наличие MTL
            if wheel_path.endswith('.obj'):
                mtl_path = wheel_path.replace('.obj', '.mtl')
                if os.path.exists(mtl_path):
                    logger.info(f"Found wheel material file: {mtl_path}")
                else:
                    logger.warning(f"Wheel material file not found: {mtl_path}")

            # Загружаем модель (Panda3D автоматически загрузит материалы)
            self.wheel_model = self.loader.loadModel(wheel_path)

            if self.wheel_model and not self.wheel_model.isEmpty():
                logger.info("Wheel model loaded successfully!")
            else:
                logger.error("Wheel model is empty or invalid")
                self.wheel_model = None
        except Exception as e:
            logger.error(f"Error loading wheel model: {e}")

        # Настраиваем колесо
        if self.wheel_model and not self.wheel_model.isEmpty():
            logger.info("Configuring wheel model...")

            # Создаем родительский узел для перемещения
            self.box_weel_move = self.render.attachNewNode("boxWeelMove")
            truck_long = max(1000, self.truck_width)
            weel_position = 50
            self.box_weel_move.setPos(weel_position - truck_long / 2, WHEEL_CABIN_HEIGHT, 0)

            # Прикрепляем колесо и настраиваем трансформации
            self.wheel_model.reparentTo(self.box_weel_move)
            self.wheel_model.setScale(100, 100, 100)
            self.wheel_model.setTwoSided(True)
            self.wheel_model.setHpr(0, 90, 0)
            self.wheel_model.setPos(0, 125, 0)

            # Отключаем освещение для колеса
            self.wheel_model.setLightOff(1)

            # Сохраняем оригинальные материалы (не перезаписываем!)
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

            # Создаем родительский узел для перемещения
            self.box_lorry_move = self.render.attachNewNode("boxLorryMove")
            truck_long = max(1000, self.truck_width)
            lorry_position = -400
            self.box_lorry_move.setPos(lorry_position + truck_long / 2, WHEEL_CABIN_HEIGHT, 0)

            # Прикрепляем кабину и настраиваем трансформации
            self.lorry_model.reparentTo(self.box_lorry_move)
            self.lorry_model.setScale(100, 100, 100)
            self.lorry_model.setTwoSided(True)
            self.lorry_model.setHpr(0, 90, 0)
            self.lorry_model.setPos(0, 125, 0)

            # Отключаем освещение для кабины
            self.lorry_model.setLightOff(1)

            # Сохраняем оригинальные материалы (не перезаписываем!)
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

            logger.info("Cabin configured successfully")

        logger.info("Models loading completed")

    def setup_scene(self):
        # Отключаем все эффекты, которые могут создавать "туман"
        # self.render.setShaderAuto()
        self.render.setAntialias(AntialiasAttrib.MMultisample)
        self.render.setTwoSided(True)
        self.setBackgroundColor(0.35, 0.35, 0.35, 1)

        # Отключаем автоматическое управление камерой
        self.disableMouse()

        # Настройки отображения - отключаем освещение для устранения теней
        self.render.setAttrib(TransparencyAttrib.make(TransparencyAttrib.M_none))
        self.render.setDepthOffset(0)
        # Отключаем освещение для всей сцены
        self.render.setLightOff(1)
        
        # Дополнительные настройки для отключения теней
        from panda3d.core import ShaderAttrib
        self.render.setShaderAuto(False)  # Отключаем автоматические шейдеры
        self.render.setLightOff(1)  # Отключаем все источники света
        
        # Отключаем автоматическое освещение
        self.render.setLightOff(1)
        self.render.clearLight()

        # Оптимизация рендеринга
        self.setFrameRateMeter(True)
        self.setBackgroundColor(*BACKGROUND_COLOR)

    def setup_camera(self):
        self.camLens.setFov(45.8)
        self.arc = ArcCamera(self)
        self.taskMgr.add(self.arc.tick, "camera_update")

    def update_camera_position(self):
        pass

    def setup_lighting(self):
        # Полностью отключаем все источники света для устранения теней
        dlight = DirectionalLight('hemispheric')
        dlight.setColor((1.5, 1.5, 1.5, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, 0)  # Соответствует вектору (-1, 1, -1)

        # Отключаем ambient свет тоже
        alight = AmbientLight('ambient')
        alight.setColor((1.0, 1.0, 1.0, 1))  # Увеличиваем интенсивность для компенсации
        alnp = self.render.attachNewNode(alight)

        # Не устанавливаем никаких источников света
        self.render.setLight(dlnp)  # Отключаем направленный свет
        self.render.setLight(alnp)  # Отключаем ambient свет

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
        # Левая кнопка мыши - вращение
        self.accept("mouse1", self.arc.on_left_down)
        self.accept("mouse1-up", self.arc.on_left_up)

        # Правая кнопка мыши - панорамирование
        self.accept("mouse2", self.arc.on_right_down)
        self.accept("mouse2-up", self.arc.on_right_up)

        # Колесо мыши - масштабирование
        self.accept("wheel_up", self.arc.on_wheel_in)
        self.accept("wheel_down", self.arc.on_wheel_out)

        # SHIFT для привязки объектов
        self.accept("shift", self.shift_down)
        self.accept("shift-up", self.shift_up)

    def start_camera_rotate(self):
        self.arc.start_rotate()

    def stop_camera_rotate(self):
        self.arc.stop_rotate()

    def start_camera_pan(self):
        self.arc.start_pan()

    def stop_camera_pan(self):
        self.arc.stop_pan()

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


if __name__ == "__main__":
    from PyQt5 import QtWidgets, QtCore, QtGui
    from qt_panels import LeftSidebar
    from hotkeys import HotkeyController


    class PandaWidget(QtWidgets.QWidget):
        ready = QtCore.pyqtSignal()

        def __init__(self, parent=None):
            super().__init__(parent)
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
            self.setWindowTitle("GTSTREAM")
            self.viewer = PandaWidget(self)
            # Central splitter: left sidebar + 3D viewer
            splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
            # Left-side sidebar: thin vertical bar | panel container | 3D viewer
            sidebar = LeftSidebar(lambda: self.viewer.app3d, self)
            splitter.addWidget(sidebar)
            splitter.addWidget(sidebar.panel_container)
            splitter.addWidget(self.viewer)
            splitter.setStretchFactor(0, 0)
            splitter.setStretchFactor(1, 0)
            splitter.setStretchFactor(2, 1)
            self.setCentralWidget(splitter)
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

            # Размеры бокса (веб-предустановки + свой размер)
            # Устарело: теперь используется левый сайдбар
            # self._init_size_tab()

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

        def _init_size_tab(self):
            dock = QtWidgets.QDockWidget("Параметры", self)
            dock.setObjectName("dock_sizes")
            dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
            tabs = QtWidgets.QTabWidget(dock)
            dock.setWidget(tabs)

            tab_sizes = QtWidgets.QWidget()
            tabs.addTab(tab_sizes, "Размеры бокса")
            layout = QtWidgets.QVBoxLayout(tab_sizes)

            group = QtWidgets.QButtonGroup(tab_sizes)
            group.setExclusive(True)
            presets = [
                ("Тент 13.6", 1360, 260, 245),
                ("Мега", 1360, 300, 245),
                ("Конт 40ф", 1203, 239, 235),
                ("Конт 20ф", 590, 239, 235),
                ("Рефр", 1340, 239, 235),
                ("Тент 16.5", 1650, 260, 245),
            ]
            self._size_radio_to_dims = {}
            for title, w, h, d in presets:
                rb = QtWidgets.QRadioButton(title)
                layout.addWidget(rb)
                rb.toggled.connect(lambda checked, W=w, H=h, D=d, BTN=rb: checked and self._apply_preset(W, H, D, BTN))
                self._size_radio_to_dims[rb] = (w, h, d)

            btn_custom = QtWidgets.QPushButton("Свой размер…")
            btn_custom.clicked.connect(self._open_custom_dialog)
            layout.addWidget(btn_custom)
            layout.addStretch(1)

            self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
            self.dock_r = dock

        def _apply_preset(self, w: int, h: int, d: int, button: QtWidgets.QAbstractButton):
            # Подсветка выбранного пресета обеспечивает RadioButton
            try:
                self.viewer.app3d.switch_truck(int(w), int(h), int(d))
            except Exception:
                pass

        def _open_custom_dialog(self):
            dlg = QtWidgets.QDialog(self)
            dlg.setWindowTitle("Свой размер")
            form = QtWidgets.QFormLayout(dlg)
            ed_w = QtWidgets.QLineEdit(dlg)
            ed_h = QtWidgets.QLineEdit(dlg)
            ed_d = QtWidgets.QLineEdit(dlg)
            for ed in (ed_w, ed_h, ed_d):
                ed.setMaxLength(4)
                ed.setValidator(QtGui.QIntValidator(1, 9999, dlg))
            form.addRow("Длина (см)", ed_w)
            form.addRow("Высота (см)", ed_h)
            form.addRow("Ширина (см)", ed_d)
            btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
                                              parent=dlg)
            form.addRow(btns)

            def on_accept():
                try:
                    w = int(ed_w.text())
                    h = int(ed_h.text())
                    d = int(ed_d.text())
                except Exception:
                    return
                self.viewer.app3d.switch_truck(w, h, d)
                dlg.accept()

            btns.accepted.connect(on_accept)
            btns.rejected.connect(dlg.reject)
            dlg.exec_()


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
