from knapsack.item import Item, Instance


def test_item_ratio():
    item = Item(weight=4, value=10)
    assert item.ratio == 2.5


def test_instance_sorts_by_ratio_descending():
    raw = [Item(weight=10, value=10), Item(weight=2, value=10), Item(weight=5, value=10)]
    inst = Instance.from_items(raw, capacity=15)
    assert [it.weight for it in inst.items] == [2, 5, 10]
    assert inst.capacity == 15
    assert inst.n == 3
