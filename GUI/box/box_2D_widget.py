import json

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDrag

from GUI.box.box_rect_widget import BoxRectWidget
from core.box.box import Box


class Box2DWidget(QtWidgets.QWidget):
    def __init__(self, box: Box, parent=None):
        super().__init__(parent)
        self.box = box
        self.setFixedHeight(60)
        self.setMinimumWidth(150)
        self.setToolTip(box.get_info_string())

        box.changed.connect(self.update_display)

        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        box_display = BoxRectWidget(self.box)
        layout.addWidget(box_display)

        info_layout = QtWidgets.QVBoxLayout()
        info_layout.setSpacing(2)

        self.label_text = QtWidgets.QLabel(self.box.label)
        self.label_text.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 11px;
                color: #2c3e50;
            }
        """)
        info_layout.addWidget(self.label_text)

        # Размеры
        self.size_text = QtWidgets.QLabel(self.box.get_dimensions_string())
        self.size_text.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #7f8c8d;
            }
        """)
        info_layout.addWidget(self.size_text)

        weight_qty_text = f"{self.box.weight}кг"
        if self.box.quantity > 1:
            weight_qty_text += f" × {self.box.quantity}"
        self.weight_qty_label = QtWidgets.QLabel(weight_qty_text)
        self.weight_qty_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #34495e;
            }
        """)
        info_layout.addWidget(self.weight_qty_label)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        delete_btn = QtWidgets.QPushButton("×")
        delete_btn.setFixedSize(20, 20)
        delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
        delete_btn.clicked.connect(self.delete_box)
        layout.addWidget(delete_btn)

        # Создаем индикатор количества (всегда создаем, но скрываем если quantity = 1)
        self.qty_label = QtWidgets.QLabel(f"×{self.box.quantity}")
        self.qty_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #e74c3c;
                background-color: #fadbd8;
                border-radius: 8px;
                padding: 2px 6px;
                min-width: 20px;
            }
        """)
        self.qty_label.setAlignment(QtCore.Qt.AlignCenter)
        
        # Показываем индикатор только если количество > 1
        if self.box.quantity > 1:
            self.qty_label.show()
        else:
            self.qty_label.hide()
            
        layout.addWidget(self.qty_label)

    def delete_box(self):
        reply = QtWidgets.QMessageBox.question(
            self, 'Удалить коробку',
            f'Удалить коробку {self.box.label}?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            parent = self.parent()
            while parent and not hasattr(parent, 'box_manager'):
                parent = parent.parent()
            if parent:
                parent.box_manager.remove_box(self.box)

    def update_display(self):
        print(f"[UpdateDisplay] Updating display for box {self.box.label}, quantity={self.box.quantity}")
        
        # Обновляем только текстовые элементы, не пересоздаем layout
        if hasattr(self, 'label_text'):
            self.label_text.setText(self.box.label)
        
        if hasattr(self, 'size_text'):
            self.size_text.setText(self.box.get_dimensions_string())

        if hasattr(self, 'weight_qty_label'):
            weight_qty_text = f"{self.box.weight}кг"
            if self.box.quantity > 1:
                weight_qty_text += f" × {self.box.quantity}"
            self.weight_qty_label.setText(weight_qty_text)

        # Обновляем индикатор количества
        if hasattr(self, 'qty_label'):
            self.qty_label.setText(f"×{self.box.quantity}")
            if self.box.quantity > 1:
                self.qty_label.show()
                print(f"[UpdateDisplay] Showing quantity label: ×{self.box.quantity}")
            else:
                self.qty_label.hide()
                print(f"[UpdateDisplay] Hiding quantity label (quantity=1)")

        # Обновляем tooltip
        tooltip_parts = [self.box.get_info_string()]

        if self.box.additional_info:
            tooltip_parts.append(f"Информация: {self.box.additional_info}")

        if self.box.cargo_markings:
            marking_name = self.box.get_marking_names()
            tooltip_parts.append(f"Маркировка: {marking_name}")

        self.setToolTip("\n".join(tooltip_parts))
        
        print(f"[UpdateDisplay] Updated all elements for box {self.box.label}")

    def enterEvent(self, event):
        """При наведении мыши"""
        self.setStyleSheet("""
            Box2DWidget {
                background-color: #e8f4fd;
                border: 1px solid #3498db;
                border-radius: 4px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("""
            Box2DWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return

        if not hasattr(self, 'drag_start_position'):
            return

        if ((event.pos() - self.drag_start_position).manhattanLength() <
                QtWidgets.QApplication.startDragDistance()):
            return

        self.start_drag()

    def start_drag(self):
        drag = QDrag(self)
        mimeData = QtCore.QMimeData()

        box_data = {
            'id': self.box.id,
            'width': self.box.width,
            'height': self.box.height,
            'depth': self.box.depth,
            'label': self.box.label,
            'weight': self.box.weight,
            'quantity': self.box.quantity,
            'additional_info': self.box.additional_info,
            'cargo_markings': self.box.cargo_markings
        }
        # Убираем color из box_data - цвет будет определяться размерами в 3D сцене
        
        print(f"[Drag] Starting drag for box {self.box.label} (color will be determined by size: {self.box.width}x{self.box.height}x{self.box.depth})")

        mimeData.setText(json.dumps(box_data))
        drag.setMimeData(mimeData)

        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())

        dropAction = drag.exec_(Qt.MoveAction | Qt.CopyAction)

        print(f"[DragResult] Box {self.box.label}: dropAction={dropAction}, quantity_before={self.box.quantity}")
        
        # Если drag был принят (не зависимо от типа), обрабатываем как успешный
        if dropAction != Qt.IgnoreAction:
            print(f"[DragResult] Drag accepted, calling handle_successful_drag()")
            self.handle_successful_drag()
        else:
            print(f"[DragResult] Drag was ignored, no quantity change")

    def handle_successful_drag(self):
        print(f"[HandleDrag] Box {self.box.label}: current quantity={self.box.quantity}")
        if self.box.quantity > 1:
            old_quantity = self.box.quantity
            self.box.quantity -= 1
            print(f"[HandleDrag] Reduced quantity from {old_quantity} to {self.box.quantity}")
            self.box.changed.emit()
        else:
            print(f"[HandleDrag] Removing box {self.box.label} from manager (quantity=1)")
            parent = self.parent()
            while parent and not hasattr(parent, 'box_manager'):
                parent = parent.parent()
            if parent:
                parent.box_manager.remove_box(self.box)
            else:
                print(f"[HandleDrag] ERROR: Could not find box_manager parent")

