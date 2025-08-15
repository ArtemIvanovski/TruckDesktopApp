#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid
from typing import Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal


class Box(QObject):
    CARGO_MARKINGS = {
        'fragile': {'name': 'Хрупкое', 'icon': '🍷', 'symbol': '🔍'},
        'this_way_up': {'name': 'Верх', 'icon': '⬆️', 'symbol': '↑↑'},
        'no_stack': {'name': 'Не штабелировать', 'icon': '📦', 'symbol': '⛔'},
        'keep_dry': {'name': 'Беречь от влаги', 'icon': '☔', 'symbol': '💧'},
        'center_gravity': {'name': 'Центр тяжести', 'icon': '⚖️', 'symbol': '⊕'},
        'alcohol': {'name': 'Алкоголь', 'icon': '🍺', 'symbol': '🍷'},
        'no_hooks': {'name': 'Без крюков', 'icon': '🚫', 'symbol': '⚓'},
        'temperature': {'name': 'Температурный режим', 'icon': '🌡️', 'symbol': '❄️'}
    }

    changed = pyqtSignal()

    def __init__(self, width, height, depth, label="", weight=0.0, quantity=1,
                 additional_info="", cargo_markings=None, parent=None):
        super().__init__(parent)

        self.id = str(uuid.uuid4())

        self.width = width
        self.height = height
        self.depth = depth

        self.label = label if label else f"PO#{self.id[:4]}"
        self.weight = weight  # в кг
        self.quantity = quantity

        self.position: Optional[Tuple[float, float, float]] = None

        self.is_in_truck = False
        self.is_rotated = False
        self.truck_index: Optional[int] = None

        self.color: Optional[Tuple[float, float, float]] = None
        self.additional_info = additional_info
        self.cargo_markings = cargo_markings or []

        self.mesh_object = None

    def get_volume(self) -> float:
        return self.width * self.height * self.depth

    def get_marking_icons(self):
        icons = []
        for marking in self.cargo_markings:
            if marking in self.CARGO_MARKINGS:
                icons.append(self.CARGO_MARKINGS[marking]['icon'])
        return icons

    def get_marking_names(self):
        names = []
        for marking in self.cargo_markings:
            if marking in self.CARGO_MARKINGS:
                names.append(self.CARGO_MARKINGS[marking]['name'])
        return names

    def get_total_weight(self) -> float:
        return self.weight * self.quantity

    def get_total_volume(self) -> float:
        return self.get_volume() * self.quantity

    def get_dimensions_string(self) -> str:
        return f"{self.width}×{self.height}×{self.depth} см"

    def get_info_string(self) -> str:
        lines = [
            f"Маркировка: {self.label}",
            f"Размеры: {self.get_dimensions_string()}",
            f"Вес: {self.weight:.1f} кг",
            f"Количество: {self.quantity} шт",
            f"Общий вес: {self.get_total_weight():.1f} кг",
            f"Объем: {self.get_volume():,.0f} см³"
        ]

        if self.additional_info:
            lines.append(f"Информация: {self.additional_info}")

        if self.cargo_markings:
            marking_names = self.get_marking_names()
            lines.append(f"Маркировки груза: {', '.join(marking_names)}")

        if self.is_in_truck:
            lines.append(f"В грузовике: #{self.truck_index + 1}")

        if self.position:
            x, y, z = self.position
            lines.append(f"Позиция: ({x:.1f}, {y:.1f}, {z:.1f}) см")

        lines.append(f"ID: {self.id[:8]}")

        return "\n".join(lines)

    def clone(self) -> 'Box':
        new_box = Box(
            width=self.width,
            height=self.height,
            depth=self.depth,
            label=self.label,
            weight=self.weight,
            quantity=1,
            parent=self.parent()
        )
        new_box.color = self.color
        return new_box

    def split(self, new_quantity: int) -> Optional['Box']:
        """Разделить коробки на две группы, возвращает новую группу"""
        if new_quantity >= self.quantity or new_quantity <= 0:
            return None

        # Создаем новую группу
        new_box = Box(
            width=self.width,
            height=self.height,
            depth=self.depth,
            label=self.label,
            weight=self.weight,
            quantity=new_quantity,
            parent=self.parent()
        )
        new_box.color = self.color

        # Уменьшаем количество в текущей группе
        self.quantity -= new_quantity
        self.changed.emit()

        return new_box

    def set_position(self, x: float, y: float, z: float):
        """Установить позицию в 3D пространстве"""
        self.position = (x, y, z)
        self.changed.emit()

    def set_in_truck(self, truck_index: int):
        """Поместить коробку в грузовик"""
        self.is_in_truck = True
        self.truck_index = truck_index
        self.changed.emit()

    def remove_from_truck(self):
        """Убрать коробку из грузовика"""
        self.is_in_truck = False
        self.truck_index = None
        self.changed.emit()

    def rotate(self):
        """Повернуть коробку (поменять местами ширину и глубину)"""
        self.width, self.depth = self.depth, self.width
        self.is_rotated = not self.is_rotated
        self.changed.emit()

    def can_fit_in_truck(self, truck_width: int, truck_height: int, truck_depth: int) -> bool:
        """Проверить, поместится ли коробка в грузовик"""
        return (self.width <= truck_width and
                self.height <= truck_height and
                self.depth <= truck_depth)

    def __str__(self) -> str:
        return f"Box({self.label}, {self.get_dimensions_string()}, {self.quantity}шт)"

    def __repr__(self) -> str:
        return self.__str__()


class BoxManager(QObject):
    """Менеджер для управления коллекцией коробок"""

    # Сигналы
    box_added = pyqtSignal(Box)
    box_removed = pyqtSignal(Box)
    boxes_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.boxes = []

    def add_box(self, box: Box):
        """Добавить коробку"""
        box.setParent(self)
        box.changed.connect(self.boxes_changed.emit)
        self.boxes.append(box)
        self.box_added.emit(box)
        self.boxes_changed.emit()

    def remove_box(self, box: Box):
        """Удалить коробку"""
        if box in self.boxes:
            self.boxes.remove(box)
            self.box_removed.emit(box)
            self.boxes_changed.emit()

    def get_all_boxes(self) -> list:
        """Получить все коробки"""
        return self.boxes.copy()

    def get_boxes_in_truck(self, truck_index: int = None) -> list:
        """Получить коробки в грузовике"""
        if truck_index is None:
            return [box for box in self.boxes if box.is_in_truck]
        return [box for box in self.boxes if box.is_in_truck and box.truck_index == truck_index]

    def get_boxes_in_bar(self) -> list:
        """Получить коробки в баре (не размещенные)"""
        return [box for box in self.boxes if not box.is_in_truck and box.position is None]

    def get_total_weight(self) -> float:
        """Получить общий вес всех коробок"""
        return sum(box.get_total_weight() for box in self.boxes)

    def get_total_volume(self) -> float:
        """Получить общий объем всех коробок"""
        return sum(box.get_total_volume() for box in self.boxes)

    def clear_all(self):
        """Очистить все коробки"""
        self.boxes.clear()
        self.boxes_changed.emit()

    def find_similar_boxes(self, box: Box) -> list:
        """Найти похожие коробки (одинаковые размеры)"""
        return [b for b in self.boxes
                if b != box and
                b.width == box.width and
                b.height == box.height and
                b.depth == box.depth]
