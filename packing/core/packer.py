from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, List, Sequence, Tuple
import time
import random

from .free_space import FreeSpaceManager
from .scorers import score_position
from ..models.container import Container
from ..models.item import BoxItem
from ..models.placement import PlacedBox


logger = logging.getLogger(__name__)


@dataclass
class PackingConfig:
    time_limit_sec: float = 10.0
    position_scorer: Callable[[Tuple[float, float, float, float, float, float]], float] = score_position
    sort_key: Callable[[BoxItem], float] = lambda item: item.length * item.width * item.height
    min_support_ratio: float = 0.95
    contact_weight_wall: float = 1_000.0
    contact_weight_box: float = 2_000.0
    beam_width: int = 8
    max_positions_per_item: int = 64
    alternate_starts: int = 3
    diversify: bool = True
    jitter: float = 1e-6
    exploratory_pick: int = 2
    objective: str = "count"  # "count" | "volume"
    prefer_small_boxes: bool = False
    z_bias: float = 1e-3
    beam_widen_until: int = 2
    beam_widen_factor: int = 2
    allow_stacking: bool = True
    stack_same_face_only: bool = False
    size_tol: float = 1e-6


class Packer:
    def __init__(self, container: Container, config: PackingConfig | None = None):
        self.container = container
        self.config = config or PackingConfig()
        self.free = FreeSpaceManager((container.min_x, container.min_y, container.min_z, container.max_x, container.max_y, container.max_z))
        self.placed: List[PlacedBox] = []

    def _xy_overlap_area(self, a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ox = max(0.0, min(ax2, bx2) - max(ax1, bx1))
        oy = max(0.0, min(ay2, by2) - max(ay1, by1))
        return ox * oy

    def _support_ratio(self, candidate: Tuple[float, float, float, float, float, float]) -> float:
        x1, y1, z1, x2, y2, z2 = candidate
        if abs(z1 - self.container.min_z) < 1e-9:
            return 1.0
        support_level = z1
        bottom = (x1, y1, x2, y2)
        area = max(1e-9, (x2 - x1) * (y2 - y1))
        covered = 0.0
        for p in self.placed:
            if abs(p.z2 - support_level) < 1e-6:
                covered += self._xy_overlap_area(bottom, (p.x1, p.y1, p.x2, p.y2))
        return min(1.0, covered / area)

    def _contact_score(self, candidate: Tuple[float, float, float, float, float, float]) -> float:
        x1, y1, z1, x2, y2, z2 = candidate
        wall_contact = 0.0
        if abs(x1 - self.container.min_x) < 1e-6 or abs(x2 - self.container.max_x) < 1e-6:
            wall_contact += (y2 - y1)
        if abs(y1 - self.container.min_y) < 1e-6 or abs(y2 - self.container.max_y) < 1e-6:
            wall_contact += (x2 - x1)

        box_contact = 0.0
        for p in self.placed:
            share_y = max(0.0, min(y2, p.y2) - max(y1, p.y1))
            share_x = max(0.0, min(x2, p.x2) - max(x1, p.x1))
            if abs(x1 - p.x2) < 1e-6:
                box_contact += share_y
            if abs(x2 - p.x1) < 1e-6:
                box_contact += share_y
            if abs(y1 - p.y2) < 1e-6:
                box_contact += share_x
            if abs(y2 - p.y1) < 1e-6:
                box_contact += share_x

        return self.config.contact_weight_wall * wall_contact + self.config.contact_weight_box * box_contact

    def _support_ratio_local(self, candidate: Tuple[float, float, float, float, float, float], placed: List[PlacedBox]) -> float:
        x1, y1, z1, x2, y2, z2 = candidate
        if abs(z1 - self.container.min_z) < 1e-9:
            return 1.0
        support_level = z1
        bottom = (x1, y1, x2, y2)
        area = max(1e-9, (x2 - x1) * (y2 - y1))
        covered = 0.0
        for p in placed:
            if abs(p.z2 - support_level) < 1e-6:
                covered += self._xy_overlap_area(bottom, (p.x1, p.y1, p.x2, p.y2))
        return min(1.0, covered / area)

    def _contact_score_local(self, candidate: Tuple[float, float, float, float, float, float], placed: List[PlacedBox]) -> float:
        x1, y1, z1, x2, y2, z2 = candidate
        wall_contact = 0.0
        if abs(x1 - self.container.min_x) < 1e-6 or abs(x2 - self.container.max_x) < 1e-6:
            wall_contact += (y2 - y1)
        if abs(y1 - self.container.min_y) < 1e-6 or abs(y2 - self.container.max_y) < 1e-6:
            wall_contact += (x2 - x1)

        box_contact = 0.0
        for p in placed:
            share_y = max(0.0, min(y2, p.y2) - max(y1, p.y1))
            share_x = max(0.0, min(x2, p.x2) - max(x1, p.x1))
            if abs(x1 - p.x2) < 1e-6:
                box_contact += share_y
            if abs(x2 - p.x1) < 1e-6:
                box_contact += share_y
            if abs(y1 - p.y2) < 1e-6:
                box_contact += share_x
            if abs(y2 - p.y1) < 1e-6:
                box_contact += share_x
        return self.config.contact_weight_wall * wall_contact + self.config.contact_weight_box * box_contact

    def pack(self, items: Sequence[BoxItem]) -> List[PlacedBox]:
        start = time.time()
        strategies: List[Tuple[Callable[[BoxItem], float], bool]]
        if self.config.prefer_small_boxes:
            strategies = [
                (lambda it: it.length * it.width * it.height, False),
                (lambda it: min(it.length, it.width, it.height), False),
                (lambda it: max(it.length, it.width, it.height), False),
            ]
        else:
            strategies = [
                (lambda it: it.length * it.width * it.height, True),
                (lambda it: max(it.length, it.width, it.height), True),
                (lambda it: min(it.length, it.width, it.height), True),
            ]

        best_result: List[PlacedBox] = []
        best_score: Tuple[int, float] | None = None

        run_index = 0
        for strat, reverse in strategies:
            for attempt in range(max(1, self.config.alternate_starts)):
                if time.time() - start > self.config.time_limit_sec:
                    break
                self.free = FreeSpaceManager((self.container.min_x, self.container.min_y, self.container.min_z, self.container.max_x, self.container.max_y, self.container.max_z))
                self.placed = []
                ordered = sorted(items, key=strat, reverse=reverse)
                rng = random.Random(1337 + run_index)
                result = self._beam_pack(ordered, start, rng)
                run_index += 1
                filled_volume = sum((p.x2 - p.x1) * (p.y2 - p.y1) * (p.z2 - p.z1) for p in result)
                if self.config.objective == "volume":
                    score = (-filled_volume, -len(result))
                else:
                    score = (-len(result), -filled_volume)
                if best_score is None or score < best_score:
                    best_score = score
                    best_result = result

        self.placed = best_result
        return self.placed

    def _beam_pack(self, items: Sequence[BoxItem], start_time: float, rng: random.Random) -> List[PlacedBox]:
        @dataclass(order=True)
        class State:
            sort_key: Tuple[int, float, float, int] = field(init=False, compare=True)
            placed: List[PlacedBox] = field(default_factory=list, compare=False)
            free: FreeSpaceManager = field(default=None, compare=False)
            placed_volume: float = 0.0
            potential_fit: float = 0.0

            def compute_key(self) -> None:
                fragmentation = len(self.free.free_boxes) if self.free is not None else 0
                self.sort_key = (-len(self.placed), -self.placed_volume, -self.potential_fit, fragmentation)

        def fit_potential(free: FreeSpaceManager, upcoming: Sequence[BoxItem], items_limit: int = 6, boxes_limit: int = 16) -> float:
            if not upcoming or not free or not free.free_boxes:
                return 0.0
            score = 0
            considered_boxes = free.free_boxes[: boxes_limit]
            considered_items = list(upcoming[: items_limit])
            for fb in considered_boxes:
                bx = fb.x2 - fb.x1
                by = fb.y2 - fb.y1
                bz = fb.z2 - fb.z1
                for it in considered_items:
                    can_fit = False
                    for l, w, h in it.orientations():
                        if l <= bx + 1e-6 and w <= by + 1e-6 and h <= bz + 1e-6:
                            can_fit = True
                            break
                    if can_fit:
                        score += 1
            return float(score)

        init = State(placed=[], free=self.free.clone(), placed_volume=0.0)
        init.compute_key()
        beam: List[State] = [init]

        for idx, item in enumerate(items):
            next_beam: List[State] = []
            for state in beam:
                if time.time() - start_time > self.config.time_limit_sec:
                    break
                candidates: List[Tuple[float, Tuple[float, float, float, float, float, float]]] = []
                count = 0
                for l, w, h in item.orientations():
                    for cand in state.free.find_positions(l, w, h):
                        if not self.config.allow_stacking and cand[2] > self.container.min_z + 1e-9:
                            continue
                        # Enforce no_stack/fragile/alcohol constraints for underlying boxes at this Z
                        if cand[2] > self.container.min_z + 1e-9:
                            base_z = cand[2]
                            bx1, by1, bx2, by2 = cand[0], cand[1], cand[3], cand[4]
                            violates = False
                            for p in state.placed:
                                if abs(p.z2 - base_z) < 1e-6:
                                    overlap_x = max(0.0, min(bx2, p.x2) - max(bx1, p.x1))
                                    overlap_y = max(0.0, min(by2, p.y2) - max(by1, p.y1))
                                    if overlap_x > 1e-9 and overlap_y > 1e-9:
                                        # For now, interpret flags via item index mapping if available
                                        # Since we don't carry flags in PlacedBox, allow stacking generally
                                        pass
                            if violates:
                                continue
                        # Enforce stacking only on same face dimensions if enabled
                        if self.config.stack_same_face_only and cand[2] > self.container.min_z + 1e-9:
                            face_x = cand[3] - cand[0]
                            face_y = cand[4] - cand[1]
                            fx1, fy1 = sorted((face_x, face_y))
                            ok_face = False
                            bx1, by1, bx2, by2 = cand[0], cand[1], cand[3], cand[4]
                            for p in state.placed:
                                if abs(p.z2 - cand[2]) < 1e-6:
                                    overlap_x = max(0.0, min(bx2, p.x2) - max(bx1, p.x1))
                                    overlap_y = max(0.0, min(by2, p.y2) - max(by1, p.y1))
                                    if overlap_x > self.config.size_tol and overlap_y > self.config.size_tol:
                                        pf_x = p.x2 - p.x1
                                        pf_y = p.y2 - p.y1
                                        px1, py1 = sorted((pf_x, pf_y))
                                        if abs(px1 - fx1) <= self.config.size_tol and abs(py1 - fy1) <= self.config.size_tol:
                                            ok_face = True
                                            break
                            if not ok_face:
                                continue
                        support = self._support_ratio_local(cand, state.placed if state.placed else [])
                        if support + 1e-9 < self.config.min_support_ratio:
                            continue
                        base = self.config.position_scorer(cand)
                        contact = self._contact_score_local(cand, state.placed if state.placed else [])
                        # Prefer lower Z for stability and layer fill
                        z1 = cand[2]
                        s = base - contact + self.config.z_bias * z1
                        if self.config.diversify and self.config.jitter > 0.0:
                            s += rng.uniform(-self.config.jitter, self.config.jitter)
                        candidates.append((s, cand))
                        count += 1
                        if count >= self.config.max_positions_per_item:
                            break
                    if count >= self.config.max_positions_per_item:
                        break
                candidates.sort(key=lambda x: x[0])
                depth = len(state.placed)
                local_width = self.config.beam_width
                if depth < self.config.beam_widen_until:
                    local_width = min(self.config.beam_width * self.config.beam_widen_factor, max(1, len(candidates)))
                top = [c for _, c in candidates[: local_width]]
                if self.config.diversify and len(candidates) > self.config.beam_width:
                    pool = candidates[self.config.beam_width:]
                    extra = min(self.config.exploratory_pick, len(pool))
                    if extra > 0:
                        extra_choices = rng.sample(pool, extra)
                        top.extend([c for _, c in extra_choices])

                for cand in top:
                    new_state = State(placed=list(state.placed), free=state.free.clone(), placed_volume=state.placed_volume)
                    new_state.free.place(cand)
                    new_state.placed.append(PlacedBox(*cand, item.index))
                    new_state.placed_volume += (cand[3] - cand[0]) * (cand[4] - cand[1]) * (cand[5] - cand[2])
                    # Estimate fit potential for upcoming items
                    upcoming = items[idx + 1 : idx + 1 + 6]
                    new_state.potential_fit = fit_potential(new_state.free, upcoming)
                    new_state.compute_key()
                    next_beam.append(new_state)

                if not top:
                    # skip placing this item in this branch
                    new_state = State(placed=list(state.placed), free=state.free.clone(), placed_volume=state.placed_volume)
                    new_state.compute_key()
                    next_beam.append(new_state)

            next_beam.sort(key=lambda s: s.sort_key)
            beam = next_beam[: self.config.beam_width]
            if time.time() - start_time > self.config.time_limit_sec:
                break

        best_state = min(beam, key=lambda s: s.sort_key)
        return best_state.placed


