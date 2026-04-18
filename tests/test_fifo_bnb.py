from knapsack.item import Item, Instance
from knapsack.fifo_bnb import solve_fifo


def test_fifo_tiny_instance():
    inst = Instance.from_items(
        [Item(2, 10), Item(4, 12), Item(6, 6)], capacity=8
    )
    result = solve_fifo(inst)
    assert result.best_value == 22
    assert result.timed_out is False
    assert result.nodes_expanded > 0
    assert result.peak_frontier_size > 0


def test_fifo_zero_capacity():
    inst = Instance.from_items([Item(1, 5), Item(2, 10)], capacity=0)
    result = solve_fifo(inst)
    assert result.best_value == 0
    assert result.taken_mask == [False, False]


def test_fifo_single_item_fits():
    inst = Instance.from_items([Item(3, 7)], capacity=5)
    result = solve_fifo(inst)
    assert result.best_value == 7
    assert result.taken_mask == [True]


def test_fifo_mask_reconstructs_value():
    inst = Instance.from_items(
        [Item(2, 10), Item(4, 12), Item(6, 6), Item(3, 5)], capacity=9
    )
    result = solve_fifo(inst)
    reconstructed = sum(
        it.value for it, taken in zip(inst.items, result.taken_mask) if taken
    )
    reconstructed_weight = sum(
        it.weight for it, taken in zip(inst.items, result.taken_mask) if taken
    )
    assert reconstructed == result.best_value
    assert reconstructed_weight <= inst.capacity
