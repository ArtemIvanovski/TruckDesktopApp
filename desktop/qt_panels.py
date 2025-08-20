from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
from app3d import TruckLoadingApp
from box_widgets import BoxManagementWidget


class LeftSidebar(QtWidgets.QWidget):
    toggled = QtCore.pyqtSignal(bool)

    def __init__(self, get_app3d, units_manager, parent=None):
        super().__init__(parent)
        self.get_app3d = get_app3d
        self.units_manager = units_manager
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
        lay.setSpacing(8)

        # Panel title
        title = QtWidgets.QLabel("Настройки прицепа")
        title.setObjectName("PanelTitle")
        title.setStyleSheet("""
            QLabel { 
                font-weight: bold; 
                font-size: 12px; 
                color: #2c3e50;
                padding: 4px;
                background-color: #ecf0f1;
                border-radius: 3px;
            }
        """)
        lay.addWidget(title)

        # Tent state section
        self.tent_btn = QtWidgets.QPushButton("🎪 Состояние тента ▲")
        self.tent_btn.setCheckable(True)
        self.tent_btn.setChecked(True)
        self.tent_btn.clicked.connect(self.toggle_tent)
        self.tent_btn.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #3498db;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
        lay.addWidget(self.tent_btn)

        self.tent_widget = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(self.tent_widget)
        v.setContentsMargins(8, 4, 8, 8)
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
                border: 1px solid #bdc3c7;
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
        lay.addWidget(self.tent_widget)

        # Presets section
        self.presets_btn = QtWidgets.QPushButton("📏 Размеры ▲")
        self.presets_btn.setCheckable(True)
        self.presets_btn.setChecked(True)
        self.presets_btn.clicked.connect(self.toggle_presets)
        self.presets_btn.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #3498db;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
        lay.addWidget(self.presets_btn)

        self.presets_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(self.presets_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(5)
        presets = [
            ("Тент 13.6", 1360, 260, 245),
            ("Мега", 1360, 300, 245),
            ("Конт 40ф", 1203, 239, 235),
            ("Конт 20ф", 590, 239, 235),
            ("Рефр", 1340, 239, 235),
            ("Тент 16.5", 1650, 260, 245),
        ]
        grp = QtWidgets.QButtonGroup(self.presets_widget)
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
                    border: 1px solid #bdc3c7;
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
        lay.addWidget(self.presets_widget)

        # Custom size section
        self.custom_btn = QtWidgets.QPushButton("⚙️ Свой размер ▲")
        self.custom_btn.setCheckable(True)
        self.custom_btn.clicked.connect(self.toggle_custom)
        self.custom_btn.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                color: #2c3e50;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #3498db;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
        lay.addWidget(self.custom_btn)

        self.custom_widget = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(self.custom_widget)
        grid.setContentsMargins(8, 4, 8, 8)
        grid.setSpacing(6)

        input_style = """
            QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                font-size: 10px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #3498db;
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

        btn_apply = QtWidgets.QPushButton("Применить")
        btn_apply.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                color: white;
                background-color: #27ae60;
                border: none;
                border-radius: 4px;
                padding: 8px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        grid.addWidget(btn_apply, 3, 0, 1, 2)
        btn_apply.clicked.connect(self._apply_custom)
        self.custom_widget.hide()
        lay.addWidget(self.custom_widget)

        # Reset
        btn_reset = QtWidgets.QPushButton("Сбросить")
        btn_reset.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                color: #2c3e50;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
        """)
        btn_reset.clicked.connect(self._reset_defaults)
        lay.addWidget(btn_reset)

        lay.addStretch(1)
        return w

    def _build_boxes_panel(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        w.setObjectName("BoxesPanel")

        self.box_management = BoxManagementWidget(self.units_manager, w)

        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.box_management)

        return w

    def get_box_manager(self):
        if hasattr(self, 'box_management'):
            return self.box_management.get_box_manager()
        return None

    def _apply_custom(self):
        try:
            w = int(self.ed_w.text())
            h = int(self.ed_h.text())
            d = int(self.ed_d.text())
        except Exception:
            return
        self._switch_truck(w, h, d)

    def _reset_defaults(self):
        self._set_tent_alpha(0.0)
        self._switch_truck(1650, 260, 245)

    def toggle_tent(self):
        if self.tent_btn.isChecked():
            self.tent_widget.show()
            self.tent_btn.setText("🎪 Состояние тента ▲")
        else:
            self.tent_widget.hide()
            self.tent_btn.setText("🎪 Состояние тента ▼")

    def toggle_presets(self):
        if self.presets_btn.isChecked():
            self.presets_widget.show()
            self.presets_btn.setText("📏 Размеры ▲")
        else:
            self.presets_widget.hide()
            self.presets_btn.setText("📏 Размеры ▼")

    def toggle_custom(self):
        if self.custom_btn.isChecked():
            self.custom_widget.show()
            self.custom_btn.setText("⚙️ Свой размер ▲")
        else:
            self.custom_widget.hide()
            self.custom_btn.setText("⚙️ Свой размер ▼")

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