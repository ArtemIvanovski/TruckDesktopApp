from PyQt5.QtCore import QObject, pyqtSignal

from core.box.box import Box


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
        """Добавить коробку. Если существует идентичная коробка, то увеличить её количество"""
        # Ищем существующую коробку с такими же параметрами
        existing_box = self.find_identical_box(box)
        
        if existing_box:
            # Объединяем коробки
            existing_box.quantity += box.quantity
            # Обновляем маркировку, если новая коробка имеет стандартную маркировку PO#
            if (not box.label.startswith("PO#") and 
                existing_box.label.startswith("PO#")):
                existing_box.label = box.label
            existing_box.changed.emit()
            self.boxes_changed.emit()
            print(f"[BoxManager] Merged box into existing {existing_box.label}, new quantity: {existing_box.quantity}")
        else:
            # Добавляем новую коробку
            box.setParent(self)
            box.changed.connect(self.boxes_changed.emit)
            self.boxes.append(box)
            self.box_added.emit(box)
            self.boxes_changed.emit()
            print(f"[BoxManager] Added new box {box.label}, quantity: {box.quantity}")

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

    def find_identical_box(self, box: Box) -> Box:
        """Найти идентичную коробку (одинаковые все параметры кроме ID, количества и маркировки)"""
        for existing_box in self.boxes:
            if existing_box.is_similar_to(box):
                return existing_box
        return None