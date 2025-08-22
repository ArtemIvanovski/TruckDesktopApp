from PyQt5 import QtWidgets, QtCore
from core.i18n import tr, TranslatableMixin


class CameraControlWidget(QtWidgets.QWidget, TranslatableMixin):
    def __init__(self, camera, parent=None):
        super().__init__(parent)
        self.camera = camera
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

        self.create_hotkeys_group(content_layout)
        self.create_sensitivity_group(content_layout)
        self.create_inertia_group(content_layout)
        self.create_limits_group(content_layout)
        self.create_inversion_group(content_layout)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.create_buttons(layout)

    def create_hotkeys_group(self, layout):
        # Заголовок секции для горячих клавиш
        self.hotkeys_title_btn = QtWidgets.QPushButton()
        self.hotkeys_title_btn.setCheckable(False)
        self.hotkeys_title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.hotkeys_title_btn)

        # Контент секции с информацией о горячих клавишах
        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(6)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        # Подзаголовок для управления камерой
        self.camera_title = QtWidgets.QLabel()
        self.camera_title.setStyleSheet("font-weight: bold; color: #2c3e50; margin-top: 5px;")
        form.addRow(self.camera_title)

        # Горячие клавиши для камеры
        self.left_mouse_label = QtWidgets.QLabel()
        self.left_mouse_desc = QtWidgets.QLabel()
        self.left_mouse_desc.setStyleSheet("color: #555; font-size: 10px;")
        form.addRow(self.left_mouse_label, self.left_mouse_desc)

        self.right_mouse_label = QtWidgets.QLabel()
        self.right_mouse_desc = QtWidgets.QLabel()
        self.right_mouse_desc.setStyleSheet("color: #555; font-size: 10px;")
        form.addRow(self.right_mouse_label, self.right_mouse_desc)

        self.mouse_wheel_label = QtWidgets.QLabel()
        self.mouse_wheel_desc = QtWidgets.QLabel()
        self.mouse_wheel_desc.setStyleSheet("color: #555; font-size: 10px;")
        form.addRow(self.mouse_wheel_label, self.mouse_wheel_desc)

        # Разделитель
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setStyleSheet("color: #ccc; margin: 5px 0;")
        form.addRow(separator)

        # Подзаголовок для работы с коробками
        self.boxes_title = QtWidgets.QLabel()
        self.boxes_title.setStyleSheet("font-weight: bold; color: #2c3e50; margin-top: 5px;")
        form.addRow(self.boxes_title)

        # Горячие клавиши для коробок
        self.rotate_key_label = QtWidgets.QLabel("R / К:")
        self.rotate_key_desc = QtWidgets.QLabel()
        self.rotate_key_desc.setStyleSheet("color: #555; font-size: 10px;")
        form.addRow(self.rotate_key_label, self.rotate_key_desc)

        self.wasd_key_label = QtWidgets.QLabel("W / A / S / D:")
        self.wasd_key_desc = QtWidgets.QLabel()
        self.wasd_key_desc.setStyleSheet("color: #555; font-size: 10px;")
        form.addRow(self.wasd_key_label, self.wasd_key_desc)

        self.delete_key_label = QtWidgets.QLabel("Backspace / Delete:")
        self.delete_key_desc = QtWidgets.QLabel()
        self.delete_key_desc.setStyleSheet("color: #555; font-size: 10px;")
        form.addRow(self.delete_key_label, self.delete_key_desc)

        self.hide_key_label = QtWidgets.QLabel("H / Р:")
        self.hide_key_desc = QtWidgets.QLabel()
        self.hide_key_desc.setStyleSheet("color: #555; font-size: 10px;")
        form.addRow(self.hide_key_label, self.hide_key_desc)

        layout.addWidget(content_widget)

    def create_sensitivity_group(self, layout):
        # Заголовок секции как в sidebar
        self.sensitivity_title_btn = QtWidgets.QPushButton()
        self.sensitivity_title_btn.setCheckable(False)
        self.sensitivity_title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.sensitivity_title_btn)

        # Контент секции
        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['rotation_sensitivity'] = self.create_spin_box(0.1, 10.0, 0.1, 2)
        self.widgets['pan_sensitivity'] = self.create_spin_box(0.1, 5.0, 0.1, 2)
        self.widgets['zoom_sensitivity'] = self.create_spin_box(0.001, 0.1, 0.001, 3)

        self.rotation_label = QtWidgets.QLabel()
        self.pan_label = QtWidgets.QLabel()
        self.zoom_label = QtWidgets.QLabel()
        
        form.addRow(self.rotation_label, self.widgets['rotation_sensitivity'])
        form.addRow(self.pan_label, self.widgets['pan_sensitivity'])
        form.addRow(self.zoom_label, self.widgets['zoom_sensitivity'])

        layout.addWidget(content_widget)

    def create_inertia_group(self, layout):
        # Заголовок секции как в sidebar
        self.inertia_title_btn = QtWidgets.QPushButton()
        self.inertia_title_btn.setCheckable(False)
        self.inertia_title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.inertia_title_btn)

        # Контент секции
        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['enable_inertia'] = QtWidgets.QCheckBox()
        self.widgets['enable_inertia'].setStyleSheet(self.get_checkbox_style())

        self.widgets['damping'] = self.create_spin_box(0.1, 1.0, 0.01, 2)
        self.widgets['min_velocity'] = self.create_spin_box(0.0001, 0.01, 0.0001, 4)

        self.enable_inertia_label = QtWidgets.QLabel()
        self.damping_label = QtWidgets.QLabel()
        self.min_velocity_label = QtWidgets.QLabel()
        
        form.addRow(self.enable_inertia_label, self.widgets['enable_inertia'])
        form.addRow(self.damping_label, self.widgets['damping'])
        form.addRow(self.min_velocity_label, self.widgets['min_velocity'])

        layout.addWidget(content_widget)

    def create_limits_group(self, layout):
        # Заголовок секции как в sidebar
        self.limits_title_btn = QtWidgets.QPushButton()
        self.limits_title_btn.setCheckable(False)
        self.limits_title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.limits_title_btn)

        # Контент секции
        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.widgets['min_radius'] = self.create_spin_box(10, 1000, 10, 0)
        self.widgets['max_radius'] = self.create_spin_box(1000, 10000, 100, 0)
        self.widgets['max_beta'] = self.create_spin_box(0.1, 3.14, 0.01, 4)

        self.min_radius_label = QtWidgets.QLabel()
        self.max_radius_label = QtWidgets.QLabel()
        self.max_beta_label = QtWidgets.QLabel()
        
        form.addRow(self.min_radius_label, self.widgets['min_radius'])
        form.addRow(self.max_radius_label, self.widgets['max_radius'])
        form.addRow(self.max_beta_label, self.widgets['max_beta'])

        layout.addWidget(content_widget)

    def create_inversion_group(self, layout):
        # Заголовок секции как в sidebar
        self.inversion_title_btn = QtWidgets.QPushButton()
        self.inversion_title_btn.setCheckable(False)
        self.inversion_title_btn.setStyleSheet(self.get_section_title_style())
        layout.addWidget(self.inversion_title_btn)

        # Контент секции
        content_widget = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(content_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        checkboxes = [
            ('invert_rotation_x', 'invert_rotation_x_label'),
            ('invert_rotation_y', 'invert_rotation_y_label'),
            ('invert_pan_x', 'invert_pan_x_label'),
            ('invert_pan_y', 'invert_pan_y_label')
        ]

        for key, label_attr in checkboxes:
            self.widgets[key] = QtWidgets.QCheckBox()
            self.widgets[key].setStyleSheet(self.get_checkbox_style())
            label_widget = QtWidgets.QLabel()
            setattr(self, label_attr, label_widget)
            form.addRow(label_widget, self.widgets[key])

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
        spin.setMinimumWidth(80)
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
        msg.setWindowTitle(tr("Настройки"))
        msg.setText(tr("Настройки камеры применены успешно!"))
        msg.exec_()

    def reset_settings(self):
        reply = QtWidgets.QMessageBox.question(
            self, tr('Сброс настроек'),
            tr('Вы уверены, что хотите сбросить все настройки камеры до заводских?'),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self.camera.reset_camera_settings()
            self.load_current_settings()

            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setWindowTitle(tr("Настройки"))
            msg.setText(tr("Настройки камеры сброшены до заводских!"))
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

    def get_spinbox_style(self):
        return """
            QDoubleSpinBox {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                font-size: 11px;
            }
            QDoubleSpinBox:focus {
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
    
    def retranslate_ui(self):
        # Горячие клавиши
        self.hotkeys_title_btn.setText(f"⌨️ {tr('Горячие клавиши')}")
        
        # Управление камерой
        if hasattr(self, 'camera_title'):
            self.camera_title.setText(f"{tr('Управление камерой:')}")
            self.left_mouse_label.setText(tr("Левая кнопка мыши"))
            self.left_mouse_desc.setText(tr("панорамирование (перемещение)"))
            self.right_mouse_label.setText(tr("Правая кнопка мыши"))
            self.right_mouse_desc.setText(tr("вращение камеры"))
            self.mouse_wheel_label.setText(tr("Колесо мыши"))
            self.mouse_wheel_desc.setText(tr("масштабирование (приближение/отдаление)"))
        
        # Работа с коробками
        if hasattr(self, 'boxes_title'):
            self.boxes_title.setText(f"{tr('Работа с коробками:')}")
            self.rotate_key_desc.setText(tr("повернуть коробку на 90 градусов"))
            self.wasd_key_desc.setText(tr("вращать коробку вокруг собственной оси"))
            self.delete_key_desc.setText(tr("полностью удалить коробку"))
            self.hide_key_desc.setText(tr("спрятать коробку (вернуть в список)"))
        
        self.sensitivity_title_btn.setText(f"🎯 {tr('Чувствительность')}")
        self.rotation_label.setText(f"{tr('Вращение')}:")
        self.pan_label.setText(f"{tr('Панорамирование')}:")
        self.zoom_label.setText(f"{tr('Масштабирование')}:")
        
        self.inertia_title_btn.setText(f"🔄 {tr('Инерция')}")
        self.enable_inertia_label.setText(f"{tr('Включить инерцию')}:")
        self.damping_label.setText(f"{tr('Затухание')}:")
        self.min_velocity_label.setText(f"{tr('Минимальная скорость')}:")
        
        self.limits_title_btn.setText(f"🚧 {tr('Ограничения')}")
        self.min_radius_label.setText(f"{tr('Минимальный радиус')}:")
        self.max_radius_label.setText(f"{tr('Максимальный радиус')}:")
        self.max_beta_label.setText(f"{tr('Максимальный угол Beta')}:")
        
        self.inversion_title_btn.setText(f"🔄 {tr('Инверсия осей')}")
        self.invert_rotation_x_label.setText(tr("Инвертировать вращение по X"))
        self.invert_rotation_y_label.setText(tr("Инвертировать вращение по Y"))
        self.invert_pan_x_label.setText(tr("Инвертировать панорамирование по X"))
        self.invert_pan_y_label.setText(tr("Инвертировать панорамирование по Y"))
        
        self.reset_btn.setText(tr("Сбросить"))
        self.apply_btn.setText(tr("Применить"))