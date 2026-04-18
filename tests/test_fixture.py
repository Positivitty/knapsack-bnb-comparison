from benchmark.fixture import run_sweep, BenchmarkRow


def test_run_sweep_produces_expected_row_count():
    rows = run_sweep(sizes=[8, 10], trials=2, timeout_s=10.0, base_seed=1)
    assert len(rows) == 8
    assert all(isinstance(r, BenchmarkRow) for r in rows)


def test_run_sweep_covers_both_algorithms():
    rows = run_sweep(sizes=[8], trials=1, timeout_s=10.0, base_seed=1)
    algos = {r.algo for r in rows}
    assert algos == {"fifo", "best_first"}


def test_run_sweep_matches_values_on_same_instance():
    rows = run_sweep(sizes=[8, 10], trials=2, timeout_s=10.0, base_seed=1)
    by_key: dict[tuple[int, int], dict[str, int]] = {}
    for r in rows:
        by_key.setdefault((r.size, r.trial), {})[r.algo] = r.best_value
    for pair in by_key.values():
        assert pair["fifo"] == pair["best_first"]
