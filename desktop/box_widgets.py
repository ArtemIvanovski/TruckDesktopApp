import random
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
from box import Box, BoxManager


class BoxCreationWidget(QtWidgets.QWidget):
    box_created = pyqtSignal(Box)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QtWidgets.QLabel("Добавить коробки")
        title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                padding: 4px;
                background-color: #ecf0f1;
                border-radius: 3px;
            }
        """)
        layout.addWidget(title)

        # Форма для ввода параметров
        form_widget = QtWidgets.QWidget()
        form = QtWidgets.QGridLayout(form_widget)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(6)

        # Стиль для полей ввода
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

        # Размеры
        form.addWidget(QtWidgets.QLabel("Длина (см):"), 0, 0)
        self.width_input = QtWidgets.QSpinBox()
        self.width_input.setRange(1, 999)
        self.width_input.setValue(100)
        self.width_input.setStyleSheet(input_style)
        form.addWidget(self.width_input, 0, 1)

        form.addWidget(QtWidgets.QLabel("Ширина (см):"), 1, 0)
        self.depth_input = QtWidgets.QSpinBox()
        self.depth_input.setRange(1, 999)
        self.depth_input.setValue(80)
        self.depth_input.setStyleSheet(input_style)
        form.addWidget(self.depth_input, 1, 1)

        form.addWidget(QtWidgets.QLabel("Высота (см):"), 2, 0)
        self.height_input = QtWidgets.QSpinBox()
        self.height_input.setRange(1, 999)
        self.height_input.setValue(60)
        self.height_input.setStyleSheet(input_style)
        form.addWidget(self.height_input, 2, 1)

        # Маркировка
        form.addWidget(QtWidgets.QLabel("Маркировка:"), 3, 0)
        self.label_input = QtWidgets.QLineEdit()
        self.label_input.setPlaceholderText("PO#1234")
        self.label_input.setStyleSheet(input_style)
        form.addWidget(self.label_input, 3, 1)

        # Вес
        form.addWidget(QtWidgets.QLabel("Вес (кг):"), 4, 0)
        self.weight_input = QtWidgets.QDoubleSpinBox()
        self.weight_input.setRange(0.1, 999.9)
        self.weight_input.setValue(5.0)
        self.weight_input.setDecimals(1)
        self.weight_input.setStyleSheet(input_style)
        form.addWidget(self.weight_input, 4, 1)

        # Количество
        form.addWidget(QtWidgets.QLabel("Количество:"), 5, 0)
        self.quantity_input = QtWidgets.QSpinBox()
        self.quantity_input.setRange(1, 999)
        self.quantity_input.setValue(1)
        self.quantity_input.setStyleSheet(input_style)
        form.addWidget(self.quantity_input, 5, 1)

        layout.addWidget(form_widget)

        # Кнопка добавления
        add_button = QtWidgets.QPushButton("Добавить")
        add_button.setStyleSheet("""
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
        add_button.clicked.connect(self.create_box)
        layout.addWidget(add_button)

        # Кнопка очистки формы
        clear_button = QtWidgets.QPushButton("Очистить")
        clear_button.setStyleSheet("""
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
        clear_button.clicked.connect(self.clear_form)
        layout.addWidget(clear_button)

    def create_box(self):
        """Создать новую коробку с введенными параметрами"""
        try:
            width = self.width_input.value()
            height = self.height_input.value()
            depth = self.depth_input.value()
            label = self.label_input.text().strip()
            weight = self.weight_input.value()
            quantity = self.quantity_input.value()

            if not label:
                label = f"PO#{random.randint(1000, 9999)}"

            box = Box(
                width=width,
                height=height,
                depth=depth,
                label=label,
                weight=weight,
                quantity=quantity
            )

            box.color = (
                random.uniform(0.3, 0.9),
                random.uniform(0.3, 0.9),
                random.uniform(0.3, 0.9)
            )

            self.box_created.emit(box)

            if label.startswith("PO#"):
                try:
                    num = int(label[3:]) + 1
                    self.label_input.setText(f"PO#{num}")
                except ValueError:
                    pass

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось создать коробку: {e}")

    def clear_form(self):
        self.width_input.setValue(100)
        self.height_input.setValue(60)
        self.depth_input.setValue(80)
        self.label_input.clear()
        self.weight_input.setValue(5.0)
        self.quantity_input.setValue(1)


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

        if self.box.quantity > 1:
            qty_label = QtWidgets.QLabel(f"×{self.box.quantity}")
            qty_label.setStyleSheet("""
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
            qty_label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(qty_label)

    def update_display(self):
        self.label_text.setText(self.box.label)
        self.size_text.setText(self.box.get_dimensions_string())

        weight_qty_text = f"{self.box.weight}кг"
        if self.box.quantity > 1:
            weight_qty_text += f" × {self.box.quantity}"
        self.weight_qty_label.setText(weight_qty_text)

        self.setToolTip(self.box.get_info_string())

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


class BoxRectWidget(QtWidgets.QWidget):
    def __init__(self, box: Box, parent=None):
        super().__init__(parent)
        self.box = box
        self.setFixedSize(50, 50)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Цвет коробки
        if self.box.color:
            r, g, b = self.box.color
            color = QtGui.QColor(int(r * 255), int(g * 255), int(b * 255))
        else:
            color = QtGui.QColor(100, 150, 200)

        # Рисуем прямоугольник коробки
        rect = self.rect().adjusted(2, 2, -2, -2)

        # Заливка
        brush = QtGui.QBrush(color)
        painter.setBrush(brush)

        # Контур
        pen = QtGui.QPen(color.darker(150), 2)
        painter.setPen(pen)

        painter.drawRoundedRect(rect, 4, 4)

        # Рисуем размеры внутри прямоугольника
        painter.setPen(QtGui.QPen(QtCore.Qt.white if color.lightness() < 128 else QtCore.Qt.black))
        font = painter.font()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)

        # Сокращенные размеры
        w = self.box.width
        h = self.box.height
        d = self.box.depth

        # Отображаем размеры как ширина×высота
        size_text = f"{w}×{h}"
        painter.drawText(rect, QtCore.Qt.AlignCenter, size_text)


