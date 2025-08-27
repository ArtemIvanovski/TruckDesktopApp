from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PlacedBox:
    x1: float
    y1: float
    z1: float
    x2: float
    y2: float
    z2: float
    index: int

    @property
    def bounds(self) -> Tuple[float, float, float, float, float, float]:
        return self.x1, self.y1, self.z1, self.x2, self.y2, self.z2


