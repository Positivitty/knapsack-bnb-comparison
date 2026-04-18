from knapsack.result import Result


def test_result_defaults():
    r = Result(
        best_value=0, taken_mask=[False, False, False], nodes_expanded=0,
        peak_frontier_size=0, timed_out=False,
    )
    assert r.best_value == 0
    assert r.taken_mask == [False, False, False]
    assert r.timed_out is False


def test_result_is_mutable_on_fields_we_need():
    r = Result(
        best_value=0, taken_mask=[False], nodes_expanded=0,
        peak_frontier_size=0, timed_out=False,
    )
    r.best_value = 42
    assert r.best_value == 42
