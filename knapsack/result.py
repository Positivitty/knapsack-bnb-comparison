from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Result:
    best_value: int
    taken_mask: list[bool]
    nodes_expanded: int
    peak_frontier_size: int
    timed_out: bool
