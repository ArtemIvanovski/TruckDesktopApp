from typing import List, Optional, Tuple

from core.trucks.truck_model import TruckModel


class TruckManager:
    def __init__(self):
        self.trucks: List[TruckModel] = []
        self.current_index: int = 0
        self.app3d = None
        self._callbacks = []
        # In-memory only: always start with one default truck
        self.trucks.append(TruckModel(1, 'Грузовик 1', 1650, 260, 245))

    def set_app3d(self, app3d):
        self.app3d = app3d
        self._notify()

    def set_on_changed(self, callback):
        self.add_on_changed(callback)

    def add_on_changed(self, callback):
        try:
            if callable(callback) and callback not in self._callbacks:
                self._callbacks.append(callback)
                self._notify()
        except Exception:
            pass

    def remove_on_changed(self, callback):
        try:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
        except Exception:
            pass

    def _notify(self):
        for cb in list(self._callbacks):
            try:
                cb()
            except Exception:
                continue

    def _load(self):
        # No-op: persistence disabled
        return

    def _save(self):
        # No-op: persistence disabled
        return

    def get_current(self) -> TruckModel:
        return self.trucks[self.current_index]

    def add_truck(self) -> TruckModel:
        new_id = max([t.id for t in self.trucks] + [0]) + 1
        model = TruckModel(new_id, f'Грузовик {new_id}', 1650, 260, 245)
        self.trucks.append(model)
        self.current_index = len(self.trucks) - 1
        self._notify()
        return model

    def remove_current_truck(self):
        if len(self.trucks) <= 1:
            return
        del self.trucks[self.current_index]
        if self.current_index >= len(self.trucks):
            self.current_index = len(self.trucks) - 1
        self._notify()

    def select_index(self, index: int):
        if index < 0 or index >= len(self.trucks):
            return
        if self.app3d:
            self._capture_boxes_to_current()
        self.current_index = index
        if self.app3d:
            self._apply_current_to_scene()
        self._notify()

    def select_next(self):
        self.select_index((self.current_index + 1) % len(self.trucks))

    def select_prev(self):
        self.select_index((self.current_index - 1) % len(self.trucks))

    def rename_current(self, name: str):
        self.get_current().name = name.strip() or self.get_current().name
        self._notify()

    def set_ready_current(self, ready: bool):
        self.get_current().ready = bool(ready)
        self._notify()

    def set_overlay_current(self, visible: bool):
        self.get_current().show_overlay = bool(visible)
        self._notify()

    def set_size_current(self, width: int, height: int, depth: int):
        t = self.get_current()
        t.width, t.height, t.depth = int(width), int(height), int(depth)
        if self.app3d:
            self.app3d.switch_truck(t.width, t.height, t.depth)
        self._notify()

    def set_tent_state_current(self, alpha: float, is_open: bool):
        t = self.get_current()
        t.tent_alpha = float(alpha)
        t.tent_open = bool(is_open)
        if self.app3d:
            self.app3d.set_tent_alpha(alpha)
        self._notify()

    def capture_now(self):
        if self.app3d:
            self._capture_boxes_to_current()
            self._notify()

    def _capture_boxes_to_current(self):
        if not self.app3d:
            return
        boxes = []
        for node in getattr(self.app3d, 'scene_boxes', []) or []:
            if not node or node.isEmpty():
                continue
            try:
                data = node.getPythonTag('box_data') or {}
                pos = self.app3d.render.getRelativePoint(node, (0, 0, 0))
                h, p, r = node.getHpr(self.app3d.render)
                boxes.append({
                    'box_data': data,
                    'pos': {'x': pos.x, 'y': pos.y, 'z': pos.z},
                    'hpr': {'h': h, 'p': p, 'r': r},
                })
            except Exception:
                continue
        self.get_current().boxes = boxes

    def _apply_current_to_scene(self):
        t = self.get_current()
        if self.app3d:
            self.app3d.switch_truck(t.width, t.height, t.depth)
            self.app3d.set_tent_alpha(t.tent_alpha)
            self._clear_scene_boxes()
            for b in t.boxes or []:
                try:
                    node = self.app3d.create_3d_box_from_data(b.get('box_data', {}), None)
                    if node:
                        pos = b.get('pos', {})
                        hpr = b.get('hpr', {})
                        node.setPos(self.app3d.render, float(pos.get('x', 0)), float(pos.get('y', 0)), float(pos.get('z', 0)))
                        node.setHpr(self.app3d.render, float(hpr.get('h', 0)), float(hpr.get('p', 0)), float(hpr.get('r', 0)))
                except Exception:
                    continue

    def _clear_scene_boxes(self):
        try:
            for node in list(getattr(self.app3d, 'scene_boxes', []) or []):
                try:
                    node.removeNode()
                except Exception:
                    pass
            if hasattr(self.app3d, 'scene_boxes'):
                self.app3d.scene_boxes = []
        except Exception:
            pass

    def get_items(self) -> List[TruckModel]:
        return list(self.trucks)

