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
        self.setMinimumSize(1000, 700)

        from units import UnitsManager
        self.units_manager = UnitsManager()

        self.viewer = PandaWidget(self)
        self.sidebar = LeftSidebar(lambda: self.viewer.app3d, self.units_manager, self)

        self._setup_central_widget()

        self.viewer.ready.connect(self._on_viewer_ready)
        self.sidebar.toggled.connect(self._on_sidebar_toggled)

        self.hotkeys = HotkeyController(self)
        self.setup_menu_bar()
        self.setStatusBar(None)

        self._apply_styles()

    def _setup_central_widget(self):
        """Настройка центрального виджета с панелью и 3D областью"""
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # Главный layout
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Добавляем боковую панель
        main_layout.addWidget(self.sidebar)

        # Добавляем 3D виджет
        main_layout.addWidget(self.viewer, 1)  # stretch factor = 1

    def _apply_styles(self):
        """Применение стилей к главному окну"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QMenuBar {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 4px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QMenuBar::item:selected {
                background-color: #34495e;
            }
            QMenuBar::item:pressed {
                background-color: #3498db;
            }
            QMenu {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #ecf0f1;
                margin: 4px 8px;
            }
        """)

    def _on_sidebar_toggled(self, expanded):
        """Обработчик изменения состояния боковой панели"""
        if expanded:
            logging.debug("Sidebar expanded")
        else:
            logging.debug("Sidebar collapsed")

    def _on_viewer_ready(self):
        """Обработчик готовности 3D-движка"""
        logging.info("[Qt] Panda3D ready")

    def setup_menu_bar(self):
        """Настройка меню"""
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        # Меню "Файл"
        file_menu = menubar.addMenu('📁 Файл')
        file_menu.addAction('🆕 Новый', self.new_file, 'Ctrl+N')
        file_menu.addAction('📂 Открыть...', self.open_file, 'Ctrl+O')
        file_menu.addAction('💾 Сохранить', self.save_file, 'Ctrl+S')
        file_menu.addAction('💾 Сохранить как...', self.save_file_as, 'Ctrl+Shift+S')
        file_menu.addSeparator()
        file_menu.addAction('❌ Выход', self.close, 'Ctrl+Q')

        # Меню "Вид"
        view_menu = menubar.addMenu('👁 Вид')
        view_menu.addAction('⬆️ Сверху', self._view_top, 'Ctrl+1')
        view_menu.addAction('⬅️ Слева', self._view_left, 'Ctrl+2')
        view_menu.addAction('➡️ Справа', self._view_right, 'Ctrl+3')
        view_menu.addAction('🔄 Сбросить', self._view_reset, 'Ctrl+0')
        view_menu.addSeparator()
        view_menu.addAction('🖥 Полный экран', self._toggle_fullscreen, 'F11')

        # Меню "Настройки"
        settings_menu = menubar.addMenu('⚙️ Настройки')
        settings_menu.addAction('🔧 Настройки...', self.open_settings, 'Ctrl+,')

        # Меню "Помощь"
        help_menu = menubar.addMenu('❓ Помощь')
        help_menu.addAction('📖 Справка', self.show_help, 'F1')
        help_menu.addAction('⌨️ Горячие клавиши', self.show_hotkeys, 'Ctrl+/')
        help_menu.addSeparator()
        help_menu.addAction('ℹ️ О программе', self.show_about)

    # Методы для обработки действий меню
    def new_file(self):
        print("Новый файл")

    def open_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Открыть файл", "", "JSON файлы (*.json);;Все файлы (*.*)"
        )
        if file_path:
            print(f"Открыть файл: {file_path}")

    def save_file(self):
        print("Сохранить файл")

    def save_file_as(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Сохранить как", "", "JSON файлы (*.json);;Все файлы (*.*)"
        )
        if file_path:
            print(f"Сохранить как: {file_path}")

    def open_settings(self):
        """Открытие окна настроек"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            graphics_manager = getattr(self.viewer.app3d, 'graphics_manager', None)
            settings_window = SettingsWindow(self.viewer.app3d.arc, graphics_manager, self)
            settings_window.exec_()

    def show_help(self):
        """Показать справку"""
        help_text = """
        <h3>Управление камерой:</h3>
        <ul>
        <li><b>Левая кнопка мыши</b> - панорамирование (перемещение)</li>
        <li><b>Правая кнопка мыши</b> - вращение камеры</li>
        <li><b>Колесо мыши</b> - масштабирование (приближение/отдаление)</li>
        </ul>

        <h3>Горячие клавиши:</h3>
        <ul>
        <li><b>F11</b> - переключить полный экран</li>
        <li><b>F12</b> - переключить полный экран (альтернативная)</li>
        <li><b>Esc</b> - выйти из полного экрана</li>
        <li><b>Ctrl+1,2,3</b> - быстрые виды (сверху, слева, справа)</li>
        <li><b>Ctrl+0</b> - сбросить вид</li>
        </ul>

        <h3>Интерфейс:</h3>
        <ul>
        <li>Левая панель содержит настройки кузова и управление коробками</li>
        <li>Нажмите на вкладку для открытия соответствующей панели</li>
        <li>Нажмите еще раз на активную вкладку для закрытия панели</li>
        <li>Используйте кнопку ✕ в правом верхнем углу панели для закрытия</li>
        <li>Нажмите <b>Esc</b> для закрытия открытой панели</li>
        </ul>
        """

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Справка")
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(help_text)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec_()

    def show_hotkeys(self):
        """Показать горячие клавиши"""
        hotkeys_text = """
        <table>
        <tr><td><b>F11, F12</b></td><td>Полный экран</td></tr>
        <tr><td><b>Esc</b></td><td>Закрыть панель / Выход из полного экрана</td></tr>
        <tr><td><b>Ctrl+N</b></td><td>Новый файл</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Открыть файл</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Сохранить</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Выход</td></tr>
        <tr><td><b>Ctrl+1</b></td><td>Вид сверху</td></tr>
        <tr><td><b>Ctrl+2</b></td><td>Вид слева</td></tr>
        <tr><td><b>Ctrl+3</b></td><td>Вид справа</td></tr>
        <tr><td><b>Ctrl+0</b></td><td>Сбросить вид</td></tr>
        <tr><td><b>Ctrl+,</b></td><td>Настройки</td></tr>
        <tr><td><b>F1</b></td><td>Справка</td></tr>
        </table>
        """

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Горячие клавиши")
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(hotkeys_text)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec_()

    def show_about(self):
        """Показать информацию о программе"""
        about_text = """
        <h2>GTSTREAM</h2>
        <p><b>Система загрузки грузовиков</b></p>
        <p>Версия 1.0</p>

        <h3>Технологии:</h3>
        <ul>
        <li>Python 3</li>
        <li>PyQt5 - пользовательский интерфейс</li>
        <li>Panda3D - 3D-движок</li>
        </ul>

        <p>© 2024 GTSTREAM Team</p>
        """

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("О программе")
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(about_text)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec_()

    # Методы управления видом
    def _view_top(self):
        """Вид сверху"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            cam = self.viewer.app3d.arc
            cam.radius = 1400
            cam.alpha = 3.14159265 / 2
            cam.beta = 0.00001
            cam.update()

    def _view_left(self):
        """Вид слева"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            cam = self.viewer.app3d.arc
            cam.radius = 1400
            cam.alpha = 3.14159265 / 2
            cam.beta = 3.14159265 / 2
            cam.update()

    def _view_right(self):
        """Вид справа"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            cam = self.viewer.app3d.arc
            cam.radius = 1400
            cam.alpha = -3.14159265 / 2
            cam.beta = 3.14159265 / 2
            cam.update()

    def _view_reset(self):
        """Сброс вида"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            cam = self.viewer.app3d.arc
            cam.radius = 2000
            cam.alpha = 3.14159265 / 2
            cam.beta = 3.14159265 / 3
            cam.target.set(0, 300, 0)
            cam.update()

    def _toggle_fullscreen(self):
        """Переключение полноэкранного режима"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        # Дополнительная обработка F12 для полного экрана
        if event.key() == QtCore.Qt.Key_F12:
            self._toggle_fullscreen()
            return

        # Закрытие левой панели на Escape
        if event.key() == QtCore.Qt.Key_Escape:
            if hasattr(self, 'sidebar') and self.sidebar.is_expanded:
                self.sidebar._collapse()
                event.accept()
                return
            elif self.isFullScreen():
                self.showNormal()
                event.accept()
                return

        super().keyPressEvent(event)