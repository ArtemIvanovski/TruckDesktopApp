from PyQt5 import QtWidgets, QtCore, QtGui

from core.i18n import tr, TranslatableMixin


class GridWidget(QtWidgets.QWidget, TranslatableMixin):
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

        self.create_display_group(content_layout)
        self.create_appearance_group(content_layout)
        self.create_spacing_group(content_layout)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.create_buttons(layout)

    def create_display_group(self, layout):
        self.display_title_btn = QtWidgets.QPushButton()
        self.display_title_btn.setCheckable(False)
        self.display_title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.display_title_btn)

        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['grid_enabled'] = QtWidgets.QCheckBox()
        self.widgets['grid_enabled'].setStyleSheet(self.get_checkbox_style())

        self.grid_enabled_label = QtWidgets.QLabel()
        form.addRow(self.grid_enabled_label, self.widgets['grid_enabled'])

        layout.addWidget(content_widget)

    def create_appearance_group(self, layout):
        self.appearance_title_btn = QtWidgets.QPushButton()
        self.appearance_title_btn.setCheckable(False)
        self.appearance_title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.appearance_title_btn)

        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['grid_opacity'] = QtWidgets.QDoubleSpinBox()
        self.widgets['grid_opacity'].setRange(0.0, 1.0)
        self.widgets['grid_opacity'].setSingleStep(0.1)
        self.widgets['grid_opacity'].setDecimals(2)
        self.widgets['grid_opacity'].setMinimumWidth(120)
        self.widgets['grid_opacity'].setStyleSheet(self.get_spinbox_style())

        self.grid_color_btn = QtWidgets.QPushButton()
        self.grid_color_btn.setMinimumHeight(24)
        self.grid_color_btn.clicked.connect(self.choose_grid_color)

        self.grid_opacity_label = QtWidgets.QLabel()
        self.grid_color_label = QtWidgets.QLabel()
        form.addRow(self.grid_opacity_label, self.widgets['grid_opacity'])
        form.addRow(self.grid_color_label, self.grid_color_btn)

        layout.addWidget(content_widget)

    def create_spacing_group(self, layout):
        self.spacing_title_btn = QtWidgets.QPushButton()
        self.spacing_title_btn.setCheckable(False)
        self.spacing_title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.spacing_title_btn)

        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['grid_spacing_x_cm'] = QtWidgets.QSpinBox()
        self.widgets['grid_spacing_x_cm'].setRange(1, 100)
        self.widgets['grid_spacing_x_cm'].setSingleStep(1)
        self.widgets['grid_spacing_x_cm'].setMinimumWidth(120)
        self.widgets['grid_spacing_x_cm'].setStyleSheet(self.get_spinbox_style())

        self.widgets['grid_spacing_y_cm'] = QtWidgets.QSpinBox()
        self.widgets['grid_spacing_y_cm'].setRange(1, 100)
        self.widgets['grid_spacing_y_cm'].setSingleStep(1)
        self.widgets['grid_spacing_y_cm'].setMinimumWidth(120)
        self.widgets['grid_spacing_y_cm'].setStyleSheet(self.get_spinbox_style())

        self.grid_spacing_x_label = QtWidgets.QLabel()
        self.grid_spacing_y_label = QtWidgets.QLabel()
        form.addRow(self.grid_spacing_x_label, self.widgets['grid_spacing_x_cm'])
        form.addRow(self.grid_spacing_y_label, self.widgets['grid_spacing_y_cm'])

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

    def load_current_settings(self):
        if not self.graphics_manager:
            return

        settings = self.graphics_manager.get_graphics_settings()

        if 'grid_enabled' in self.widgets:
            self.widgets['grid_enabled'].setChecked(settings.grid_enabled)
        if 'grid_opacity' in self.widgets:
            self.widgets['grid_opacity'].setValue(settings.grid_opacity)
        if 'grid_spacing_x_cm' in self.widgets:
            self.widgets['grid_spacing_x_cm'].setValue(settings.grid_spacing_x_cm)
        if 'grid_spacing_y_cm' in self.widgets:
            self.widgets['grid_spacing_y_cm'].setValue(settings.grid_spacing_y_cm)

        self.update_grid_color_button(settings.grid_color)

    def update_grid_color_button(self, color):
        r, g, b = color
        hex_color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
        self.grid_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                border: 2px solid #888;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #0078d4;
            }}
        """)
        self.grid_color_btn.setText(f"RGB({int(r * 255)}, {int(g * 255)}, {int(b * 255)})")

    def choose_grid_color(self):
        if not self.graphics_manager:
            return

        settings = self.graphics_manager.get_graphics_settings()
        r, g, b = settings.grid_color
        current_color = QtGui.QColor(int(r * 255), int(g * 255), int(b * 255))

        color = QtWidgets.QColorDialog.getColor(current_color, self, tr("Выберите цвет сетки"))
        if color.isValid():
            new_color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            self.graphics_manager.update_graphics_settings(grid_color=new_color)
            self.update_grid_color_button(new_color)

    def apply_settings(self):
        if not self.graphics_manager:
            return

        settings_dict = {}

        for key, widget in self.widgets.items():
            if isinstance(widget, QtWidgets.QCheckBox):
                settings_dict[key] = widget.isChecked()
            elif isinstance(widget, (QtWidgets.QDoubleSpinBox, QtWidgets.QSpinBox)):
                settings_dict[key] = widget.value()

        self.graphics_manager.update_graphics_settings(**settings_dict)

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle(tr("Настройки"))
        msg.setText(tr("Настройки сетки применены успешно!"))
        msg.exec_()

    def reset_settings(self):
        reply = QtWidgets.QMessageBox.question(
            self, tr('Сброс настроек'),
            tr('Вы уверены, что хотите сбросить все настройки сетки до заводских?'),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            if self.graphics_manager:
                self.graphics_manager.reset_grid_settings()
                self.load_current_settings()

                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Information)
                msg.setWindowTitle(tr("Настройки"))
                msg.setText(tr("Настройки сетки сброшены до заводских!"))
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

    def get_spinbox_style(self):
        return """
            QSpinBox, QDoubleSpinBox {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                font-size: 11px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #3498db;
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

    def retranslate_ui(self):
        self.display_title_btn.setText(f"📊 {tr('Отображение сетки')}")
        self.grid_enabled_label.setText(f"{tr('Включить сетку')}:")

        self.appearance_title_btn.setText(f"🎨 {tr('Внешний вид')}")
        self.grid_opacity_label.setText(f"{tr('Прозрачность')}:")
        self.grid_color_label.setText(f"{tr('Цвет сетки')}:")

        self.spacing_title_btn.setText(f"📏 {tr('Размеры ячеек')}")
        self.grid_spacing_x_label.setText(f"{tr('Размер по X (см)')}:")
        self.grid_spacing_y_label.setText(f"{tr('Размер по Y (см)')}:")

        self.reset_btn.setText(tr("Сбросить"))
        self.apply_btn.setText(tr("Применить"))
