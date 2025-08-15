from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
from app3d import TruckLoadingApp
from box_widgets import BoxManagementWidget


class LeftSidebar(QtWidgets.QWidget):
    toggled = QtCore.pyqtSignal(bool)

    def __init__(self, get_app3d, parent=None):
        super().__init__(parent)
        self.get_app3d = get_app3d
        self.setObjectName("LeftSidebar")
        self.active_panel = None
        self._setup_ui()

    def _setup_ui(self):
        self.bar_width = 12  # Увеличили для читаемости надписи
        self.panel_width = 250  # Увеличили ширину для комфортного отображения коробок
        self.setFixedWidth(self.bar_width)  # Initially only bar width

        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Vertical bar
        bar = QtWidgets.QWidget(self)
        bar.setFixedWidth(self.bar_width)
        bar_lay = QtWidgets.QVBoxLayout(bar)
        bar_lay.setContentsMargins(0, 0, 0, 0)
        bar_lay.setSpacing(2)

        # Кнопка для прицепа
        self.btn_truck = self._make_vertical_button("Кузов")
        self.btn_truck.clicked.connect(lambda: self._toggle_panel("truck"))
        bar_lay.addWidget(self.btn_truck)

        # Кнопка для коробок
        self.btn_boxes = self._make_vertical_button("Коробки")
        self.btn_boxes.clicked.connect(lambda: self._toggle_panel("boxes"))
        bar_lay.addWidget(self.btn_boxes)

        bar_lay.addStretch(1)
        root.addWidget(bar)

        # Panel container to the right of bar
        self.panel_container = QtWidgets.QStackedWidget()
        self.panel_container.setFixedWidth(self.panel_width)
        self.panel_container.hide()
        root.addWidget(self.panel_container)

        # Build panels
        self.truck_panel = self._build_truck_panel()
        self.panel_container.addWidget(self.truck_panel)

        self.boxes_panel = self._build_boxes_panel()
        self.panel_container.addWidget(self.boxes_panel)

    def _make_vertical_button(self, text: str) -> QtWidgets.QToolButton:
        btn = QtWidgets.QToolButton(self)
        btn.setText(text)
        btn.setCheckable(True)
        btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        btn.setMinimumHeight(80)  # Уменьшили высота для размещения двух кнопок
        btn.setStyleSheet("""
            QToolButton {
                font-weight: 700;
                font-size: 10px;
                color: #2c3e50;
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 4px;
                text-align: center;
            }
            QToolButton:hover {
                background-color: #d5dbdb;
                border-color: #3498db;
                transform: scale(1.02);
            }
            QToolButton:checked {
                background-color: #3498db;
                color: white;
                border-color: #2980b9;
                font-weight: 800;
            }
        """)
        btn.setArrowType(QtCore.Qt.RightArrow)
        return btn

    def _toggle_panel(self, panel_type: str):
        """Переключить панель"""
        if self.active_panel == panel_type:
            # Скрыть активную панель
            self.panel_container.hide()
            self.setFixedWidth(self.bar_width)
            self.active_panel = None
            self._update_button_states()
            self.toggled.emit(False)
        else:
            # Показать новую панель
            if panel_type == "truck":
                self.panel_container.setCurrentWidget(self.truck_panel)
            elif panel_type == "boxes":
                self.panel_container.setCurrentWidget(self.boxes_panel)

            self.panel_container.show()
            self.setFixedWidth(self.bar_width + self.panel_width)
            self.active_panel = panel_type
            self._update_button_states()
            self.toggled.emit(True)

    def _update_button_states(self):
        """Обновить состояния кнопок"""
        self.btn_truck.setChecked(self.active_panel == "truck")
        self.btn_boxes.setChecked(self.active_panel == "boxes")

    def _build_truck_panel(self) -> QtWidgets.QWidget:
        """Панель настроек прицепа (существующая логика)"""
        w = QtWidgets.QWidget()
        w.setObjectName("TruckPanel")
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(5)

        # Panel title
        title = QtWidgets.QLabel("Настройки прицепа")
        title.setObjectName("PanelTitle")
        title.setStyleSheet("""
            QLabel#PanelTitle { 
                font-weight: bold; 
                font-size: 14px; 
                margin-bottom: 8px; 
                color: #2c3e50;
                padding: 6px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
        """)
        lay.addWidget(title)

        # Open/Close group
        gb_state = QtWidgets.QGroupBox("Состояние тента")
        gb_state.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: #fdfdfd;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px 0 6px;
                background-color: white;
                border-radius: 3px;
            }
        """)
        v = QtWidgets.QVBoxLayout(gb_state)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(6)
        btn_open = QtWidgets.QRadioButton("Открыт")
        btn_close = QtWidgets.QRadioButton("Закрыт")
        btn_open.setChecked(True)
        radio_style = """
            QRadioButton {
                font-size: 11px;
                font-weight: 500;
                color: #2c3e50;
                spacing: 6px;
                padding: 2px;
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
        btn_open.setStyleSheet(radio_style)
        btn_close.setStyleSheet(radio_style)
        v.addWidget(btn_open)
        v.addWidget(btn_close)
        btn_open.toggled.connect(lambda on: on and self._set_tent_alpha(0.0))
        btn_close.toggled.connect(lambda on: on and self._set_tent_alpha(0.3))
        lay.addWidget(gb_state)

        # Presets group
        gb_presets = QtWidgets.QGroupBox("Размеры")
        gb_presets.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: #fdfdfd;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px 0 6px;
                background-color: white;
                border-radius: 3px;
            }
        """)
        form = QtWidgets.QFormLayout(gb_presets)
        form.setContentsMargins(8, 8, 8, 8)
        form.setSpacing(5)
        presets = [
            ("Тент 13.6", 1360, 260, 245),
            ("Мега", 1360, 300, 245),
            ("Конт 40ф", 1203, 239, 235),
            ("Конт 20ф", 590, 239, 235),
            ("Рефр", 1340, 239, 235),
            ("Тент 16.5", 1650, 260, 245),
        ]
        grp = QtWidgets.QButtonGroup(gb_presets)
        grp.setExclusive(True)
        for title, W, H, D in presets:
            rb = QtWidgets.QRadioButton(title)
            rb.setStyleSheet("""
                QRadioButton {
                    font-size: 11px;
                    font-weight: 500;
                    color: #2c3e50;
                    spacing: 6px;
                    padding: 2px;
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
            """)
            grp.addButton(rb)
            form.addRow(rb)
            rb.toggled.connect(lambda on, w=W, h=H, d=D: on and self._switch_truck(w, h, d))
        lay.addWidget(gb_presets)

        # Custom size
        gb_custom = QtWidgets.QGroupBox("Свой размер")
        gb_custom.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: #fdfdfd;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px 0 6px;
                background-color: white;
                border-radius: 3px;
            }
        """)
        grid = QtWidgets.QGridLayout(gb_custom)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        input_style = """
            QLineEdit {
                font-size: 11px;
                font-weight: 500;
                padding: 4px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                color: #2c3e50;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
            QLineEdit:hover {
                border-color: #95a5a6;
            }
        """

        label_style = """
            QLabel {
                font-size: 11px;
                font-weight: 600;
                color: #2c3e50;
            }
        """

        self.ed_w = QtWidgets.QLineEdit();
        self.ed_h = QtWidgets.QLineEdit();
        self.ed_d = QtWidgets.QLineEdit()
        for ed in (self.ed_w, self.ed_h, self.ed_d):
            ed.setMaxLength(4)
            ed.setValidator(QtGui.QIntValidator(1, 9999, w))
            ed.setPlaceholderText("см")
            ed.setStyleSheet(input_style)
            ed.setFixedHeight(24)

        lbl_w = QtWidgets.QLabel("Длина");
        lbl_w.setStyleSheet(label_style)
        lbl_h = QtWidgets.QLabel("Высота");
        lbl_h.setStyleSheet(label_style)
        lbl_d = QtWidgets.QLabel("Ширина");
        lbl_d.setStyleSheet(label_style)

        grid.addWidget(lbl_w, 0, 0);
        grid.addWidget(self.ed_w, 0, 1)
        grid.addWidget(lbl_h, 1, 0);
        grid.addWidget(self.ed_h, 1, 1)
        grid.addWidget(lbl_d, 2, 0);
        grid.addWidget(self.ed_d, 2, 1)

        self.cb_custom = QtWidgets.QCheckBox("Свой размер")
        self.cb_custom.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                font-weight: 500;
                color: #2c3e50;
                spacing: 6px;
                padding: 2px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
            QCheckBox:hover {
                color: #3498db;
            }
        """)
        grid.addWidget(self.cb_custom, 3, 0, 1, 2)

        btn_apply = QtWidgets.QPushButton("Применить")
        btn_apply.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                color: white;
                background-color: #3498db;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #21618c;
                transform: translateY(1px);
            }
        """)
        grid.addWidget(btn_apply, 4, 0, 1, 2)
        btn_apply.clicked.connect(self._apply_custom)
        lay.addWidget(gb_custom)

        # Reset
        btn_reset = QtWidgets.QPushButton("Сбросить")
        btn_reset.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                padding: 6px 12px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
                border-color: #95a5a6;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
                transform: translateY(1px);
            }
        """)
        btn_reset.clicked.connect(self._reset_defaults)
        lay.addWidget(btn_reset)

        lay.addStretch(1)
        return w

    def _build_boxes_panel(self) -> QtWidgets.QWidget:
        """Панель управления коробками"""
        w = QtWidgets.QWidget()
        w.setObjectName("BoxesPanel")

        # Используем BoxManagementWidget для управления коробками
        self.box_management = BoxManagementWidget(w)

        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.box_management)

        return w

    def get_box_manager(self):
        """Получить менеджер коробок"""
        if hasattr(self, 'box_management'):
            return self.box_management.get_box_manager()
        return None

    def _apply_custom(self):
        if not self.cb_custom.isChecked():
            return
        try:
            w = int(self.ed_w.text())
            h = int(self.ed_h.text())
            d = int(self.ed_d.text())
        except Exception:
            return
        self._switch_truck(w, h, d)

    def _reset_defaults(self):
        # Default: Тент 16.5 открыт
        self._set_tent_alpha(0.0)
        self._switch_truck(1650, 260, 245)

    # helpers
    def _app3d(self):
        try:
            return self.get_app3d()
        except Exception:
            return None

    def _set_tent_alpha(self, a: float):
        app = self._app3d()
        if app:
            app.set_tent_alpha(a)

    def _switch_truck(self, w: int, h: int, d: int):
        app = self._app3d()
        if app:
            app.switch_truck(w, h, d)