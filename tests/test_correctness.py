import random
from itertools import product

import pytest

from knapsack.best_first_bnb import solve_best_first
from knapsack.fifo_bnb import solve_fifo
from knapsack.item import Item, Instance


def brute_force(inst: Instance) -> int:
    best = 0
    for mask in product((False, True), repeat=inst.n):
        w = sum(it.weight for it, take in zip(inst.items, mask) if take)
        v = sum(it.value for it, take in zip(inst.items, mask) if take)
        if w <= inst.capacity and v > best:
            best = v
    return best


def _random_instance(n: int, seed: int) -> Instance:
    rng = random.Random(seed)
    items = [Item(weight=rng.randint(1, 100), value=rng.randint(1, 100)) for _ in range(n)]
    total_weight = sum(it.weight for it in items)
    capacity = total_weight // 2
    return Instance.from_items(items, capacity=capacity)


@pytest.mark.parametrize("n", [5, 10, 12])
@pytest.mark.parametrize("trial", range(10))
def test_both_algos_match_brute_force(n, trial):
    inst = _random_instance(n, seed=1000 * n + trial)
    expected = brute_force(inst)

    fifo = solve_fifo(inst)
    best_first = solve_best_first(inst)

    assert fifo.best_value == expected, f"FIFO mismatch n={n} trial={trial}"
    assert best_first.best_value == expected, f"Best-first mismatch n={n} trial={trial}"

    for name, result in (("fifo", fifo), ("best_first", best_first)):
        w = sum(it.weight for it, take in zip(inst.items, result.taken_mask) if take)
        v = sum(it.value for it, take in zip(inst.items, result.taken_mask) if take)
        assert v == result.best_value, f"{name} mask value mismatch"
        assert w <= inst.capacity, f"{name} mask exceeds capacity"
