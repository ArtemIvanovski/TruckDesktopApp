from PyQt5 import QtWidgets, QtCore
from core.i18n import tr, TranslatableMixin


class TruckSettingsWidget(QtWidgets.QWidget, TranslatableMixin):
    def __init__(self, truck_manager, parent=None):
        super().__init__(parent)
        self.truck_manager = truck_manager
        self._setup_ui()
        self._wire()
        if self.truck_manager:
            self.truck_manager.add_on_changed(self._refresh)
        self._refresh()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.display_section = self._create_display_section()
        layout.addWidget(self.display_section)

        self.title = QtWidgets.QLabel()
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
        layout.addWidget(self.title)

        self.ready_section = self._create_ready_section()
        layout.addWidget(self.ready_section)

        self.info_section = self._create_info_section()
        layout.addWidget(self.info_section)

        layout.addStretch(1)

    def _create_display_section(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.display_btn = QtWidgets.QPushButton()
        self.display_btn.setCheckable(True)
        self.display_btn.setChecked(False)
        self.display_btn.clicked.connect(self.toggle_display)
        self.display_btn.setStyleSheet("""
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
        layout.addWidget(self.display_btn)

        self.display_widget = QtWidgets.QWidget()
        display_layout = QtWidgets.QHBoxLayout(self.display_widget)
        display_layout.setContentsMargins(8, 4, 8, 8)
        display_layout.setSpacing(6)

        self.display_label = QtWidgets.QLabel()
        self.display_checkbox = QtWidgets.QCheckBox()
        self.display_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11px;
                color: #2c3e50;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
        """)

        display_layout.addWidget(self.display_label)
        display_layout.addWidget(self.display_checkbox)
        display_layout.addStretch(1)
        layout.addWidget(self.display_widget)

        return widget

    def _create_ready_section(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.ready_btn = QtWidgets.QPushButton()
        self.ready_btn.setCheckable(True)
        self.ready_btn.setChecked(False)
        self.ready_btn.clicked.connect(self.toggle_ready)
        self.ready_btn.setStyleSheet("""
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
        layout.addWidget(self.ready_btn)

        self.ready_widget = QtWidgets.QWidget()
        ready_layout = QtWidgets.QVBoxLayout(self.ready_widget)
        ready_layout.setContentsMargins(8, 4, 8, 8)
        ready_layout.setSpacing(6)

        self.ready_yes = QtWidgets.QRadioButton()
        self.ready_no = QtWidgets.QRadioButton()
        self.ready_no.setChecked(True)

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
        self.ready_yes.setStyleSheet(radio_style)
        self.ready_no.setStyleSheet(radio_style)

        ready_layout.addWidget(self.ready_yes)
        ready_layout.addWidget(self.ready_no)
        layout.addWidget(self.ready_widget)

        return widget

    def _create_info_section(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.info_btn = QtWidgets.QPushButton()
        self.info_btn.setCheckable(True)
        self.info_btn.setChecked(False)
        self.info_btn.clicked.connect(self.toggle_info)
        self.info_btn.setStyleSheet("""
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
        layout.addWidget(self.info_btn)

        self.info_widget = QtWidgets.QWidget()
        info_layout = QtWidgets.QGridLayout(self.info_widget)
        info_layout.setContentsMargins(8, 4, 8, 8)
        info_layout.setSpacing(6)

        label_style = """
            QLabel {
                font-size: 11px;
                font-weight: 600;
                color: #2c3e50;
            }
        """

        value_style = """
            QLabel {
                font-size: 11px;
                color: #34495e;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 4px;
            }
        """

        self.boxes_label = QtWidgets.QLabel()
        self.boxes_label.setStyleSheet(label_style)
        self.boxes_value = QtWidgets.QLabel("0")
        self.boxes_value.setStyleSheet(value_style)

        self.weight_label = QtWidgets.QLabel()
        self.weight_label.setStyleSheet(label_style)
        self.weight_value = QtWidgets.QLabel("0.0")
        self.weight_value.setStyleSheet(value_style)

        info_layout.addWidget(self.boxes_label, 0, 0)
        info_layout.addWidget(self.boxes_value, 0, 1)
        info_layout.addWidget(self.weight_label, 1, 0)
        info_layout.addWidget(self.weight_value, 1, 1)

        layout.addWidget(self.info_widget)
        return widget

    def _wire(self):
        self.display_checkbox.toggled.connect(self._on_display_changed)
        self.ready_yes.toggled.connect(self._on_ready_changed)
        self.ready_no.toggled.connect(self._on_ready_changed)

    def _on_display_changed(self, checked):
        if not self.truck_manager:
            return
        self.truck_manager.set_overlay_current(checked)

    def _on_ready_changed(self):
        if not self.truck_manager:
            return
        ready = self.ready_yes.isChecked()
        self.truck_manager.set_ready_current(ready)

    def toggle_display(self):
        if self.display_btn.isChecked():
            self.display_widget.show()
            expanded = "▲"
        else:
            self.display_widget.hide()
            expanded = "▼"
        self.display_btn.setText(f"📺 {tr('Отображение')} {expanded}")

    def toggle_ready(self):
        if self.ready_btn.isChecked():
            self.ready_widget.show()
            expanded = "▲"
        else:
            self.ready_widget.hide()
            expanded = "▼"
        self.ready_btn.setText(f"✅ {tr('Готовность к погрузке')} {expanded}")

    def toggle_info(self):
        if self.info_btn.isChecked():
            self.info_widget.show()
            expanded = "▲"
        else:
            self.info_widget.hide()
            expanded = "▼"
        self.info_btn.setText(f"📊 {tr('Информация')} {expanded}")

    def _refresh(self):
        if not self.truck_manager:
            return
        
        current = self.truck_manager.get_current()
        self.display_checkbox.setChecked(current.show_overlay)
        
        if current.ready:
            self.ready_yes.setChecked(True)
        else:
            self.ready_no.setChecked(True)
        
        boxes_count = len(current.boxes or [])
        self.boxes_value.setText(str(boxes_count))
        self.weight_value.setText("0.0")
        
        # Устанавливаем начальное состояние секций
        if not self.display_btn.isChecked():
            self.display_btn.setChecked(True)
            self.toggle_display()
        
        if not self.ready_btn.isChecked():
            self.ready_btn.setChecked(True)
            self.toggle_ready()
        
        if not self.info_btn.isChecked():
            self.info_btn.setChecked(True)
            self.toggle_info()
        
        self.retranslate_ui()

    def retranslate_ui(self):
        if not self.truck_manager:
            self.title.setText(tr("Настройки грузовика"))
            self.display_label.setText(tr("Отображать на главном экране") + ":")
            self.ready_yes.setText(tr("Готов к погрузке"))
            self.ready_no.setText(tr("Не готов"))
            self.boxes_label.setText(tr("Количество коробок") + ":")
            self.weight_label.setText(tr("Общий вес") + ":")
        else:
            current = self.truck_manager.get_current()
            self.title.setText(f"{tr('Настройки')}: {current.name}")
            
            self.display_label.setText(tr("Отображать на главном экране") + ":")
            
            self.ready_yes.setText(tr("Готов к погрузке"))
            self.ready_no.setText(tr("Не готов"))
            
            self.boxes_label.setText(tr("Количество коробок") + ":")
            self.weight_label.setText(tr("Общий вес") + ":")
        
        self.toggle_display()
        self.toggle_ready()
        self.toggle_info()
