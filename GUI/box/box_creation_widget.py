import random

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal

from core.box.box import Box
from core.i18n import tr, TranslatableMixin


class BoxCreationWidget(QtWidgets.QWidget, TranslatableMixin):
    box_created = pyqtSignal(Box)

    def __init__(self, units_manager, parent=None):
        super().__init__(parent)
        self.units_manager = units_manager
        self.setup_ui()
        units_manager.units_changed.connect(self.update_units)
        self.retranslate_ui()

    def update_units(self):
        distance_symbol = self.units_manager.get_distance_symbol()
        weight_symbol = self.units_manager.get_weight_symbol()

        self.width_input.setValue(self.units_manager.from_internal_distance(100))
        self.height_input.setValue(self.units_manager.from_internal_distance(60))
        self.depth_input.setValue(self.units_manager.from_internal_distance(80))
        self.weight_input.setValue(self.units_manager.from_internal_weight(5.0))

        # Обновляем метки
        form_layout = self.findChild(QtWidgets.QGridLayout)
        if form_layout:
            for i in range(form_layout.rowCount()):
                item = form_layout.itemAtPosition(i, 0)
                if item and item.widget():
                    label = item.widget()
                    if isinstance(label, QtWidgets.QLabel):
                        text = label.text()
                        if tr("Длина") in text:
                            label.setText(f"{tr('Длина')} ({distance_symbol}):")
                        elif tr("Ширина") in text:
                            label.setText(f"{tr('Ширина')} ({distance_symbol}):")
                        elif tr("Высота") in text:
                            label.setText(f"{tr('Высота')} ({distance_symbol}):")
                        elif tr("Вес") in text:
                            label.setText(f"{tr('Вес')} ({weight_symbol}):")

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

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

        self.basic_btn = QtWidgets.QPushButton()
        self.basic_btn.setCheckable(True)
        self.basic_btn.setChecked(True)
        self.basic_btn.clicked.connect(self.toggle_basic)
        self.basic_btn.setStyleSheet("""
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
        layout.addWidget(self.basic_btn)

        self.basic_widget = QtWidgets.QWidget()
        form = QtWidgets.QGridLayout(self.basic_widget)
        form.setContentsMargins(8, 4, 8, 8)
        form.setSpacing(6)

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

        distance_symbol = self.units_manager.get_distance_symbol()
        weight_symbol = self.units_manager.get_weight_symbol()

        self.length_label = QtWidgets.QLabel()
        form.addWidget(self.length_label, 0, 0)
        self.width_input = QtWidgets.QDoubleSpinBox()
        self.width_input.setRange(0.1, 999.9)
        self.width_input.setDecimals(1)
        self.width_input.setValue(self.units_manager.from_internal_distance(100))
        self.width_input.setStyleSheet(input_style)
        form.addWidget(self.width_input, 0, 1)

        self.width_label = QtWidgets.QLabel()
        form.addWidget(self.width_label, 1, 0)
        self.depth_input = QtWidgets.QDoubleSpinBox()
        self.depth_input.setRange(0.1, 999.9)
        self.depth_input.setDecimals(1)
        self.depth_input.setValue(self.units_manager.from_internal_distance(80))
        self.depth_input.setStyleSheet(input_style)
        form.addWidget(self.depth_input, 1, 1)

        self.height_label = QtWidgets.QLabel()
        form.addWidget(self.height_label, 2, 0)
        self.height_input = QtWidgets.QDoubleSpinBox()
        self.height_input.setRange(0.1, 999.9)
        self.height_input.setDecimals(1)
        self.height_input.setValue(self.units_manager.from_internal_distance(60))
        self.height_input.setStyleSheet(input_style)
        form.addWidget(self.height_input, 2, 1)

        self.marking_label = QtWidgets.QLabel()
        form.addWidget(self.marking_label, 3, 0)
        self.label_input = QtWidgets.QLineEdit()
        self.label_input.setPlaceholderText("PO#1234")
        self.label_input.setStyleSheet(input_style)
        form.addWidget(self.label_input, 3, 1)

        self.weight_label = QtWidgets.QLabel()
        form.addWidget(self.weight_label, 4, 0)
        self.weight_input = QtWidgets.QDoubleSpinBox()
        self.weight_input.setRange(0.1, 999.9)
        self.weight_input.setValue(self.units_manager.from_internal_weight(5.0))
        self.weight_input.setDecimals(1)
        self.weight_input.setStyleSheet(input_style)
        form.addWidget(self.weight_input, 4, 1)

        self.quantity_label = QtWidgets.QLabel()
        form.addWidget(self.quantity_label, 5, 0)
        self.quantity_input = QtWidgets.QSpinBox()
        self.quantity_input.setRange(1, 999)
        self.quantity_input.setValue(1)
        self.quantity_input.setStyleSheet(input_style)
        form.addWidget(self.quantity_input, 5, 1)

        layout.addWidget(self.basic_widget)

        self.advanced_btn = QtWidgets.QPushButton()
        self.advanced_btn.setCheckable(True)
        self.advanced_btn.clicked.connect(self.toggle_advanced)
        layout.addWidget(self.advanced_btn)

        self.advanced_widget = QtWidgets.QWidget()
        advanced_layout = QtWidgets.QVBoxLayout(self.advanced_widget)
        advanced_layout.setSpacing(4)

        info_layout = QtWidgets.QHBoxLayout()
        self.info_label = QtWidgets.QLabel()
        info_layout.addWidget(self.info_label)
        self.info_input = QtWidgets.QLineEdit()
        # Placeholder будет установлен в retranslate_ui
        self.info_input.setStyleSheet(input_style)
        info_layout.addWidget(self.info_input)
        advanced_layout.addLayout(info_layout)

        self.markings_group = QtWidgets.QGroupBox()
        self.markings_group.setStyleSheet("QGroupBox { font-size: 10px; }")
        markings_grid = QtWidgets.QGridLayout(self.markings_group)
        markings_grid.setSpacing(2)

        self.marking_checkboxes = {}
        row, col = 0, 0
        for key, info in Box.CARGO_MARKINGS.items():
            checkbox = QtWidgets.QCheckBox(f"{info['icon']}")
            checkbox.setToolTip(info['name'])
            checkbox.setStyleSheet("font-size: 12px;")
            self.marking_checkboxes[key] = checkbox
            markings_grid.addWidget(checkbox, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        advanced_layout.addWidget(self.markings_group)
        self.advanced_widget.hide()
        layout.addWidget(self.advanced_widget)

        self.add_button = QtWidgets.QPushButton()
        self.add_button.setStyleSheet("""
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
        self.add_button.clicked.connect(self.create_box)
        layout.addWidget(self.add_button)

        self.clear_button = QtWidgets.QPushButton()
        self.clear_button.setStyleSheet("""
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
        self.clear_button.clicked.connect(self.clear_form)
        layout.addWidget(self.clear_button)

    def toggle_basic(self):
        if self.basic_btn.isChecked():
            self.basic_widget.show()
            self.basic_btn.setText(f"📋 {tr('Основные параметры')} ▲")
        else:
            self.basic_widget.hide()
            self.basic_btn.setText(f"📋 {tr('Основные параметры')} ▼")

    def create_box(self):
        try:
            width_internal = self.units_manager.to_internal_distance(self.width_input.value())
            height_internal = self.units_manager.to_internal_distance(self.height_input.value())
            depth_internal = self.units_manager.to_internal_distance(self.depth_input.value())
            weight_internal = self.units_manager.to_internal_weight(self.weight_input.value())

            label = self.label_input.text().strip()
            quantity = self.quantity_input.value()
            additional_info = self.info_input.text().strip()

            selected_markings = []
            for key, checkbox in self.marking_checkboxes.items():
                if checkbox.isChecked():
                    selected_markings.append(key)

            if not label:
                label = f"PO#{random.randint(1000, 9999)}"

            box = Box(
                width=width_internal, height=height_internal, depth=depth_internal,
                label=label, weight=weight_internal, quantity=quantity,
                additional_info=additional_info,
                cargo_markings=selected_markings
            )

            box.color = None

            print(f"[BoxCreation] Created box {box.label} without individual color (will be determined by size)")

            self.box_created.emit(box)

            if label.startswith("PO#"):
                try:
                    num = int(label[3:]) + 1
                    self.label_input.setText(f"PO#{num}")
                except ValueError:
                    pass

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, tr("Ошибка"), tr("Не удалось создать коробку: {error}").format(error=e))

    def clear_form(self):
        self.width_input.setValue(self.units_manager.from_internal_distance(100))
        self.height_input.setValue(self.units_manager.from_internal_distance(60))
        self.depth_input.setValue(self.units_manager.from_internal_distance(80))
        self.label_input.clear()
        self.weight_input.setValue(self.units_manager.from_internal_weight(5.0))
        self.quantity_input.setValue(1)
        self.info_input.clear()
        for checkbox in self.marking_checkboxes.values():
            checkbox.setChecked(False)

    def toggle_advanced(self):
        if self.advanced_btn.isChecked():
            self.advanced_widget.show()
            self.advanced_btn.setText(f"⚙️ {tr('Дополнительно')} ▲")
        else:
            self.advanced_widget.hide()
            self.advanced_btn.setText(f"⚙️ {tr('Дополнительно')} ▼")

    def retranslate_ui(self):
        distance_symbol = self.units_manager.get_distance_symbol()
        weight_symbol = self.units_manager.get_weight_symbol()

        self.title.setText(tr("Добавить коробки"))

        # Обновляем метки
        self.length_label.setText(f"{tr('Длина')} ({distance_symbol}):")
        self.width_label.setText(f"{tr('Ширина')} ({distance_symbol}):")
        self.height_label.setText(f"{tr('Высота')} ({distance_symbol}):")
        self.marking_label.setText(f"{tr('Маркировка')}:")
        self.weight_label.setText(f"{tr('Вес')} ({weight_symbol}):")
        self.quantity_label.setText(f"{tr('Количество')}:")

        # Обновляем кнопки
        if self.basic_btn.isChecked():
            self.basic_btn.setText(f"📋 {tr('Основные параметры')} ▲")
        else:
            self.basic_btn.setText(f"📋 {tr('Основные параметры')} ▼")

        if self.advanced_btn.isChecked():
            self.advanced_btn.setText(f"⚙️ {tr('Дополнительно')} ▲")
        else:
            self.advanced_btn.setText(f"⚙️ {tr('Дополнительно')} ▼")

        self.info_label.setText(f"{tr('Информация')}:")
        self.info_input.setPlaceholderText(tr("Дополнительная информация..."))
        self.markings_group.setTitle(f"🏷️ {tr('Маркировки груза')}")

        self.add_button.setText(tr("Добавить"))
        self.clear_button.setText(tr("Очистить"))
