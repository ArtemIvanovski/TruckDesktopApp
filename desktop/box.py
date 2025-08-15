#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid
from typing import Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal


class Box(QObject):
    changed = pyqtSignal()

    def __init__(self,
                 width: int,
                 height: int,
                 depth: int,
                 label: str = "",
                 weight: float = 0.0,
                 quantity: int = 1,
                 parent=None):
        super().__init__(parent)

        # Уникальный идентификатор
        self.id = str(uuid.uuid4())

        # Размеры (в см)
        self.width = width
        self.height = height
        self.depth = depth

        # Информация о коробке
        self.label = label if label else f"PO#{self.id[:4]}"
        self.weight = weight  # в кг
        self.quantity = quantity

        # Позиция в 3D пространстве (изначально None - коробка в баре)
        self.position: Optional[Tuple[float, float, float]] = None

        # Состояние коробки
        self.is_in_truck = False
        self.is_rotated = False
        self.truck_index: Optional[int] = None

        # Цвет для отображения (будет генерироваться автоматически)
        self.color: Optional[Tuple[float, float, float]] = None

        # 3D объект (если коробка размещена на сцене)
        self.mesh_object = None

    def get_volume(self) -> float:
        """Получить объем коробки в кубических см"""
        return self.width * self.height * self.depth

    def get_total_weight(self) -> float:
        """Получить общий вес всех коробок данного типа"""
        return self.weight * self.quantity

    def get_total_volume(self) -> float:
        """Получить общий объем всех коробок данного типа"""
        return self.get_volume() * self.quantity

    def get_dimensions_string(self) -> str:
        """Получить строку с размерами"""
        return f"{self.width}×{self.height}×{self.depth} см"

    def get_info_string(self) -> str:
        """Получить полную информацию о коробке"""
        lines = [
            f"Маркировка: {self.label}",
            f"Размеры: {self.get_dimensions_string()}",
            f"Вес: {self.weight} кг",
            f"Количество: {self.quantity}",
            f"Общий вес: {self.get_total_weight()} кг",
            f"Объем: {self.get_volume()} см³"
        ]

        if self.is_in_truck:
            lines.append(f"В грузовике: #{self.truck_index + 1}")

        if self.position:
            x, y, z = self.position
            lines.append(f"Позиция: ({x:.1f}, {y:.1f}, {z:.1f})")

        return "\n".join(lines)

    def clone(self) -> 'Box':
        """Создать копию коробки с новым ID"""
        new_box = Box(
            width=self.width,
            height=self.height,
            depth=self.depth,
            label=self.label,
            weight=self.weight,
            quantity=1,  # При клонировании количество всегда 1
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