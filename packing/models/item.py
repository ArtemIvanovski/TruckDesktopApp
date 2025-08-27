from dataclasses import dataclass
from typing import Iterable, List, Tuple, Optional, FrozenSet


def unique_orientations(l: float, w: float, h: float) -> List[Tuple[float, float, float]]:
    dims = [l, w, h]
    perms = set([
        (dims[0], dims[1], dims[2]),
        (dims[0], dims[2], dims[1]),
        (dims[1], dims[0], dims[2]),
        (dims[1], dims[2], dims[0]),
        (dims[2], dims[0], dims[1]),
        (dims[2], dims[1], dims[0]),
    ])
    return sorted(perms)


@dataclass(frozen=True)
class BoxItem:
    length: float
    width: float
    height: float
    index: int
    flags: FrozenSet[str] = frozenset()
    front_axis: Optional[str] = None  # 'x'|'y' when 'this_way_up' is present

    def orientations(self) -> Iterable[Tuple[float, float, float]]:
        if 'this_way_up' in self.flags:
            base_orients: List[Tuple[float, float, float]] = [(self.length, self.width, self.height), (self.width, self.length, self.height)]
            if self.front_axis == 'x':
                return [(self.length, self.width, self.height)]
            if self.front_axis == 'y':
                return [(self.width, self.length, self.height)]
            return base_orients
        return unique_orientations(self.length, self.width, self.height)


