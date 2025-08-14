from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QPainter, QFont, QFontMetrics
import math


class VerticalTabButton(QtWidgets.QPushButton):
    """Кнопка таба с вертикальным текстом"""

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setText("")  # Убираем обычный текст
        self.vertical_text = text
        self.setCheckable(True)
        self.setFixedSize(40, 120)  # Ширина 40px, высота для текста

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Настройка шрифта
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)

        # Цвет текста в зависимости от состояния - сделаем более контрастным
        if self.isChecked():
            painter.setPen(QtGui.QColor(255, 255, 255))  # Белый для активного
        else:
            painter.setPen(QtGui.QColor(189, 195, 199))  # Светло-серый для неактивного

        # Поворот для вертикального текста
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(-90)

        # Рисуем текст по центру
        text_rect = painter.fontMetrics().boundingRect(self.vertical_text)
        painter.drawText(-text_rect.width() / 2, text_rect.height() / 4, self.vertical_text)


class TruckSettingsPanel(QtWidgets.QWidget):
    """Панель настроек кузова"""

    def __init__(self, get_app3d, parent=None):
        super().__init__(parent)
        self.get_app3d = get_app3d
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Заголовок
        title = QtWidgets.QLabel("Настройки кузова")
        title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
                border-left: 4px solid #3498db;
            }
        """)
        layout.addWidget(title)

        # Состояние тента
        tent_group = self._create_tent_group()
        layout.addWidget(tent_group)

        # Быстрые размеры
        presets_group = self._create_presets_group()
        layout.addWidget(presets_group)

        # Свой размер
        custom_group = self._create_custom_group()
        layout.addWidget(custom_group)

        layout.addStretch()

    def _create_tent_group(self):
        group = QtWidgets.QGroupBox("Тент")
        group.setStyleSheet(self._get_group_style())

        layout = QtWidgets.QVBoxLayout(group)
        layout.setSpacing(8)

        self.tent_open = QtWidgets.QRadioButton("Открыт")
        self.tent_closed = QtWidgets.QRadioButton("Закрыт")
        self.tent_open.setChecked(True)

        for radio in [self.tent_open, self.tent_closed]:
            radio.setStyleSheet(self._get_radio_style())
            layout.addWidget(radio)

        self.tent_open.toggled.connect(lambda on: on and self._set_tent_alpha(0.0))
        self.tent_closed.toggled.connect(lambda on: on and self._set_tent_alpha(0.3))

        return group

    def _create_presets_group(self):
        group = QtWidgets.QGroupBox("Быстрый выбор")
        group.setStyleSheet(self._get_group_style())

        layout = QtWidgets.QVBoxLayout(group)
        layout.setSpacing(6)

        presets = [
            ("Тент 13.6", 1360, 260, 245),
            ("Тент 16.5", 1650, 260, 245),
            ("Мега", 1360, 300, 245),
            ("Конт 40ф", 1203, 239, 235),
            ("Конт 20ф", 590, 239, 235),
            ("Рефр", 1340, 239, 235),
        ]

        self.preset_group = QtWidgets.QButtonGroup(group)

        for name, w, h, d in presets:
            btn = QtWidgets.QPushButton(name)
            btn.setStyleSheet(self._get_preset_button_style())
            btn.clicked.connect(lambda checked, _w=w, _h=h, _d=d: self._switch_truck(_w, _h, _d))
            layout.addWidget(btn)

        return group

    def _create_custom_group(self):
        group = QtWidgets.QGroupBox("Свой размер")
        group.setStyleSheet(self._get_group_style())

        layout = QtWidgets.QGridLayout(group)
        layout.setSpacing(8)

        # Поля ввода
        self.width_edit = self._create_size_edit("1650")
        self.height_edit = self._create_size_edit("260")
        self.depth_edit = self._create_size_edit("245")

        layout.addWidget(QtWidgets.QLabel("Длина:"), 0, 0)
        layout.addWidget(self.width_edit, 0, 1)
        layout.addWidget(QtWidgets.QLabel("см"), 0, 2)

        layout.addWidget(QtWidgets.QLabel("Высота:"), 1, 0)
        layout.addWidget(self.height_edit, 1, 1)
        layout.addWidget(QtWidgets.QLabel("см"), 1, 2)

        layout.addWidget(QtWidgets.QLabel("Ширина:"), 2, 0)
        layout.addWidget(self.depth_edit, 2, 1)
        layout.addWidget(QtWidgets.QLabel("см"), 2, 2)

        # Кнопка применить
        apply_btn = QtWidgets.QPushButton("Применить")
        apply_btn.setStyleSheet(self._get_apply_button_style())
        apply_btn.clicked.connect(self._apply_custom)
        layout.addWidget(apply_btn, 3, 0, 1, 3)

        return group

    def _create_size_edit(self, default_value):
        edit = QtWidgets.QLineEdit(default_value)
        edit.setMaxLength(4)
        edit.setValidator(QtGui.QIntValidator(50, 9999))
        edit.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                font-size: 11px;
                min-width: 60px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        return edit

    def _apply_custom(self):
        try:
            w = int(self.width_edit.text())
            h = int(self.height_edit.text())
            d = int(self.depth_edit.text())
            self._switch_truck(w, h, d)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Введите корректные числовые значения")

    def _switch_truck(self, w, h, d):
        app = self._app3d()
        if app:
            app.switch_truck(w, h, d)

    def _set_tent_alpha(self, alpha):
        app = self._app3d()
        if app:
            app.set_tent_alpha(alpha)

    def _app3d(self):
        try:
            return self.get_app3d()
        except Exception:
            return None

    def _get_group_style(self):
        return """
            QGroupBox {
                font-weight: 600;
                font-size: 11px;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: #fdfdfd;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 6px;
                background-color: white;
                border-radius: 2px;
            }
        """

    def _get_radio_style(self):
        return """
            QRadioButton {
                font-size: 11px;
                color: #2c3e50;
                spacing: 6px;
                padding: 3px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border-radius: 7px;
                border: 2px solid #bdc3c7;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
            QRadioButton:hover {
                color: #3498db;
            }
        """

    def _get_preset_button_style(self):
        return """
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                border: 1px solid #d5dbdb;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
                color: #2c3e50;
                min-height: 16px;
            }
            QPushButton:hover {
                background-color: #ebf3fd;
                border-color: #3498db;
                color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #d6eaf8;
                border-color: #2980b9;
            }
        """

    def _get_apply_button_style(self):
        return """
            QPushButton {
                padding: 8px;
                border: none;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                font-weight: 600;
                font-size: 11px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """


class BoxesPanel(QtWidgets.QWidget):
    """Панель управления коробками"""

    def __init__(self, get_app3d, parent=None):
        super().__init__(parent)
        self.get_app3d = get_app3d
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Заголовок
        title = QtWidgets.QLabel("Управление коробками")
        title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 4px;
                border-left: 4px solid #e74c3c;
            }
        """)
        layout.addWidget(title)

        # Заглушка - здесь будет функционал коробок
        placeholder = QtWidgets.QLabel("Функционал коробок\nбудет добавлен...")
        placeholder.setAlignment(QtCore.Qt.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                padding: 40px;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
            }
        """)
        layout.addWidget(placeholder)

        layout.addStretch()


class LeftSidebar(QtWidgets.QWidget):
    """Левая боковая панель с анимацией"""

    toggled = pyqtSignal(bool)

    def __init__(self, get_app3d, parent=None):
        super().__init__(parent)
        self.get_app3d = get_app3d
        self.setObjectName("LeftSidebar")

        # Размеры
        self.tab_bar_width = 40
        self.panel_width = 280
        self.is_expanded = False

        # Анимация
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        self._setup_ui()
        self._collapse()  # Начинаем в свернутом состоянии

    def _setup_ui(self):
        # Основной layout
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Панель с кнопками табов
        self._create_tab_bar()

        # Контейнер с содержимым панелей
        self._create_content_area()

    def _create_tab_bar(self):
        self.tab_bar = QtWidgets.QWidget()
        self.tab_bar.setFixedWidth(self.tab_bar_width)
        self.tab_bar.setStyleSheet("""
            QWidget {
                background-color: #34495e;
                border-right: 1px solid #2c3e50;
            }
        """)

        tab_layout = QtWidgets.QVBoxLayout(self.tab_bar)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(2)

        # Кнопки табов
        self.truck_tab = VerticalTabButton("КУЗОВ")
        self.boxes_tab = VerticalTabButton("КОРОБКИ")

        # Стили для кнопок
        tab_style = """
            QPushButton {
                border: none;
                background-color: transparent;
                border-radius: 0;
            }
            QPushButton:hover {
                background-color: #3e5770;
            }
            QPushButton:checked {
                background-color: #3498db;
                border-right: 3px solid #2980b9;
            }
        """

        self.truck_tab.setStyleSheet(tab_style)
        self.boxes_tab.setStyleSheet(tab_style)

        # Группа кнопок для взаимоисключающего выбора
        self.tab_group = QtWidgets.QButtonGroup()
        self.tab_group.addButton(self.truck_tab, 0)
        self.tab_group.addButton(self.boxes_tab, 1)
        self.tab_group.setExclusive(False)  # Позволяем снимать выделение

        # События
        self.truck_tab.clicked.connect(self._on_truck_tab_clicked)
        self.boxes_tab.clicked.connect(self._on_boxes_tab_clicked)

        tab_layout.addWidget(self.truck_tab)
        tab_layout.addWidget(self.boxes_tab)
        tab_layout.addStretch()

        self.main_layout.addWidget(self.tab_bar)

    def _create_content_area(self):
        self.content_area = QtWidgets.QStackedWidget()
        self.content_area.setFixedWidth(self.panel_width)
        self.content_area.setStyleSheet("""
            QStackedWidget {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-left: none;
            }
        """)

        # Создаем контейнер с кнопкой закрытия
        content_container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(content_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Верхняя панель с кнопкой закрытия
        top_bar = QtWidgets.QWidget()
        top_bar.setFixedHeight(30)
        top_bar.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                border-bottom: 1px solid #bdc3c7;
            }
        """)

        top_layout = QtWidgets.QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 4, 4, 4)
        top_layout.addStretch()

        # Кнопка закрытия
        close_btn = QtWidgets.QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setToolTip("Закрыть панель (Esc)")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #7f8c8d;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                color: white;
            }
        """)
        close_btn.clicked.connect(self._collapse)
        top_layout.addWidget(close_btn)

        container_layout.addWidget(top_bar)

        # Создаем панели
        self.truck_panel = TruckSettingsPanel(self.get_app3d, self)
        self.boxes_panel = BoxesPanel(self.get_app3d, self)

        self.content_area.addWidget(self.truck_panel)
        self.content_area.addWidget(self.boxes_panel)

        container_layout.addWidget(self.content_area)

        # Скрываем по умолчанию
        content_container.hide()
        self.content_container = content_container

        self.main_layout.addWidget(content_container)

    def _on_truck_tab_clicked(self):
        # Если кнопка была активна и мы кликнули по ней снова - закрываем панель
        if not self.truck_tab.isChecked() and self.is_expanded and self.content_area.currentWidget() == self.truck_panel:
            self._collapse()
        elif self.truck_tab.isChecked():
            # Снимаем выделение с другой кнопки
            self.boxes_tab.setChecked(False)
            self.content_area.setCurrentWidget(self.truck_panel)
            self._expand()

    def _on_boxes_tab_clicked(self):
        # Если кнопка была активна и мы кликнули по ней снова - закрываем панель
        if not self.boxes_tab.isChecked() and self.is_expanded and self.content_area.currentWidget() == self.boxes_panel:
            self._collapse()
        elif self.boxes_tab.isChecked():
            # Снимаем выделение с другой кнопки
            self.truck_tab.setChecked(False)
            self.content_area.setCurrentWidget(self.boxes_panel)
            self._expand()

    def _expand(self):
        if not self.is_expanded:
            self.is_expanded = True
            self.content_container.show()

            # Анимация расширения
            current_geometry = self.geometry()
            target_geometry = QtCore.QRect(
                current_geometry.x(),
                current_geometry.y(),
                self.tab_bar_width + self.panel_width,
                current_geometry.height()
            )

            self.animation.setStartValue(current_geometry)
            self.animation.setEndValue(target_geometry)
            self.animation.start()

            self.toggled.emit(True)

    def _collapse(self):
        if self.is_expanded:
            self.is_expanded = False

            # Снимаем выделение с табов
            self.truck_tab.setChecked(False)
            self.boxes_tab.setChecked(False)

            # Анимация сворачивания
            current_geometry = self.geometry()
            target_geometry = QtCore.QRect(
                current_geometry.x(),
                current_geometry.y(),
                self.tab_bar_width,
                current_geometry.height()
            )

            self.animation.setStartValue(current_geometry)
            self.animation.setEndValue(target_geometry)
            self.animation.finished.connect(self._on_collapse_finished)
            self.animation.start()

            self.toggled.emit(False)

    def _on_collapse_finished(self):
        """Вызывается после завершения анимации сворачивания"""
        if not self.is_expanded:
            self.content_container.hide()
        self.animation.finished.disconnect()

    def mousePressEvent(self, event):
        """Клик в пустое место панели сворачивает её"""
        if event.button() == QtCore.Qt.LeftButton and self.is_expanded:
            # Проверяем, что клик был в области содержимого, а не на кнопках
            if event.x() > self.tab_bar_width:
                # Если клик был по заголовку панели, не закрываем
                clicked_widget = self.childAt(event.pos())
                if clicked_widget and clicked_widget.objectName() in ["TruckSettingsPanel", "BoxesPanel"]:
                    # Клик по содержимому панели - не закрываем
                    pass
                else:
                    # Клик по пустому месту или границе панели - можно закрыть
                    pass
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == QtCore.Qt.Key_Escape and self.is_expanded:
            self._collapse()
            event.accept()
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event):
        """Получение фокуса для обработки клавиатуры"""
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        super().focusInEvent(event)

    def sizeHint(self):
        if self.is_expanded:
            return QtCore.QSize(self.tab_bar_width + self.panel_width, 600)
        else:
            return QtCore.QSize(self.tab_bar_width, 600)