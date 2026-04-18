# Knapsack Branch-and-Bound Comparison — Design

**Date:** 2026-04-18
**Status:** Draft — awaiting user review
**Assignment:** Compare two Branch-and-Bound variants on the 0/1 Knapsack problem, measure runtime and operation count, produce data showing a clear winner, and prepare research notes for a video walkthrough.

## 1. Goal

Build a self-contained Python project that:

1. Implements two Branch-and-Bound algorithms for 0/1 Knapsack — **FIFO B&B** (queue-based) and **Best-First B&B** (priority-queue / Least-Cost). Both share a single fractional-relaxation upper bound function so the comparison isolates the search strategy.
2. Runs both on identical, reproducibly-generated instances across a range of input sizes, multiple trials per size, with a per-run timeout.
3. Records runtime, nodes expanded, and peak frontier size for each run.
4. Produces a CSV of raw results plus two log-scale matplotlib charts (runtime vs. size, nodes vs. size).
5. Documents the research, prediction, and results in the README so the video walkthrough can use it as the script.

## 2. Non-Goals

- No GUI, no animation, no web front-end.
- No dynamic-programming or greedy baselines (outside the scope of the assignment).
- No tuning for maximum raw speed — both implementations should be idiomatic Python so the comparison is fair.
- No distributed execution.

## 3. Project Structure

```
~/Projects/knapsack-bnb-comparison/
├── README.md                  # research write-up: complexity, memory, prediction, results
├── requirements.txt           # matplotlib, tabulate, pytest
├── knapsack/
│   ├── __init__.py
│   ├── item.py                # Item dataclass (weight, value, ratio)
│   ├── bounds.py              # shared fractional-relaxation upper bound
│   ├── fifo_bnb.py            # FIFO (queue-based) B&B
│   └── best_first_bnb.py      # Least-Cost (priority-queue) B&B
├── benchmark/
│   ├── __init__.py
│   ├── generate.py            # reproducible random instances (seeded)
│   ├── fixture.py             # runs both algos across sizes, collects metrics
│   └── plot.py                # renders runtime + node-expansion charts
├── tests/
│   └── test_correctness.py    # brute-force parity on small inputs
├── results/                   # CSV + PNGs committed after runs
└── run_benchmark.py           # entry point
```

## 4. The Two Algorithms

Both consume an `Instance` (a list of `Item(weight, value)` sorted by value/weight ratio descending, plus a capacity) and return:

```python
Result(
    best_value: int,
    taken_mask: list[bool],       # which items were chosen
    nodes_expanded: int,          # ops counter
    peak_frontier_size: int,      # max live-node count during the run
    timed_out: bool,
)
```

### 4.1 Shared node representation

```python
Node(
    level: int,                   # index of next item to consider
    weight: int,                  # weight accumulated so far
    value: int,                   # value accumulated so far
    bound: float,                 # optimistic upper bound from this node
    taken_mask: tuple[bool, ...], # choices made so far (immutable for hashing if needed)
)
```

### 4.2 Shared bound function (`bounds.py`)

Fractional-knapsack relaxation on remaining items: walk forward from `level`, greedily add whole items in ratio order while they fit, then add a fractional slice of the next item to fill the remaining capacity. Returns the (possibly non-integer) upper bound.

### 4.3 FIFO B&B (`fifo_bnb.py`)

- Frontier: `collections.deque`.
- Expand the root, enqueue children (include / exclude the next item).
- Pop from the **front** of the deque.
- Prune a popped node when its stored bound ≤ best value found so far.
- Update `best_value` whenever a feasible leaf (level == n) beats it.
- Increment `nodes_expanded` each time a node is popped and expanded.
- Track `peak_frontier_size` as `max(peak, len(deque))` after each enqueue.

### 4.4 Best-First B&B (`best_first_bnb.py`)

- Frontier: `heapq` min-heap keyed on `-bound` (so the highest-bound node pops first).
- Same expansion and pruning rules as FIFO.
- Same counters.
- Tie-breaking: use a monotonically increasing sequence number as the second sort key to avoid comparing `Node` objects.

### 4.5 Early termination

Neither algorithm terminates early on "good enough" — both run until the frontier is empty (modulo timeout). This keeps the comparison of total work apples-to-apples.

## 5. Benchmark Fixture

### 5.1 Instance generation (`benchmark/generate.py`)

