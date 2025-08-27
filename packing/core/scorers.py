from typing import Tuple


def volume(bounds: Tuple[float, float, float, float, float, float]) -> float:
    return (bounds[3] - bounds[0]) * (bounds[4] - bounds[1]) * (bounds[5] - bounds[2])


def score_position(bounds: Tuple[float, float, float, float, float, float]) -> float:
    x1, y1, z1, x2, y2, z2 = bounds
    return z1 * 1e6 + y1 * 1e3 + x1


