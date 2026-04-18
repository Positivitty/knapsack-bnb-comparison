from knapsack.item import Item, Instance
from knapsack.bounds import upper_bound


def test_bound_empty_remaining():
    inst = Instance.from_items([Item(4, 10), Item(6, 12)], capacity=10)
    assert upper_bound(inst, level=2, weight=10, value=22) == 22


def test_bound_over_capacity_returns_neg_infinity():
    inst = Instance.from_items([Item(4, 10)], capacity=3)
    assert upper_bound(inst, level=0, weight=5, value=0) == float("-inf")


def test_bound_takes_full_items_then_fraction():
    inst = Instance.from_items(
        [Item(2, 10), Item(4, 12), Item(6, 6)], capacity=8
    )
    assert upper_bound(inst, level=0, weight=0, value=0) == 24.0


def test_bound_stops_when_capacity_full():
    inst = Instance.from_items([Item(5, 10), Item(5, 10)], capacity=5)
    assert upper_bound(inst, level=0, weight=0, value=0) == 10.0