- Seeded RNG (`random.Random(seed)`).
- Weights: uniform int `[1, 100]`.
- Values: uniform int `[1, 100]`.
- Capacity: `floor(0.5 * sum(weights))` — the classic "hard" ratio where neither "take everything" nor "take nothing" is near-optimal.
- Items are sorted by value/weight ratio descending before being handed to the algorithms (required by the bound function).

### 5.2 Fixture loop (`benchmark/fixture.py`)

- Sizes: `[10, 15, 20, 25, 30, 35, 40]`.
- Trials per size: `5`, using seeds `size * 100 + trial_index` so runs are reproducible.
- Per-run timeout: `60` seconds. Implementation: pass a `deadline = time.perf_counter() + timeout` into the algorithm; the main loop checks it once per pop. On timeout, return `Result(..., timed_out=True)` with whatever best-so-far and counters we have.
- For each `(size, trial)`:
  1. Generate instance.
  2. Run FIFO B&B, time with `time.perf_counter()`.
  3. Run Best-First B&B on the same instance, time it.
  4. If neither timed out, assert `fifo.best_value == best_first.best_value`. If one timed out, skip the assertion (partial result).
  5. Append two rows to the results list (one per algorithm).
- Write CSV to `results/benchmark_YYYY-MM-DD.csv` with columns:
  `size, trial, seed, algo, runtime_s, best_value, nodes_expanded, peak_frontier, timed_out`.

### 5.3 Plots (`benchmark/plot.py`)

Two PNGs, both with log-scale y-axis and linear x-axis (item count):

1. **`runtime_vs_size.png`** — one line per algorithm (mean across trials), shaded min-max band.
2. **`nodes_vs_size.png`** — same format, showing operation count.

Timed-out runs render as open markers at the timeout value so they're visually distinct.

## 6. Correctness Testing (`tests/test_correctness.py`)

- For N in `[5, 10, 12]`, generate 10 random instances per size.
- Brute-force the optimum by iterating all `2^N` subsets.
- Assert `fifo_bnb(instance).best_value == brute_force == best_first_bnb(instance).best_value`.
- Also assert both `taken_mask` results yield the reported `best_value` when applied to the instance (guards against off-by-one on which mask is returned).
- pytest, single file, no mocks.

## 7. Research Write-Up (README.md)

Structure:

1. **Problem statement** — 0/1 Knapsack, NP-hard, why B&B is the standard exact approach.
2. **Algorithm 1: FIFO B&B** — how it works, pseudocode, complexity.
3. **Algorithm 2: Best-First (LC) B&B** — same treatment.
4. **Comparison table (pre-run prediction):**

   | | FIFO B&B | Best-First B&B |
   |---|---|---|
   | Frontier structure | Queue (deque) | Min-heap (priority queue) |
   | Per-node op cost | O(1) enqueue/dequeue | O(log n) push/pop |
   | Worst-case nodes | O(2^n) | O(2^n) |
   | Expected nodes in practice | Much larger — breadth-first, no guidance toward good solutions | Much smaller — always expands the most promising node first, so best-value rises quickly and prunes more aggressively |
   | Peak frontier | Up to full level-width of the tree | Bounded by live nodes with bound > best_so_far |
   | Strength | Simple; cache-friendly | Finds good feasible solutions fast, enabling aggressive pruning |

5. **Prediction:** Best-First wins decisively on runtime, and the gap widens with N. FIFO's per-op cost is cheaper, but it explores orders of magnitude more nodes, so Best-First wins overall. Memory: both O(2^n) worst case, but Best-First's measured peak frontier is typically smaller because pruning kicks in sooner.
6. **Results:** embed both PNGs and a summary table aggregated from the CSV.
7. **Conclusion:** which won, by how much, and whether the prediction held.

## 8. Dependencies

```
matplotlib>=3.7
tabulate>=0.9
pytest>=7
```

Standard library: `collections.deque`, `heapq`, `dataclasses`, `random`, `time.perf_counter`, `csv`, `argparse`.

## 9. Entry Point (`run_benchmark.py`)

CLI flags:
- `--sizes 10,15,20,25,30,35,40` (override sweep)
- `--trials 5`
- `--timeout 60`
- `--seed 42` (base seed)
- `--out results/` (output directory)

Default invocation `python run_benchmark.py` runs the full sweep, writes CSV + PNGs, and prints a summary table to stdout.

## 10. Open Questions

None at spec time. Anything discovered during implementation (e.g., a size that makes FIFO always time out) will be resolved by adjusting sweep bounds in the fixture rather than by changing the algorithms.
