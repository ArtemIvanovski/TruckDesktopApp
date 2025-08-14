#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

from PyQt5 import QtWidgets, QtCore, QtGui

from windows.settings_window import SettingsWindow
from hotkeys import HotkeyController
from qt_panels import LeftSidebar
import sys
import os

print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
print(f"Files in current dir: {os.listdir('.')}")

try:
    from app3d import TruckLoadingApp

    print("TruckLoadingApp imported successfully")
except ImportError as e:
    print(f"Import error: {e}")
# Настройка логирования в самом начале
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
        self.setup_menu_bar()
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

    def setup_menu_bar(self):
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        file_menu = menubar.addMenu('Файл')
        file_menu.addAction('Новый', self.new_file)
        file_menu.addAction('Открыть...', self.open_file)
        file_menu.addAction('Сохранить', self.save_file)
        file_menu.addAction('Сохранить как...', self.save_file_as)
        file_menu.addSeparator()
        file_menu.addAction('Выход', self.close)

        settings_menu = menubar.addMenu('Настройки')
        settings_menu.addAction('Настройки...', self.open_settings)

        help_menu = menubar.addMenu('Помощь')
        help_menu.addAction('Справка', self.show_help)
        help_menu.addAction('Горячие клавиши', self.show_hotkeys)
        help_menu.addSeparator()
        help_menu.addAction('О программе', self.show_about)

    def new_file(self):
        print("Новый файл")

    def open_file(self):
        print("Открыть файл")

    def save_file(self):
        print("Сохранить файл")

    def save_file_as(self):
        print("Сохранить как")

    def open_settings(self):
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            settings_window = SettingsWindow(self.viewer.app3d.arc, self)
            settings_window.exec_()

    def show_help(self):
        QtWidgets.QMessageBox.information(
            self, "Справка",
            "Управление:\n\n"
            "• ЛКМ - вращение камеры\n"
            "• ПКМ - панорамирование\n"
            "• Колесо мыши - масштабирование\n"
            "• F12 - полный экран\n"
            "• Esc - выход из полного экрана"
        )

    def show_hotkeys(self):
        QtWidgets.QMessageBox.information(
            self, "Горячие клавиши",
            "F12 - Переключить полный экран\n"
            "Esc - Выйти из полного экрана"
        )

    def show_about(self):
        QtWidgets.QMessageBox.about(
            self, "О программе",
            "GTSTREAM\n\n"
            "Система загрузки грузовиков\n"
            "Версия 1.0\n\n"
            "Разработано с использованием:\n"
            "• Python\n"
            "• PyQt5\n"
            "• Panda3D"
        )

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
