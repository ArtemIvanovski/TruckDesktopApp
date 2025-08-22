from PyQt5 import QtWidgets, QtCore, QtGui

from GUI.box.box_management_widget import BoxManagementWidget
from GUI.load_calculation.load_calculation_widget import LoadCalculationWidget
from core.i18n import tr, TranslatableMixin


class LeftSidebar(QtWidgets.QWidget, TranslatableMixin):
    toggled = QtCore.pyqtSignal(bool)

    def __init__(self, get_app3d, units_manager, parent=None):
        super().__init__(parent)
        self.get_app3d = get_app3d
        self.units_manager = units_manager
        self.setObjectName("LeftSidebar")
        self.active_panel = None
        self._setup_ui()
        
        # Подключаемся к сигналу изменения единиц измерения
        if self.units_manager:
            self.units_manager.units_changed.connect(self._update_units_display)
        
        self.retranslate_ui()

    def _setup_ui(self):
        self.bar_width = 12
        self.panel_width = 250
        self.loads_panel_width = 280  # Увеличенная ширина для панели нагрузок
        self.setFixedWidth(self.bar_width)

        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Vertical bar
        bar = QtWidgets.QWidget(self)
        bar.setFixedWidth(self.bar_width)
        bar_lay = QtWidgets.QVBoxLayout(bar)
        bar_lay.setContentsMargins(0, 0, 0, 0)
        bar_lay.setSpacing(2)

        self.btn_truck = self._make_vertical_button(tr("Кузов"))
        self.btn_truck.clicked.connect(lambda: self._toggle_panel("truck"))
        bar_lay.addWidget(self.btn_truck)

        self.btn_boxes = self._make_vertical_button(tr("Коробки"))
        self.btn_boxes.clicked.connect(lambda: self._toggle_panel("boxes"))
        bar_lay.addWidget(self.btn_boxes)

        self.btn_loads = self._make_vertical_button(tr("Нагрузки"))
        self.btn_loads.clicked.connect(lambda: self._toggle_panel("loads"))
        bar_lay.addWidget(self.btn_loads)

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

        self.loads_panel = self._build_loads_panel()
        self.panel_container.addWidget(self.loads_panel)

    def _make_vertical_button(self, text: str) -> QtWidgets.QToolButton:
        btn = QtWidgets.QToolButton(self)
        btn.setText(text)
        btn.setCheckable(True)
        btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        btn.setMinimumHeight(60)  # Уменьшили высоту для размещения трех кнопок
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
                current_panel_width = self.panel_width
            elif panel_type == "boxes":
                self.panel_container.setCurrentWidget(self.boxes_panel)
                current_panel_width = self.panel_width
            elif panel_type == "loads":
                self.panel_container.setCurrentWidget(self.loads_panel)
                current_panel_width = self.loads_panel_width

            self.panel_container.setFixedWidth(current_panel_width)
            self.panel_container.show()
            self.setFixedWidth(self.bar_width + current_panel_width)
            self.active_panel = panel_type
            self._update_button_states()
            self.toggled.emit(True)

    def _update_button_states(self):
        """Обновить состояния кнопок"""
        self.btn_truck.setChecked(self.active_panel == "truck")
        self.btn_boxes.setChecked(self.active_panel == "boxes")
        self.btn_loads.setChecked(self.active_panel == "loads")

    def _build_truck_panel(self) -> QtWidgets.QWidget:
        """Панель настроек прицепа (существующая логика)"""
        w = QtWidgets.QWidget()
        w.setObjectName("TruckPanel")
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        # Panel title
        self.title = QtWidgets.QLabel()
        self.title.setObjectName("PanelTitle")
        self.title.setStyleSheet("""
            QLabel { 
                font-weight: bold; 
                font-size: 12px; 
                color: #2c3e50;
                padding: 4px;
                background-color: #ecf0f1;
                border-radius: 3px;
            }
        """)
        lay.addWidget(self.title)

        # Tent state section
        self.tent_btn = QtWidgets.QPushButton()
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
        self.btn_open = QtWidgets.QRadioButton()
        self.btn_close = QtWidgets.QRadioButton()
        self.btn_open.setChecked(True)
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
        self.btn_open.setStyleSheet(radio_style)
        self.btn_close.setStyleSheet(radio_style)
        v.addWidget(self.btn_open)
        v.addWidget(self.btn_close)
        self.btn_open.toggled.connect(lambda on: on and self._set_tent_alpha(0.0))
        self.btn_close.toggled.connect(lambda on: on and self._set_tent_alpha(0.3))
        lay.addWidget(self.tent_widget)

        # Presets section
        self.presets_btn = QtWidgets.QPushButton()
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
        self.custom_btn = QtWidgets.QPushButton()
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
            ed.setMaxLength(8)
            # Используем QDoubleValidator для поддержки дробных чисел
            ed.setValidator(QtGui.QDoubleValidator(0.1, 9999.0, 2, w))
            ed.setPlaceholderText(self.units_manager.get_distance_symbol())
            ed.setStyleSheet(input_style)
            ed.setFixedHeight(24)

        self.lbl_w = QtWidgets.QLabel()
        self.lbl_w.setStyleSheet(label_style)
        self.lbl_h = QtWidgets.QLabel()
        self.lbl_h.setStyleSheet(label_style)
        self.lbl_d = QtWidgets.QLabel()
        self.lbl_d.setStyleSheet(label_style)

        grid.addWidget(self.lbl_w, 0, 0);
        grid.addWidget(self.ed_w, 0, 1)
        grid.addWidget(self.lbl_h, 1, 0);
        grid.addWidget(self.ed_h, 1, 1)
        grid.addWidget(self.lbl_d, 2, 0);
        grid.addWidget(self.ed_d, 2, 1)

        self.btn_apply = QtWidgets.QPushButton()
        self.btn_apply.setStyleSheet("""
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
        grid.addWidget(self.btn_apply, 3, 0, 1, 2)
        self.btn_apply.clicked.connect(self._apply_custom)
        self.custom_widget.hide()
        lay.addWidget(self.custom_widget)

        # Reset
        self.btn_reset = QtWidgets.QPushButton()
        self.btn_reset.setStyleSheet("""
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
        self.btn_reset.clicked.connect(self._reset_defaults)
        lay.addWidget(self.btn_reset)

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

    def _build_loads_panel(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        w.setObjectName("LoadsPanel")

        self.load_calculation = LoadCalculationWidget(self.units_manager, self.get_app3d, w)

        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.load_calculation)

        return w

    def get_box_manager(self):
        if hasattr(self, 'box_management'):
            return self.box_management.get_box_manager()
        return None

    def _apply_custom(self):
        try:
            # Получаем значения в пользовательских единицах
            w_user = float(self.ed_w.text())
            h_user = float(self.ed_h.text())
            d_user = float(self.ed_d.text())
            
            # Конвертируем в внутренние единицы (см)
            w = int(self.units_manager.to_internal_distance(w_user))
            h = int(self.units_manager.to_internal_distance(h_user))
            d = int(self.units_manager.to_internal_distance(d_user))
        except Exception:
            return
        self._switch_truck(w, h, d)

    def _reset_defaults(self):
        self._set_tent_alpha(0.0)
        self._switch_truck(1650, 260, 245)

    def toggle_tent(self):
        if self.tent_btn.isChecked():
            self.tent_widget.show()
            self.tent_btn.setText(f"🎪 {tr('Состояние тента')} ▲")
        else:
            self.tent_widget.hide()
            self.tent_btn.setText(f"🎪 {tr('Состояние тента')} ▼")

    def toggle_presets(self):
        if self.presets_btn.isChecked():
            self.presets_widget.show()
            self.presets_btn.setText(f"📏 {tr('Размеры')} ▲")
        else:
            self.presets_widget.hide()
            self.presets_btn.setText(f"📏 {tr('Размеры')} ▼")

    def toggle_custom(self):
        if self.custom_btn.isChecked():
            self.custom_widget.show()
            self.custom_btn.setText(f"⚙️ {tr('Свой размер')} ▲")
        else:
            self.custom_widget.hide()
            self.custom_btn.setText(f"⚙️ {tr('Свой размер')} ▼")

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

    def _update_units_display(self):
        """Обновляет отображение единиц измерения в полях ввода"""
        if not self.units_manager:
            return
        
        symbol = self.units_manager.get_distance_symbol()

        for ed in (self.ed_w, self.ed_h, self.ed_d):
            ed.setPlaceholderText(symbol)

    def retranslate_ui(self):
        self.btn_truck.setText(tr("Кузов"))
        self.btn_boxes.setText(tr("Коробки"))
        self.btn_loads.setText(tr("Нагрузки"))
        
        if hasattr(self, 'title'):
            self.title.setText(tr("Настройки прицепа"))
        
        if hasattr(self, 'tent_btn'):
            expanded = "▲" if self.tent_btn.isChecked() else "▼"
            self.tent_btn.setText(f"🎪 {tr('Состояние тента')} {expanded}")
        
        if hasattr(self, 'btn_open'):
            self.btn_open.setText(tr("Открыт"))
        
        if hasattr(self, 'btn_close'):
            self.btn_close.setText(tr("Закрыт"))
        
        if hasattr(self, 'presets_btn'):
            expanded = "▲" if self.presets_btn.isChecked() else "▼"
            self.presets_btn.setText(f"📏 {tr('Размеры')} {expanded}")
        
        if hasattr(self, 'custom_btn'):
            expanded = "▲" if self.custom_btn.isChecked() else "▼"
            self.custom_btn.setText(f"⚙️ {tr('Свой размер')} {expanded}")
        
        if hasattr(self, 'lbl_w'):
            self.lbl_w.setText(tr("Длина"))
            self.lbl_h.setText(tr("Высота"))
            self.lbl_d.setText(tr("Ширина"))
        
        if hasattr(self, 'btn_apply'):
            self.btn_apply.setText(tr("Применить"))
        
        if hasattr(self, 'btn_reset'):
            self.btn_reset.setText(tr("Сбросить"))