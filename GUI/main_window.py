import logging

from GUI.left_sidebar.left_sidebar import LeftSidebar
from GUI.panda_widget import PandaWidget
from GUI.settings_window.settings_window import SettingsWindow
from core.hotkeys import HotkeyController
from utils.setting_deploy import get_resource_path
from core.i18n import tr, translation_manager, TranslatableMixin
from PyQt5 import QtWidgets, QtCore, QtGui

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

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow, TranslatableMixin):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(QtGui.QIcon(get_resource_path("assets/icon/logo.png")))

        # Устанавливаем размер окна на весь доступный экран
        screen = QtWidgets.QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            self.resize(screen_geometry.width(), screen_geometry.height())
            self.move(screen_geometry.x(), screen_geometry.y())

        from core.units import UnitsManager
        self.units_manager = UnitsManager()

        self.viewer = PandaWidget(self)
        self.sidebar = LeftSidebar(lambda: self.viewer.app3d, self.units_manager, self)

        self._setup_central_widget()

        self.viewer.ready.connect(self._on_viewer_ready)
        self.sidebar.toggled.connect(self._on_sidebar_toggled)

        self.hotkeys = HotkeyController(self)
        # Подключаем сигналы горячих клавиш к функциям
        self.hotkeys.rotate_box.connect(self.on_rotate_box)
        self.hotkeys.delete_box.connect(self.on_delete_box)
        self.hotkeys.hide_box.connect(self.on_hide_box)

        self.setup_menu_bar()
        self.setStatusBar(None)

        self._apply_styles()
        self.retranslate_ui()

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

    def on_rotate_box(self):
        """Поворот выбранной коробки через горячую клавишу"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            self.viewer.app3d.rotate_selected_box()

    def on_delete_box(self):
        """Удаление выбранной коробки через горячую клавишу"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            self.viewer.app3d.delete_selected_box()

    def on_hide_box(self):
        """Скрытие выбранной коробки через горячую клавишу"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            self.viewer.app3d.hide_selected_box()

    def setup_menu_bar(self):
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        self.file_menu = menubar.addMenu('')
        self.action_new = self.file_menu.addAction('', self.new_file, 'Ctrl+N')
        self.action_open = self.file_menu.addAction('', self.open_file, 'Ctrl+O')
        self.action_save = self.file_menu.addAction('', self.save_file, 'Ctrl+S')
        self.action_save_as = self.file_menu.addAction('', self.save_file_as, 'Ctrl+Shift+S')
        self.file_menu.addSeparator()
        self.action_exit = self.file_menu.addAction('', self.close, 'Ctrl+Q')

        self.view_menu = menubar.addMenu('')
        self.action_view_top = self.view_menu.addAction('', self._view_top, 'Ctrl+1')
        self.action_view_left = self.view_menu.addAction('', self._view_left, 'Ctrl+2')
        self.action_view_right = self.view_menu.addAction('', self._view_right, 'Ctrl+3')
        self.action_view_reset = self.view_menu.addAction('', self._view_reset, 'Ctrl+0')
        self.view_menu.addSeparator()
        self.action_fullscreen = self.view_menu.addAction('', self._toggle_fullscreen, 'F11')

        self.settings_menu = menubar.addMenu('')
        self.action_settings = self.settings_menu.addAction('', self.open_settings, 'Ctrl+,')

        self.help_menu = menubar.addMenu('')
        self.action_help = self.help_menu.addAction('', self.show_help, 'F1')
        self.action_hotkeys = self.help_menu.addAction('', self.show_hotkeys, 'Ctrl+/')
        self.help_menu.addSeparator()
        self.action_about = self.help_menu.addAction('', self.show_about)

    # Методы для обработки действий меню
    def new_file(self):
        print("Новый файл")

    def open_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, tr("Открыть файл"), "", tr("JSON файлы (*.json);;Все файлы (*.*)")
        )
        if file_path:
            print(f"Открыть файл: {file_path}")

    def save_file(self):
        print("Сохранить файл")

    def save_file_as(self):
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, tr("Сохранить как"), "", tr("JSON файлы (*.json);;Все файлы (*.*)")
        )
        if file_path:
            print(f"Сохранить как: {file_path}")

    def open_settings(self):
        """Открытие окна настроек"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            graphics_manager = getattr(self.viewer.app3d, 'graphics_manager', None)
            settings_window = SettingsWindow(self.viewer.app3d.arc, graphics_manager, self.units_manager, self)
            settings_window.exec_()

    def show_help(self):
        """Показать справку"""
        help_text = f"""
        <h3>{tr('Управление камерой:')}</h3>
        <ul>
        <li><b>{tr('Левая кнопка мыши')}</b> - {tr('панорамирование (перемещение)')}</li>
        <li><b>{tr('Правая кнопка мыши')}</b> - {tr('вращение камеры')}</li>
        <li><b>{tr('Колесо мыши')}</b> - {tr('масштабирование (приближение/отдаление)')}</li>
        </ul>

        <h3>{tr('Горячие клавиши')}:</h3>
        <ul>
        <li><b>F11, F12</b> - {tr('переключить полный экран')}</li>
        <li><b>Esc</b> - {tr('выйти из полного экрана')}</li>
        <li><b>Ctrl+1,2,3</b> - {tr('быстрые виды (сверху, слева, справа)')}</li>
        <li><b>Ctrl+0</b> - {tr('сбросить вид')}</li>
        </ul>

        <h3>{tr('Работа с коробками:')}</h3>
        <ul>
        <li><b>R / К</b> - {tr('повернуть коробку на 90 градусов')}</li>
        <li><b>W</b> - {tr('вращать коробку вперед (вертикально)')}</li>
        <li><b>S</b> - {tr('вращать коробку назад (вертикально)')}</li>
        <li><b>A</b> - {tr('вращать коробку влево (горизонтально)')}</li>
        <li><b>D</b> - {tr('вращать коробку вправо (горизонтально)')}</li>
        <li><b>Backspace / Delete</b> - {tr('полностью удалить коробку')}</li>
        <li><b>H / Р</b> - {tr('спрятать коробку (вернуть в список)')}</li>
        </ul>

        <h3>{tr('Интерфейс:')}</h3>
        <ul>
        <li>{tr('Левая панель содержит настройки кузова и управление коробками')}</li>
        <li>{tr('Нажмите на вкладку для открытия соответствующей панели')}</li>
        <li>{tr('Нажмите еще раз на активную вкладку для закрытия панели')}</li>
        <li>{tr('Используйте кнопку ✕ в правом верхнем углу панели для закрытия')}</li>
        <li>{tr('Нажмите Esc для закрытия открытой панели')}</li>
        </ul>
        """

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(tr("Справка"))
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(help_text)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec_()

    def show_hotkeys(self):
        """Показать горячие клавиши"""
        hotkeys_text = f"""
        <h3>{tr('Основные команды:')}</h3>
        <table>
        <tr><td><b>F11, F12</b></td><td>{tr('Полный экран')}</td></tr>
        <tr><td><b>Esc</b></td><td>{tr('Закрыть панель / Выход из полного экрана')}</td></tr>
        <tr><td><b>Ctrl+N</b></td><td>{tr('Новый файл')}</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>{tr('Открыть файл')}</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>{tr('Сохранить')}</td></tr>
        <tr><td><b>Ctrl+Shift+S</b></td><td>{tr('Сохранить как')}</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>{tr('Выход')}</td></tr>
        <tr><td><b>Ctrl+,</b></td><td>{tr('Настройки')}</td></tr>
        <tr><td><b>F1</b></td><td>{tr('Справка')}</td></tr>
        <tr><td><b>Ctrl+/</b></td><td>{tr('Горячие клавиши')}</td></tr>
        </table>
        
        <h3>{tr('Управление камерой:')}</h3>
        <table>
        <tr><td><b>Ctrl+1</b></td><td>{tr('Вид сверху')}</td></tr>
        <tr><td><b>Ctrl+2</b></td><td>{tr('Вид слева')}</td></tr>
        <tr><td><b>Ctrl+3</b></td><td>{tr('Вид справа')}</td></tr>
        <tr><td><b>Ctrl+0</b></td><td>{tr('Сбросить вид')}</td></tr>
        </table>
        
        <h3>{tr('Работа с коробками:')}</h3>
        <table>
        <tr><td><b>R / К</b></td><td>{tr('Повернуть коробку на 90°')}</td></tr>
        <tr><td><b>W</b></td><td>{tr('Вращать вперед (вертикально)')}</td></tr>
        <tr><td><b>S</b></td><td>{tr('Вращать назад (вертикально)')}</td></tr>
        <tr><td><b>A</b></td><td>{tr('Вращать влево (горизонтально)')}</td></tr>
        <tr><td><b>D</b></td><td>{tr('Вращать вправо (горизонтально)')}</td></tr>
        <tr><td><b>Backspace / Delete</b></td><td>{tr('Удалить коробку')}</td></tr>
        <tr><td><b>H / Р</b></td><td>{tr('Спрятать коробку')}</td></tr>
        </table>
        """

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(tr("Горячие клавиши"))
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(hotkeys_text)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec_()

    def show_about(self):
        """Показать информацию о программе"""
        about_text = f"""
        <h2>GTSTREAM</h2>
        <p><b>{tr('Система загрузки грузовиков')}</b></p>
        <p>{tr('Версия 1.0')}</p>

        <h3>{tr('Технологии:')}</h3>
        <ul>
        <li>Python 3</li>
        <li>PyQt5 - {tr('пользовательский интерфейс')}</li>
        <li>Panda3D - {tr('3D-движок')}</li>
        </ul>

        <p>© 2024 GTSTREAM Team</p>
        """

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle(tr("О программе"))
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(about_text)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec_()

    def _view_top(self):
        """Вид сверху"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            cam = self.viewer.app3d.arc
            cam.target.set(0, 0, 0)
            cam.radius = 3000
            cam.alpha = 3.14159265 / 2
            cam.beta = 3.14159265 / 2
            cam.update()

    def _view_left(self):
        """Вид слева"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            cam = self.viewer.app3d.arc
            cam.target.set(0, 0, 0)
            cam.radius = 3000
            cam.alpha = 3.14159265 / 2
            cam.beta = 3.14159265
            cam.update()

    def _view_right(self):
        """Вид справа"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            cam = self.viewer.app3d.arc
            cam.target.set(0, 0, 0)
            cam.radius = 3000
            cam.alpha = 3.14159265 / 2
            cam.beta = 0
            cam.update()

    def _view_reset(self):
        """Сброс вида"""
        if hasattr(self.viewer, 'app3d') and self.viewer.app3d:
            cam = self.viewer.app3d.arc
            cam.target.set(0, 0, 0)
            cam.radius = 3000
            cam.alpha = 3.14159265 / 2
            cam.beta = 3.14159265 / 4  # Исправлено для соответствия начальному углу
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

    def retranslate_ui(self):
        self.setWindowTitle("GTSTREAM")
        
        self.file_menu.setTitle(f"📁 {tr('Файл')}")
        self.action_new.setText(f"🆕 {tr('Новый')}")
        self.action_open.setText(f"📂 {tr('Открыть')}...")
        self.action_save.setText(f"💾 {tr('Сохранить')}")
        self.action_save_as.setText(f"💾 {tr('Сохранить как')}...")
        self.action_exit.setText(f"❌ {tr('Выход')}")
        
        self.view_menu.setTitle(f"👁 {tr('Вид')}")
        self.action_view_top.setText(f"⬆️ {tr('Сверху')}")
        self.action_view_left.setText(f"⬅️ {tr('Слева')}")
        self.action_view_right.setText(f"➡️ {tr('Справа')}")
        self.action_view_reset.setText(f"🔄 {tr('Сбросить')}")
        self.action_fullscreen.setText(f"🖥 {tr('Полный экран')}")
        
        self.settings_menu.setTitle(f"⚙️ {tr('Настройки')}")
        self.action_settings.setText(f"🔧 {tr('Настройки')}...")
        
        self.help_menu.setTitle(f"❓ {tr('Помощь')}")
        self.action_help.setText(f"📖 {tr('Справка')}")
        self.action_hotkeys.setText(f"⌨️ {tr('Горячие клавиши')}")
        self.action_about.setText(f"ℹ️ {tr('О программе')}")