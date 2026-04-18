from __future__ import annotations

import random

from knapsack.item import Instance, Item


def make_instance(n: int, seed: int) -> Instance:
    """Build a reproducible 0/1 knapsack instance.

    Each item's weight and value are drawn uniformly from [1, 100].
    Capacity is half of the total weight (integer floor).
    """
    rng = random.Random(seed)
    items = [Item(weight=rng.randint(1, 100), value=rng.randint(1, 100)) for _ in range(n)]
    capacity = sum(it.weight for it in items) // 2
    return Instance.from_items(items, capacity=capacity)
