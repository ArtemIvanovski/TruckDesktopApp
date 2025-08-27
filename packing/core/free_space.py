from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


def boxes_overlap(a: Tuple[float, float, float, float, float, float], b: Tuple[float, float, float, float, float, float]) -> bool:
    return not (a[3] <= b[0] or a[0] >= b[3] or a[4] <= b[1] or a[1] >= b[4] or a[5] <= b[2] or a[2] >= b[5])


@dataclass
class FreeBox:
    x1: float
    y1: float
    z1: float
    x2: float
    y2: float
    z2: float

    def fits(self, l: float, w: float, h: float) -> bool:
        return (self.x2 - self.x1) + 1e-9 >= l and (self.y2 - self.y1) + 1e-9 >= w and (self.z2 - self.z1) + 1e-9 >= h

    def volume(self) -> float:
        return max(0.0, self.x2 - self.x1) * max(0.0, self.y2 - self.y1) * max(0.0, self.z2 - self.z1)

    def split(self, placed: Tuple[float, float, float, float, float, float]) -> List["FreeBox"]:
        px1, py1, pz1, px2, py2, pz2 = placed
        if not boxes_overlap((self.x1, self.y1, self.z1, self.x2, self.y2, self.z2), placed):
            return [self]

        result: List[FreeBox] = []
        if self.x1 < px1:
            result.append(FreeBox(self.x1, self.y1, self.z1, px1, self.y2, self.z2))
        if px2 < self.x2:
            result.append(FreeBox(px2, self.y1, self.z1, self.x2, self.y2, self.z2))
        if self.y1 < py1:
            result.append(FreeBox(max(self.x1, px1), self.y1, self.z1, min(self.x2, px2), py1, self.z2))
        if py2 < self.y2:
            result.append(FreeBox(max(self.x1, px1), py2, self.z1, min(self.x2, px2), self.y2, self.z2))
        if self.z1 < pz1:
            result.append(FreeBox(max(self.x1, px1), max(self.y1, py1), self.z1, min(self.x2, px2), min(self.y2, py2), pz1))
        if pz2 < self.z2:
            result.append(FreeBox(max(self.x1, px1), max(self.y1, py1), pz2, min(self.x2, px2), min(self.y2, py2), self.z2))

        compacted: List[FreeBox] = []
        for fb in result:
            if fb.x2 - fb.x1 > 1e-9 and fb.y2 - fb.y1 > 1e-9 and fb.z2 - fb.z1 > 1e-9:
                compacted.append(fb)
        return compacted


class FreeSpaceManager:
    def __init__(self, bounds: Tuple[float, float, float, float, float, float]):
        self.free_boxes: List[FreeBox] = [FreeBox(*bounds)]

    def find_positions(self, l: float, w: float, h: float) -> Iterable[Tuple[float, float, float, float, float, float]]:
        for fb in self.free_boxes:
            if fb.fits(l, w, h):
                yield fb.x1, fb.y1, fb.z1, fb.x1 + l, fb.y1 + w, fb.z1 + h

    def place(self, placed: Tuple[float, float, float, float, float, float]) -> None:
        new_free: List[FreeBox] = []
        for fb in self.free_boxes:
            new_free.extend(fb.split(placed))
        self.free_boxes = self._merge(new_free)

    def clone(self) -> "FreeSpaceManager":
        clone_mgr = FreeSpaceManager((0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        clone_mgr.free_boxes = [FreeBox(fb.x1, fb.y1, fb.z1, fb.x2, fb.y2, fb.z2) for fb in self.free_boxes]
        return clone_mgr

    def total_free_volume(self) -> float:
        return sum(fb.volume() for fb in self.free_boxes)

    def _merge(self, boxes: List[FreeBox]) -> List[FreeBox]:
        merged: List[FreeBox] = []
        for b in boxes:
            skip = False
            for m in merged:
                if self._contained(b, m):
                    skip = True
                    break
            if not skip:
                merged.append(b)
        return merged

    @staticmethod
    def _contained(a: FreeBox, b: FreeBox) -> bool:
        return a.x1 >= b.x1 and a.y1 >= b.y1 and a.z1 >= b.z1 and a.x2 <= b.x2 and a.y2 <= b.y2 and a.z2 <= b.z2


