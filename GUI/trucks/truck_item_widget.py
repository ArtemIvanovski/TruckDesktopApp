from PyQt5 import QtWidgets
from core.i18n import tr, TranslatableMixin


class TruckItemWidget(QtWidgets.QWidget, TranslatableMixin):
    def __init__(self, truck_manager, truck, index, parent=None):
        super().__init__(parent)
        self.truck_manager = truck_manager
        self.truck = truck
        self.index = index
        self._setup_ui()
        self._wire()
        self.retranslate_ui()

    def _setup_ui(self):
        main_lay = QtWidgets.QVBoxLayout(self)
        main_lay.setContentsMargins(6, 6, 6, 6)
        main_lay.setSpacing(4)

        top_lay = QtWidgets.QHBoxLayout()
        top_lay.setSpacing(6)

        self.radio = QtWidgets.QRadioButton()
        self.radio.setChecked(self.truck_manager.current_index == self.index)
        self.radio.setStyleSheet("""
            QRadioButton {
                font-size: 11px;
                font-weight: 500;
                color: #2c3e50;
                spacing: 6px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 1px solid #bdc3c7;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
        """)
        top_lay.addWidget(self.radio)

        self.name_edit = QtWidgets.QLineEdit(self.truck.name)
        self.name_edit.setFixedHeight(24)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
                font-size: 11px;
                font-weight: 500;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        top_lay.addWidget(self.name_edit, 1)

        self.ready_chk = QtWidgets.QCheckBox()
        self.ready_chk.setChecked(bool(self.truck.ready))
        self.ready_chk.setStyleSheet("""
            QCheckBox {
                font-size: 10px;
                color: #2c3e50;
                spacing: 4px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #27ae60;
                border-color: #229954;
            }
        """)
        top_lay.addWidget(self.ready_chk)

        main_lay.addLayout(top_lay)

        info_lay = QtWidgets.QHBoxLayout()
        info_lay.setSpacing(8)

        self.lbl_boxes = QtWidgets.QLabel("0")
        self.lbl_boxes.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #34495e;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 2px 4px;
                min-width: 40px;
            }
        """)
        
        self.lbl_weight = QtWidgets.QLabel("0")
        self.lbl_weight.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #34495e;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 2px 4px;
                min-width: 40px;
            }
        """)

        info_lay.addWidget(self.lbl_boxes)
        info_lay.addWidget(self.lbl_weight)
        info_lay.addStretch(1)

        main_lay.addLayout(info_lay)

        self.setStyleSheet("""
            TruckItemWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin: 2px;
            }
            TruckItemWidget:hover {
                background-color: #e9ecef;
                border-color: #3498db;
            }
        """)

    def _wire(self):
        self.radio.toggled.connect(self._on_select)
        self.name_edit.editingFinished.connect(self._on_rename)
        self.ready_chk.toggled.connect(self._on_ready)

    def refresh(self, truck, index):
        self.truck = truck
        self.index = index
        self.radio.setChecked(self.truck_manager.current_index == self.index)
        self.name_edit.setText(self.truck.name)
        self.ready_chk.setChecked(bool(self.truck.ready))
        boxes = self.truck.boxes or []
        self.lbl_boxes.setText(f"{tr('Боксов')}: {len(boxes)}")
        self.lbl_weight.setText(f"{tr('Итоговый вес')}: 0")

    def _on_select(self, checked):
        if checked:
            self.truck_manager.select_index(self.index)

    def _on_rename(self):
        self.truck_manager.select_index(self.index)
        self.truck_manager.rename_current(self.name_edit.text())

    def _on_ready(self, checked):
        self.truck_manager.select_index(self.index)
        self.truck_manager.set_ready_current(checked)

    def retranslate_ui(self):
        self.refresh(self.truck, self.index)

