from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from knapsack.bounds import upper_bound
from knapsack.item import Instance
from knapsack.result import Result


@dataclass(frozen=True)
class _Node:
    level: int
    weight: int
    value: int
    bound: float
    taken: tuple[bool, ...]


def solve_fifo(inst: Instance, timeout_s: float | None = None) -> Result:
    """FIFO Branch-and-Bound for 0/1 Knapsack.

    Frontier is a deque; nodes are popped in insertion order (FIFO).
    """
    n = inst.n
    deadline = None if timeout_s is None else time.perf_counter() + timeout_s

    root = _Node(
        level=0,
        weight=0,
        value=0,
        bound=upper_bound(inst, 0, 0, 0),
        taken=tuple([False] * n),
    )
    frontier: deque[_Node] = deque([root])
    best_value = 0
    best_mask: tuple[bool, ...] = tuple([False] * n)
    nodes_expanded = 0
    peak_frontier = 1
    timed_out = False

    while frontier:
        if deadline is not None and time.perf_counter() >= deadline:
            timed_out = True
            break

        node = frontier.popleft()
        nodes_expanded += 1

        if node.bound <= best_value:
            continue
        if node.level == n:
            continue

        item = inst.items[node.level]

        # Include branch (if it fits)
        if node.weight + item.weight <= inst.capacity:
            inc_weight = node.weight + item.weight
            inc_value = node.value + item.value
            inc_taken = node.taken[: node.level] + (True,) + node.taken[node.level + 1 :]
            if inc_value > best_value:
                best_value = inc_value
                best_mask = inc_taken
            inc_bound = upper_bound(inst, node.level + 1, inc_weight, inc_value)
            if inc_bound > best_value:
                frontier.append(
                    _Node(
                        level=node.level + 1,
                        weight=inc_weight,
                        value=inc_value,
                        bound=inc_bound,
                        taken=inc_taken,
                    )
                )

        # Exclude branch (always feasible)
        exc_bound = upper_bound(inst, node.level + 1, node.weight, node.value)
        if exc_bound > best_value:
            exc_taken = node.taken[: node.level] + (False,) + node.taken[node.level + 1 :]
            frontier.append(
                _Node(
                    level=node.level + 1,
                    weight=node.weight,
                    value=node.value,
                    bound=exc_bound,
                    taken=exc_taken,
                )
            )

        if len(frontier) > peak_frontier:
            peak_frontier = len(frontier)

    return Result(
        best_value=best_value,
        taken_mask=list(best_mask),
        nodes_expanded=nodes_expanded,
        peak_frontier_size=peak_frontier,
        timed_out=timed_out,
    )
