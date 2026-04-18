import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import matplotlib.pyplot as plt

from benchmark.fixture import BenchmarkRow


_ALGO_LABEL = {"fifo": "FIFO B&B", "best_first": "Best-First B&B"}
_ALGO_COLOR = {"fifo": "tab:red", "best_first": "tab:blue"}


def _aggregate(rows, metric):
    grouped = {}
    for row in rows:
        value = getattr(row, metric)
        grouped.setdefault(row.algo, {}).setdefault(row.size, []).append(float(value))

    agg = {}
    for algo, sizes in grouped.items():
        agg[algo] = {}
        for size, vals in sizes.items():
            mean = sum(vals) / len(vals)
            agg[algo][size] = (mean, min(vals), max(vals))
    return agg


def _plot_metric(rows, metric, ylabel, title, out_path):
    agg = _aggregate(rows, metric)

    fig, ax = plt.subplots(figsize=(8, 6))
    for algo, by_size in agg.items():
        sizes = sorted(by_size.keys())
        means = [by_size[s][0] for s in sizes]
        mins = [by_size[s][1] for s in sizes]
        maxs = [by_size[s][2] for s in sizes]
        color = _ALGO_COLOR[algo]
        label = _ALGO_LABEL[algo]
        ax.plot(sizes, means, marker="o", color=color, label=label)
        ax.fill_between(sizes, mins, maxs, color=color, alpha=0.15)

    ax.set_yscale("log")
    ax.set_xlabel("Number of items (n)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--")
    ax.legend()

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_runtime(rows, out_path):
    _plot_metric(
        rows,
        metric="runtime_s",
        ylabel="Runtime (seconds, log scale)",
        title="FIFO vs. Best-First B&B — Runtime",
        out_path=out_path,
    )


def plot_nodes(rows, out_path):
    _plot_metric(
        rows,
        metric="nodes_expanded",
        ylabel="Nodes expanded (log scale)",
        title="FIFO vs. Best-First B&B — Nodes Expanded",
        out_path=out_path,
    )