class BoxListWidget(QtWidgets.QWidget):
    """Виджет для отображения списка всех коробок"""

    def __init__(self, box_manager: BoxManager, parent=None):
        super().__init__(parent)
        self.box_manager = box_manager
        self.setup_ui()

        # Подключаем сигналы менеджера
        self.box_manager.box_added.connect(self.add_box_widget)
        self.box_manager.box_removed.connect(self.remove_box_widget)

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Заголовок со статистикой
        self.header_label = QtWidgets.QLabel("Коробки (0)")
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

        # Скролл область для коробок
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

        # Кнопки управления
        buttons_layout = QtWidgets.QHBoxLayout()

        clear_button = QtWidgets.QPushButton("Очистить все")
        clear_button.setStyleSheet("""
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
        clear_button.clicked.connect(self.clear_all_boxes)
        buttons_layout.addWidget(clear_button)

        layout.addLayout(buttons_layout)

    def add_box_widget(self, box: Box):
        """Добавить виджет коробки в список"""
        box_widget = Box2DWidget(box, self)

        # Добавляем перед stretch
        self.boxes_layout.insertWidget(self.boxes_layout.count() - 1, box_widget)

        self.update_header()

    def remove_box_widget(self, box: Box):
        """Удалить виджет коробки из списка"""
        # Находим и удаляем соответствующий виджет
        for i in range(self.boxes_layout.count()):
            item = self.boxes_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, Box2DWidget) and widget.box == box:
                    widget.deleteLater()
                    break

        self.update_header()

    def update_header(self):
        """Обновить заголовок со статистикой"""
        boxes = self.box_manager.get_boxes_in_bar()
        count = len(boxes)
        total_weight = sum(box.get_total_weight() for box in boxes)
        total_qty = sum(box.quantity for box in boxes)

        header_text = f"Коробки ({count} типов, {total_qty} шт, {total_weight:.1f} кг)"
        self.header_label.setText(header_text)

    def clear_all_boxes(self):
        """Очистить все коробки"""
        reply = QtWidgets.QMessageBox.question(
            self, 'Очистить все коробки',
            'Вы уверены, что хотите удалить все коробки?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self.box_manager.clear_all()


class BoxManagementWidget(QtWidgets.QWidget):
    """Главный виджет для управления коробками"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.box_manager = BoxManager(self)
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Виджет создания коробок
        creation_widget = BoxCreationWidget(self)
        creation_widget.box_created.connect(self.box_manager.add_box)
        layout.addWidget(creation_widget)

        # Разделитель
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)

        # Список коробок
        list_widget = BoxListWidget(self.box_manager, self)
        layout.addWidget(list_widget)

    def get_box_manager(self) -> BoxManager:
        return self.box_manager