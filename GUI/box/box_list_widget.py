from PyQt5 import QtWidgets, QtCore

from GUI.box.box_2D_widget import Box2DWidget
from core.box.box import Box
from core.box.box_manager import BoxManager
from core.i18n import tr, TranslatableMixin


class BoxListWidget(QtWidgets.QWidget, TranslatableMixin):
    def __init__(self, box_manager: BoxManager, parent=None):
        super().__init__(parent)
        self.box_manager = box_manager
        self.setup_ui()
        self.retranslate_ui()

        self.box_manager.box_added.connect(self.add_box_widget)
        self.box_manager.box_removed.connect(self.remove_box_widget)
        self.box_manager.boxes_changed.connect(self.update_header)  # Обновляем header при любых изменениях
        
        print(f"[BoxListWidget] Connected to box_manager signals")

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.header_label = QtWidgets.QLabel()
        self.header_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                padding: 6px;
                background-color: #f1c40f;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.header_label)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.boxes_container = QtWidgets.QWidget()
        self.boxes_layout = QtWidgets.QVBoxLayout(self.boxes_container)
        self.boxes_layout.setContentsMargins(0, 0, 0, 0)
        self.boxes_layout.setSpacing(4)
        self.boxes_layout.addStretch()

        scroll.setWidget(self.boxes_container)
        layout.addWidget(scroll)

        buttons_layout = QtWidgets.QHBoxLayout()

        self.clear_button = QtWidgets.QPushButton()
        self.clear_button.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                color: white;
                background-color: #e74c3c;
                border: none;
                border-radius: 3px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.clear_button.clicked.connect(self.clear_all_boxes)
        buttons_layout.addWidget(self.clear_button)

        layout.addLayout(buttons_layout)

    def add_box_widget(self, box: Box):
        print(f"[BoxListWidget] Adding widget for box {box.label}, quantity={box.quantity}")
        box_widget = Box2DWidget(box, self)
        self.boxes_layout.insertWidget(self.boxes_layout.count() - 1, box_widget)
        self.update_header()

    def remove_box_widget(self, box: Box):
        print(f"[BoxListWidget] Removing widget for box {box.label}")
        for i in range(self.boxes_layout.count()):
            item = self.boxes_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, Box2DWidget) and widget.box == box:
                    print(f"[BoxListWidget] Found and removing widget for {box.label}")
                    widget.deleteLater()
                    break

        self.update_header()

    def update_header(self):
        boxes = self.box_manager.get_boxes_in_bar()
        count = len(boxes)
        total_weight = sum(box.get_total_weight() for box in boxes)
        total_qty = sum(box.quantity for box in boxes)

        print(f"[BoxListWidget] Updating header: {count} types, {total_qty} items, {total_weight:.1f}kg")
        for box in boxes:
            print(f"[BoxListWidget]   - {box.label}: qty={box.quantity}")

        header_text = tr("Коробки ({count} типов, {total_qty} шт, {total_weight:.1f} кг)").format(
            count=count, total_qty=total_qty, total_weight=total_weight)
        self.header_label.setText(header_text)

    def clear_all_boxes(self):
        reply = QtWidgets.QMessageBox.question(
            self, tr('Очистить все коробки'),
            tr('Вы уверены, что хотите удалить все коробки?'),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            while self.boxes_layout.count() > 1:
                item = self.boxes_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()

            self.box_manager.clear_all()
            self.update_header()
    
    def retranslate_ui(self):
        self.clear_button.setText(tr("Очистить все"))
        self.update_header()
