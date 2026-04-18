from benchmark.generate import make_instance


def test_make_instance_is_deterministic():
    a = make_instance(n=20, seed=42)
    b = make_instance(n=20, seed=42)
    assert [(it.weight, it.value) for it in a.items] == [
        (it.weight, it.value) for it in b.items
    ]
    assert a.capacity == b.capacity


def test_make_instance_capacity_is_half_of_total_weight():
    inst = make_instance(n=30, seed=7)
    total = sum(it.weight for it in inst.items)
    assert inst.capacity == total // 2


def test_make_instance_items_sorted_by_ratio_desc():
    inst = make_instance(n=15, seed=3)
    ratios = [it.ratio for it in inst.items]
    assert ratios == sorted(ratios, reverse=True)
