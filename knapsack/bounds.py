from __future__ import annotations

from knapsack.item import Instance


def upper_bound(inst: Instance, level: int, weight: int, value: int) -> float:
    """Fractional-relaxation upper bound for 0/1 Knapsack.

    Items in ``inst`` are assumed sorted by value/weight ratio descending.
    Walks items from ``level`` forward, taking whole items while they fit,
    then a fractional slice of the next item to fill remaining capacity.
    """
    if weight > inst.capacity:
        return float("-inf")

    bound = float(value)
    remaining = inst.capacity - weight

    for i in range(level, inst.n):
        item = inst.items[i]
        if item.weight <= remaining:
            bound += item.value
            remaining -= item.weight
        else:
            bound += item.value * (remaining / item.weight)
            break

    return bound
