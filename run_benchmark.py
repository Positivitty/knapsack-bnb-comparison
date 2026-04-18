from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from tabulate import tabulate

from benchmark.fixture import run_sweep, write_csv
from benchmark.plot import plot_nodes, plot_runtime


def _parse_sizes(value: str) -> list[int]:
    return [int(s) for s in value.split(",") if s.strip()]


def _summary_table(rows) -> str:
    by_key: dict[tuple[int, str], list] = {}
    for r in rows:
        by_key.setdefault((r.size, r.algo), []).append(r)

    headers = ["size", "algo", "mean_runtime_s", "mean_nodes", "peak_frontier", "timeouts"]
    table = []
    for (size, algo), group in sorted(by_key.items()):
        mean_rt = sum(r.runtime_s for r in group) / len(group)
        mean_nodes = sum(r.nodes_expanded for r in group) / len(group)
        peak = max(r.peak_frontier for r in group)
        timeouts = sum(1 for r in group if r.timed_out)
        table.append([size, algo, f"{mean_rt:.4f}", f"{mean_nodes:.1f}", peak, timeouts])
    return tabulate(table, headers=headers, tablefmt="github")


def main() -> None:
    parser = argparse.ArgumentParser(description="Knapsack B&B benchmark sweep")
    parser.add_argument(
        "--sizes",
        type=_parse_sizes,
        default=[10, 15, 20, 25, 30, 35, 40],
        help="Comma-separated item counts",
    )
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()

    print(
        f"Running sweep: sizes={args.sizes} trials={args.trials} "
        f"timeout={args.timeout}s seed={args.seed}"
    )
    rows = run_sweep(
        sizes=args.sizes,
        trials=args.trials,
        timeout_s=args.timeout,
        base_seed=args.seed,
    )

    stamp = date.today().isoformat()
    csv_path = args.out / f"benchmark_{stamp}.csv"
    write_csv(rows, csv_path)
    print(f"Wrote CSV: {csv_path}")

    plot_runtime(rows, args.out / "runtime_vs_size.png")
    plot_nodes(rows, args.out / "nodes_vs_size.png")
    print(f"Wrote plots: {args.out}/runtime_vs_size.png, {args.out}/nodes_vs_size.png")

    print()
    print(_summary_table(rows))


if __name__ == "__main__":
    main()
