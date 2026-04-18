from __future__ import annotations

import csv
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

from benchmark.generate import make_instance
from knapsack.best_first_bnb import solve_best_first
from knapsack.fifo_bnb import solve_fifo
from knapsack.item import Instance
from knapsack.result import Result


@dataclass
class BenchmarkRow:
    size: int
    trial: int
    seed: int
    algo: str
    runtime_s: float
    best_value: int
    nodes_expanded: int
    peak_frontier: int
    timed_out: bool


_SOLVERS: dict[str, Callable[[Instance, float | None], Result]] = {
    "fifo": solve_fifo,
    "best_first": solve_best_first,
}


def _time_solver(
    solver: Callable[[Instance, float | None], Result],
    inst: Instance,
    timeout_s: float,
) -> tuple[Result, float]:
    start = time.perf_counter()
    result = solver(inst, timeout_s)
    elapsed = time.perf_counter() - start
    return result, elapsed


def run_sweep(
    sizes: Iterable[int],
    trials: int,
    timeout_s: float,
    base_seed: int,
) -> list[BenchmarkRow]:
    rows: list[BenchmarkRow] = []
    for size in sizes:
        for trial in range(trials):
            seed = base_seed + size * 100 + trial
            inst = make_instance(n=size, seed=seed)
            for algo, solver in _SOLVERS.items():
                result, elapsed = _time_solver(solver, inst, timeout_s)
                rows.append(
                    BenchmarkRow(
                        size=size,
                        trial=trial,
                        seed=seed,
                        algo=algo,
                        runtime_s=elapsed,
                        best_value=result.best_value,
                        nodes_expanded=result.nodes_expanded,
                        peak_frontier=result.peak_frontier_size,
                        timed_out=result.timed_out,
                    )
                )
    return rows


def write_csv(rows: list[BenchmarkRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys())
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
