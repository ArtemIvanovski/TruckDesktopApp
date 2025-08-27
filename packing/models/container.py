from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Container:
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    @property
    def size_x(self) -> float:
        return self.max_x - self.min_x

    @property
    def size_y(self) -> float:
        return self.max_y - self.min_y

    @property
    def size_z(self) -> float:
        return self.max_z - self.min_z

    @staticmethod
    def from_points(points: Tuple[Tuple[float, float, float], ...]) -> "Container":
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        zs = [p[2] for p in points]
        return Container(min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


