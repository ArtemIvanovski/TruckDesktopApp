from PyQt5 import QtWidgets, QtCore, QtGui

from core.box.box import Box


class BoxRectWidget(QtWidgets.QWidget):
    def __init__(self, box: Box, parent=None):
        super().__init__(parent)
        self.box = box
        self.setFixedSize(50, 50)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Цвет коробки по размерам как в Babylon.js
        import json
        import random
        
        # Создаем ключ цвета по размерам как в Babylon: JSON.stringify([boxWidth, boxDepth, boxHeight])
        box_color_key = json.dumps([self.box.width, self.box.depth, self.box.height])
        
        # Создаем статический словарь цветов для виджетов (как boxColors Map в Babylon)
        if not hasattr(BoxRectWidget, '_box_colors'):
            BoxRectWidget._box_colors = {}
        
        if box_color_key not in BoxRectWidget._box_colors:
            # Генерируем цвет как в Babylon: new BABYLON.Color3(Math.random(), Math.random(), Math.random())
            # Используем hash для детерминированности (одинаковый размер = одинаковый цвет всегда)
            hash_val = hash(box_color_key) & 0x7FFFFFFF  # Положительное число
            random.seed(hash_val)
            r = random.random()
            g = random.random() 
            b = random.random()
            BoxRectWidget._box_colors[box_color_key] = (r, g, b)
            print(f"[BoxRect] Generated new color for size {box_color_key}: ({r:.3f}, {g:.3f}, {b:.3f}) with seed {hash_val}")
        else:
            r, g, b = BoxRectWidget._box_colors[box_color_key]
            print(f"[BoxRect] Using existing color for size {box_color_key}: ({r:.3f}, {g:.3f}, {b:.3f})")
        
        color = QtGui.QColor(int(r * 255), int(g * 255), int(b * 255))

        rect = self.rect().adjusted(2, 2, -2, -2)

        brush = QtGui.QBrush(color)
        painter.setBrush(brush)

        pen = QtGui.QPen(color.darker(150), 2)
        painter.setPen(pen)

        painter.drawRoundedRect(rect, 4, 4)

        painter.setPen(QtGui.QPen(QtCore.Qt.white if color.lightness() < 128 else QtCore.Qt.black))
        font = painter.font()
        font.setPointSize(4)
        font.setBold(True)
        painter.setFont(font)

        w = self.box.width
        h = self.box.height
        d = self.box.depth

        size_text = f"{w}×{h}"
        painter.drawText(rect, QtCore.Qt.AlignCenter, size_text)

        marking_icons = self.box.get_marking_icons()
        if marking_icons:
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            painter.setPen(QtGui.QPen(QtCore.Qt.black))

            icon_x = rect.right() - 18
            for icon in marking_icons[:3]:
                icon_rect = QtCore.QRect(icon_x, rect.top() + 2, 16, 16)
                painter.drawText(icon_rect, QtCore.Qt.AlignCenter, icon)
                icon_x -= 16

