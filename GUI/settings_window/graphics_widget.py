from PyQt5 import QtWidgets, QtCore, QtGui

from graphics.graphics_settings import get_lighting_presets
from core.i18n import tr, TranslatableMixin


class GraphicsWidget(QtWidgets.QWidget, TranslatableMixin):
    def __init__(self, graphics_manager, parent=None):
        super().__init__(parent)
        self.graphics_manager = graphics_manager
        self.widgets = {}
        self.setup_ui()
        self.load_current_settings()
        self.retranslate_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setSpacing(8)

        self.create_lighting_group(content_layout)
        self.create_materials_group(content_layout)
        self.create_colors_group(content_layout)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.create_buttons(layout)

    def create_lighting_group(self, layout):
        self.lighting_title_btn = QtWidgets.QPushButton()
        self.lighting_title_btn.setCheckable(False)
        self.lighting_title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.lighting_title_btn)

        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['lighting_enabled'] = QtWidgets.QCheckBox()
        self.widgets['lighting_enabled'].setStyleSheet(self.get_checkbox_style())

        self.lighting_mode_combo = QtWidgets.QComboBox()
        self.lighting_mode_combo.setMinimumWidth(180)
        self.lighting_mode_combo.setStyleSheet(self.get_combobox_style())
        self.update_lighting_combo()

        self.lighting_enabled_label = QtWidgets.QLabel()
        self.lighting_mode_label = QtWidgets.QLabel()
        form.addRow(self.lighting_enabled_label, self.widgets['lighting_enabled'])
        form.addRow(self.lighting_mode_label, self.lighting_mode_combo)

        layout.addWidget(content_widget)

    def create_materials_group(self, layout):
        self.materials_title_btn = QtWidgets.QPushButton()
        self.materials_title_btn.setCheckable(False)
        self.materials_title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.materials_title_btn)

        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['enable_specular'] = QtWidgets.QCheckBox()
        self.widgets['enable_specular'].setStyleSheet(self.get_checkbox_style())

        self.enable_specular_label = QtWidgets.QLabel()
        form.addRow(self.enable_specular_label, self.widgets['enable_specular'])

        layout.addWidget(content_widget)

    def create_colors_group(self, layout):
        self.colors_title_btn = QtWidgets.QPushButton()
        self.colors_title_btn.setCheckable(False)
        self.colors_title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.colors_title_btn)

        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.background_color_btn = QtWidgets.QPushButton()
        self.background_color_btn.setMinimumHeight(24)
        self.background_color_btn.clicked.connect(self.choose_background_color)
        self.background_color_label = QtWidgets.QLabel()
        form.addRow(self.background_color_label, self.background_color_btn)

        self.truck_color_btn = QtWidgets.QPushButton()
        self.truck_color_btn.setMinimumHeight(24)
        self.truck_color_btn.clicked.connect(self.choose_truck_color)
        self.truck_color_label = QtWidgets.QLabel()
        form.addRow(self.truck_color_label, self.truck_color_btn)

        layout.addWidget(content_widget)

    def create_buttons(self, layout):
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.addStretch()

        self.reset_btn = QtWidgets.QPushButton()
        self.reset_btn.setStyleSheet(self.get_reset_button_style())
        self.reset_btn.setMinimumWidth(80)
        self.reset_btn.clicked.connect(self.reset_settings)

        self.apply_btn = QtWidgets.QPushButton()
        self.apply_btn.setStyleSheet(self.get_apply_button_style())
        self.apply_btn.setMinimumWidth(80)
        self.apply_btn.clicked.connect(self.apply_settings)

        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.apply_btn)
        layout.addLayout(button_layout)

    def create_spin_box(self, min_val, max_val, step, decimals):
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(step)
        spin.setDecimals(decimals)
        spin.setMinimumWidth(120)
        spin.setStyleSheet(self.get_spinbox_style())
        return spin

    def load_current_settings(self):
        if not self.graphics_manager:
            return

        settings = self.graphics_manager.get_graphics_settings()

        # Загружаем значения в виджеты
        if 'lighting_enabled' in self.widgets:
            self.widgets['lighting_enabled'].setChecked(settings.lighting_enabled)
        if 'main_light_intensity' in self.widgets:
            self.widgets['main_light_intensity'].setValue(settings.main_light_intensity)
        if 'fill_light_intensity' in self.widgets:
            self.widgets['fill_light_intensity'].setValue(settings.fill_light_intensity)
        if 'enable_specular' in self.widgets:
            self.widgets['enable_specular'].setChecked(settings.enable_specular)

        # Обновляем цвета кнопок
        self.update_background_color_button(settings.background_color)
        self.update_truck_color_button(settings.truck_color)

    def update_background_color_button(self, color):
        r, g, b = color
        hex_color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        self.background_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                border: 2px solid #888;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #0078d4;
            }}
        """)
        self.background_color_btn.setText(f"RGB({int(r * 255)}, {int(g * 255)}, {int(b * 255)})")

    def update_truck_color_button(self, color):
        r, g, b = color
        hex_color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        self.truck_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                border: 2px solid #888;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #0078d4;
            }}
        """)
        self.truck_color_btn.setText(f"RGB({int(r * 255)}, {int(g * 255)}, {int(b * 255)})")

    def choose_background_color(self):
        if not self.graphics_manager:
            return

        settings = self.graphics_manager.get_graphics_settings()
        r, g, b = settings.background_color
        current_color = QtGui.QColor(int(r * 255), int(g * 255), int(b * 255))

        color = QtWidgets.QColorDialog.getColor(current_color, self, tr("Выберите цвет фона"))
        if color.isValid():
            new_color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            self.graphics_manager.update_graphics_settings(background_color=new_color)
            self.update_background_color_button(new_color)

    def choose_truck_color(self):
        if not self.graphics_manager:
            return

        settings = self.graphics_manager.get_graphics_settings()
        r, g, b = settings.truck_color
        current_color = QtGui.QColor(int(r * 255), int(g * 255), int(b * 255))

        color = QtWidgets.QColorDialog.getColor(current_color, self, tr("Выберите цвет тягача"))
        if color.isValid():
            new_color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            self.graphics_manager.update_graphics_settings(truck_color=new_color)
            self.update_truck_color_button(new_color)

    def apply_settings(self):
        if not self.graphics_manager:
            return

        settings_dict = {}

        for key, widget in self.widgets.items():
            if isinstance(widget, QtWidgets.QCheckBox):
                settings_dict[key] = widget.isChecked()
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                settings_dict[key] = widget.value()

        if hasattr(self, 'lighting_mode_combo'):
            selected_mode = self.lighting_mode_combo.currentData()
            if selected_mode:
                self.graphics_manager.set_lighting_mode(selected_mode)

        self.graphics_manager.update_graphics_settings(**settings_dict)

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle(tr("Настройки"))
        msg.setText(tr("Настройки графики применены успешно!"))
        msg.exec_()

    def reset_settings(self):
        reply = QtWidgets.QMessageBox.question(
            self, tr('Сброс настроек'),
            tr('Вы уверены, что хотите сбросить все настройки графики до заводских?'),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            if self.graphics_manager:
                self.graphics_manager.reset_graphics_settings()
                self.load_current_settings()

                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Information)
                msg.setWindowTitle(tr("Настройки"))
                msg.setText(tr("Настройки графики сброшены до заводских!"))
                msg.exec_()

    def get_section_title_style(self):
        return """
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
        """

    def get_combobox_style(self):
        return """
            QComboBox {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                font-size: 11px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
            }
        """

    def get_checkbox_style(self):
        return """
            QCheckBox {
                font-size: 11px;
                font-weight: 500;
                color: #2c3e50;
                spacing: 6px;
                padding: 2px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 7px;
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
        """

    def get_apply_button_style(self):
        return """
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
        """

    def get_reset_button_style(self):
        return """
            QPushButton {
                font-size: 11px;
                color: #2c3e50;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
            }
        """
    
    def update_lighting_combo(self):
        """Обновить комбобокс режимов освещения с переводами"""
        current_mode = self.lighting_mode_combo.currentData()
        self.lighting_mode_combo.clear()
        
        for mode, preset in get_lighting_presets().items():
            self.lighting_mode_combo.addItem(preset["name"], mode)
        
        # Восстанавливаем выбранный режим
        if current_mode:
            index = self.lighting_mode_combo.findData(current_mode)
            if index >= 0:
                self.lighting_mode_combo.setCurrentIndex(index)
    
    def retranslate_ui(self):
        self.lighting_title_btn.setText(f"💡 {tr('Освещение')}")
        self.lighting_enabled_label.setText(f"{tr('Включить освещение')}:")
        self.lighting_mode_label.setText(f"{tr('Режим освещения')}:")
        
        self.materials_title_btn.setText(f"🎨 {tr('Материалы')}")
        self.enable_specular_label.setText(f"{tr('Включить блики')}:")
        
        self.colors_title_btn.setText(f"🌈 {tr('Цвета')}")
        self.background_color_label.setText(tr("Цвет фона:"))
        self.truck_color_label.setText(tr("Цвет тягача:"))
        
        self.reset_btn.setText(tr("Сбросить"))
        self.apply_btn.setText(tr("Применить"))
        
        # Обновляем комбобокс с режимами освещения
        self.update_lighting_combo()
