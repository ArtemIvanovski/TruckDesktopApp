from PyQt5 import QtWidgets, QtCore, QtGui

from graphics_settings import LIGHTING_PRESETS


class CameraControlWidget(QtWidgets.QWidget):
    def __init__(self, camera, parent=None):
        super().__init__(parent)
        self.camera = camera
        self.widgets = {}
        self.setup_ui()
        self.load_current_settings()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setSpacing(25)

        self.create_sensitivity_group(content_layout)
        self.create_inertia_group(content_layout)
        self.create_limits_group(content_layout)
        self.create_inversion_group(content_layout)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.create_buttons(layout)

    def create_sensitivity_group(self, layout):
        group = QtWidgets.QGroupBox("Чувствительность")
        group.setStyleSheet(self.get_group_style())
        form = QtWidgets.QFormLayout(group)
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['rotation_sensitivity'] = self.create_spin_box(0.1, 10.0, 0.1, 2)
        self.widgets['pan_sensitivity'] = self.create_spin_box(0.1, 5.0, 0.1, 2)
        self.widgets['zoom_sensitivity'] = self.create_spin_box(0.001, 0.1, 0.001, 3)

        form.addRow("Вращение:", self.widgets['rotation_sensitivity'])
        form.addRow("Панорамирование:", self.widgets['pan_sensitivity'])
        form.addRow("Масштабирование:", self.widgets['zoom_sensitivity'])

        layout.addWidget(group)

    def create_inertia_group(self, layout):
        group = QtWidgets.QGroupBox("Инерция")
        group.setStyleSheet(self.get_group_style())
        form = QtWidgets.QFormLayout(group)
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['enable_inertia'] = QtWidgets.QCheckBox()
        self.widgets['enable_inertia'].setStyleSheet(self.get_checkbox_style())

        self.widgets['damping'] = self.create_spin_box(0.1, 1.0, 0.01, 2)
        self.widgets['min_velocity'] = self.create_spin_box(0.0001, 0.01, 0.0001, 4)

        form.addRow("Включить инерцию:", self.widgets['enable_inertia'])
        form.addRow("Затухание:", self.widgets['damping'])
        form.addRow("Минимальная скорость:", self.widgets['min_velocity'])

        layout.addWidget(group)

    def create_limits_group(self, layout):
        group = QtWidgets.QGroupBox("Ограничения")
        group.setStyleSheet(self.get_group_style())
        form = QtWidgets.QFormLayout(group)
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['min_radius'] = self.create_spin_box(10, 1000, 10, 0)
        self.widgets['max_radius'] = self.create_spin_box(1000, 10000, 100, 0)
        self.widgets['max_beta'] = self.create_spin_box(0.1, 3.14, 0.01, 4)

        form.addRow("Минимальный радиус:", self.widgets['min_radius'])
        form.addRow("Максимальный радиус:", self.widgets['max_radius'])
        form.addRow("Максимальный угол Beta:", self.widgets['max_beta'])

        layout.addWidget(group)

    def create_inversion_group(self, layout):
        group = QtWidgets.QGroupBox("Инверсия осей")
        group.setStyleSheet(self.get_group_style())
        form = QtWidgets.QFormLayout(group)
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        checkboxes = [
            ('invert_rotation_x', "Инвертировать вращение по X"),
            ('invert_rotation_y', "Инвертировать вращение по Y"),
            ('invert_pan_x', "Инвертировать панорамирование по X"),
            ('invert_pan_y', "Инвертировать панорамирование по Y")
        ]

        for key, label in checkboxes:
            self.widgets[key] = QtWidgets.QCheckBox()
            self.widgets[key].setStyleSheet(self.get_checkbox_style())
            form.addRow(label, self.widgets[key])

        layout.addWidget(group)

    def create_buttons(self, layout):
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        apply_btn = QtWidgets.QPushButton("Применить")
        apply_btn.setStyleSheet(self.get_button_style())
        apply_btn.setMinimumWidth(100)
        apply_btn.clicked.connect(self.apply_settings)

        reset_btn = QtWidgets.QPushButton("Сбросить")
        reset_btn.setStyleSheet(self.get_button_style())
        reset_btn.setMinimumWidth(100)
        reset_btn.clicked.connect(self.reset_settings)

        button_layout.addWidget(reset_btn)
        button_layout.addWidget(apply_btn)
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
        settings = self.camera.get_camera_settings()

        for key, widget in self.widgets.items():
            value = getattr(settings, key, None)
            if value is not None:
                if isinstance(widget, QtWidgets.QCheckBox):
                    widget.setChecked(value)
                elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                    widget.setValue(value)

    def apply_settings(self):
        settings_dict = {}

        for key, widget in self.widgets.items():
            if isinstance(widget, QtWidgets.QCheckBox):
                settings_dict[key] = widget.isChecked()
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                settings_dict[key] = widget.value()

        self.camera.update_camera_settings(**settings_dict)

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle("Настройки")
        msg.setText("Настройки камеры применены успешно!")
        msg.exec_()

    def reset_settings(self):
        reply = QtWidgets.QMessageBox.question(
            self, 'Сброс настроек',
            'Вы уверены, что хотите сбросить все настройки камеры до заводских?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self.camera.reset_camera_settings()
            self.load_current_settings()

            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setWindowTitle("Настройки")
            msg.setText("Настройки камеры сброшены до заводских!")
            msg.exec_()

    def get_group_style(self):
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }
        """

    def get_spinbox_style(self):
        return """
            QDoubleSpinBox {
                padding: 4px;
                border: 1px solid #c0c0c0;
                border-radius: 2px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #0078d4;
            }
        """

    def get_checkbox_style(self):
        return """
            QCheckBox {
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """

    def get_button_style(self):
        return """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #c0c0c0;
                border-radius: 2px;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """


class GraphicsWidget(QtWidgets.QWidget):
    def __init__(self, graphics_manager, parent=None):
        super().__init__(parent)
        self.graphics_manager = graphics_manager
        self.widgets = {}
        self.setup_ui()
        self.load_current_settings()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setSpacing(25)

        self.create_lighting_group(content_layout)
        self.create_materials_group(content_layout)
        self.create_colors_group(content_layout)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.create_buttons(layout)

    def create_lighting_group(self, layout):
        group = QtWidgets.QGroupBox("Освещение")
        group.setStyleSheet(self.get_group_style())
        form = QtWidgets.QFormLayout(group)
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['lighting_enabled'] = QtWidgets.QCheckBox()
        self.widgets['lighting_enabled'].setStyleSheet(self.get_checkbox_style())

        self.lighting_mode_combo = QtWidgets.QComboBox()
        self.lighting_mode_combo.setMinimumWidth(250)
        for mode, preset in LIGHTING_PRESETS.items():
            self.lighting_mode_combo.addItem(preset["name"], mode)

        form.addRow("Включить освещение:", self.widgets['lighting_enabled'])
        form.addRow("Режим освещения:", self.lighting_mode_combo)

        layout.addWidget(group)

    def create_materials_group(self, layout):
        group = QtWidgets.QGroupBox("Материалы")
        group.setStyleSheet(self.get_group_style())
        form = QtWidgets.QFormLayout(group)
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['enable_specular'] = QtWidgets.QCheckBox()
        self.widgets['enable_specular'].setStyleSheet(self.get_checkbox_style())

        form.addRow("Включить блики:", self.widgets['enable_specular'])

        layout.addWidget(group)

    def create_colors_group(self, layout):
        group = QtWidgets.QGroupBox("Цвета")
        group.setStyleSheet(self.get_group_style())
        form = QtWidgets.QFormLayout(group)
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        # Цвет фона
        self.background_color_btn = QtWidgets.QPushButton()
        self.background_color_btn.setMinimumHeight(30)
        self.background_color_btn.clicked.connect(self.choose_background_color)
        form.addRow("Цвет фона:", self.background_color_btn)

        # Цвет тягача
        self.truck_color_btn = QtWidgets.QPushButton()
        self.truck_color_btn.setMinimumHeight(30)
        self.truck_color_btn.clicked.connect(self.choose_truck_color)
        form.addRow("Цвет тягача:", self.truck_color_btn)

        layout.addWidget(group)

    def create_buttons(self, layout):
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        apply_btn = QtWidgets.QPushButton("Применить")
        apply_btn.setStyleSheet(self.get_button_style())
        apply_btn.setMinimumWidth(100)
        apply_btn.clicked.connect(self.apply_settings)

        reset_btn = QtWidgets.QPushButton("Сбросить")
        reset_btn.setStyleSheet(self.get_button_style())
        reset_btn.setMinimumWidth(100)
        reset_btn.clicked.connect(self.reset_settings)

        button_layout.addWidget(reset_btn)
        button_layout.addWidget(apply_btn)
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

        color = QtWidgets.QColorDialog.getColor(current_color, self, "Выберите цвет фона")
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

        color = QtWidgets.QColorDialog.getColor(current_color, self, "Выберите цвет тягача")
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

        # Обработка комбобокса режима освещения
        if hasattr(self, 'lighting_mode_combo'):
            selected_mode = self.lighting_mode_combo.currentData()
            if selected_mode:
                self.graphics_manager.set_lighting_mode(selected_mode)

        self.graphics_manager.update_graphics_settings(**settings_dict)

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle("Настройки")
        msg.setText("Настройки графики применены успешно!")
        msg.exec_()

    def reset_settings(self):
        reply = QtWidgets.QMessageBox.question(
            self, 'Сброс настроек',
            'Вы уверены, что хотите сбросить все настройки графики до заводских?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            if self.graphics_manager:
                self.graphics_manager.reset_graphics_settings()
                self.load_current_settings()

                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Information)
                msg.setWindowTitle("Настройки")
                msg.setText("Настройки графики сброшены до заводских!")
                msg.exec_()

    def get_group_style(self):
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }
        """

    def get_spinbox_style(self):
        return """
            QDoubleSpinBox {
                padding: 4px;
                border: 1px solid #c0c0c0;
                border-radius: 2px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #0078d4;
            }
        """

    def get_checkbox_style(self):
        return """
            QCheckBox {
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """

    def get_button_style(self):
        return """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #c0c0c0;
                border-radius: 2px;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """


class GeneralWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        group = QtWidgets.QGroupBox("Общие настройки")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }
        """)
        form = QtWidgets.QFormLayout(group)
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        autosave_cb = QtWidgets.QCheckBox()
        autosave_cb.setChecked(True)
        form.addRow("Автосохранение:", autosave_cb)

        backup_cb = QtWidgets.QCheckBox()
        backup_cb.setChecked(False)
        form.addRow("Создавать резервные копии:", backup_cb)

        language_combo = QtWidgets.QComboBox()
        language_combo.addItems(["Русский", "English"])
        language_combo.setCurrentText("Русский")
        language_combo.setMinimumWidth(120)
        form.addRow("Язык:", language_combo)

        layout.addWidget(group)
        layout.addStretch()


class SettingsWindow(QtWidgets.QDialog):
    def __init__(self, camera, graphics_manager=None, parent=None):
        super().__init__(parent)
        self.camera = camera
        self.graphics_manager = graphics_manager
        self.search_index = {}
        self.setWindowTitle("Настройки")
        self.setModal(True)
        self.resize(900, 700)
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.build_search_index()

    def setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        search_layout = QtWidgets.QHBoxLayout()
        search_layout.setContentsMargins(15, 15, 15, 10)

        search_label = QtWidgets.QLabel("Поиск:")
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Введите критерий поиска...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        self.search_edit.setMinimumWidth(300)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #c0c0c0;
                border-radius: 2px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        search_layout.addStretch()

        main_layout.addLayout(search_layout)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(separator)

        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.category_list = QtWidgets.QListWidget()
        self.category_list.setFixedWidth(200)
        self.category_list.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.category_list.setStyleSheet("""
            QListWidget {
                border-right: 1px solid #c0c0c0;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)

        self.categories = [
            "Управление",
            "Графика",
            "Общие"
        ]

        for category in self.categories:
            self.category_list.addItem(category)

        self.category_list.setCurrentRow(0)
        self.category_list.currentRowChanged.connect(self.on_category_changed)

        content_layout.addWidget(self.category_list)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        content_layout.addWidget(separator)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.title_label = QtWidgets.QLabel("Управление")
        self.title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            padding: 20px; 
            background-color: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
        """)
        right_layout.addWidget(self.title_label)

        self.content_stack = QtWidgets.QStackedWidget()

        camera_widget = CameraControlWidget(self.camera, self)
        graphics_widget = GraphicsWidget(self.graphics_manager, self)
        general_widget = GeneralWidget(self)

        self.content_stack.addWidget(camera_widget)
        self.content_stack.addWidget(graphics_widget)
        self.content_stack.addWidget(general_widget)

        right_layout.addWidget(self.content_stack)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setContentsMargins(20, 15, 20, 20)
        button_layout.addStretch()

        close_btn = QtWidgets.QPushButton("Закрыть")
        close_btn.setMinimumWidth(100)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #c0c0c0;
                border-radius: 2px;
                background-color: #f0f0f0;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        right_layout.addLayout(button_layout)

        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(right_layout)
        content_layout.addWidget(right_widget)

        main_layout.addLayout(content_layout)

    def build_search_index(self):
        self.search_index = {
            'вращение': 'Управление',
            'панорамирование': 'Управление',
            'масштабирование': 'Управление',
            'инерция': 'Управление',
            'затухание': 'Управление',
            'скорость': 'Управление',
            'радиус': 'Управление',
            'угол': 'Управление',
            'инверсия': 'Управление',
            'инвертировать': 'Управление',
            'ограничения': 'Управление',
            'чувствительность': 'Управление',
            'освещение': 'Графика',
            'свет': 'Графика',
            'интенсивность': 'Графика',
            'блики': 'Графика',
            'материалы': 'Графика',
            'цвет': 'Графика',
            'фон': 'Графика',
            'тягач': 'Графика',
            'автосохранение': 'Общие',
            'резервные': 'Общие',
            'копии': 'Общие',
            'язык': 'Общие',
            'backup': 'Общие'
        }

    def on_search_changed(self, text):
        if not text.strip():
            for i in range(self.category_list.count()):
                self.category_list.item(i).setHidden(False)
            return

        text = text.lower().strip()
        found_categories = set()

        for keyword, category in self.search_index.items():
            if text in keyword:
                found_categories.add(category)

        for i in range(self.category_list.count()):
            item = self.category_list.item(i)
            category_name = item.text()

            if category_name in found_categories or text in category_name.lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def on_category_changed(self, index):
        if 0 <= index < len(self.categories):
            self.title_label.setText(self.categories[index])
            self.content_stack.setCurrentIndex(index)


class UnitsWidget(QtWidgets.QWidget):
    def __init__(self, units_manager, parent=None):
        super().__init__(parent)
        self.units_manager = units_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        group = QtWidgets.QGroupBox("Единицы измерения")
        form = QtWidgets.QFormLayout(group)

        self.distance_combo = QtWidgets.QComboBox()
        for unit, info in self.units_manager.DISTANCE_UNITS.items():
            self.distance_combo.addItem(info['name'], unit)

        self.weight_combo = QtWidgets.QComboBox()
        for unit, info in self.units_manager.WEIGHT_UNITS.items():
            self.weight_combo.addItem(info['name'], unit)

        form.addRow("Расстояние:", self.distance_combo)
        form.addRow("Вес:", self.weight_combo)

        layout.addWidget(group)

        self.load_current_settings()

    def load_current_settings(self):
        pass

    def apply_settings(self):
        distance_unit = self.distance_combo.currentData()
        weight_unit = self.weight_combo.currentData()
        self.units_manager.set_units(distance_unit, weight_unit)
