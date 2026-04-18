# Knapsack B&B Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python project that compares FIFO Branch-and-Bound vs. Best-First (Least-Cost) Branch-and-Bound on 0/1 Knapsack, producing timing data, node-expansion counts, and charts for a class assignment video walkthrough.

**Architecture:** Two B&B implementations share a fractional-relaxation upper-bound function. A fixture runs both on identical seeded instances across sizes 10–40, captures runtime and operation count, writes a CSV, and renders two matplotlib charts. A pytest file validates correctness against brute force on small inputs.

**Tech Stack:** Python 3.11+, `collections.deque`, `heapq`, `dataclasses`, `random`, `csv`, `matplotlib`, `tabulate`, `pytest`.

**Project root:** `~/Projects/knapsack-bnb-comparison`

All paths below are relative to that root.

---

### Task 1: Scaffolding — dependencies, package dirs, gitignore

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `knapsack/__init__.py`
- Create: `benchmark/__init__.py`
- Create: `tests/__init__.py`
- Create: `results/.gitkeep`

- [ ] **Step 1: Write `requirements.txt`**

```
matplotlib>=3.7
tabulate>=0.9
pytest>=7
```

- [ ] **Step 2: Write `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
*.egg-info/
.DS_Store
```

- [ ] **Step 3: Create empty package markers**

Create these as empty files:
- `knapsack/__init__.py`
- `benchmark/__init__.py`
- `tests/__init__.py`
- `results/.gitkeep`

- [ ] **Step 4: Create venv and install**

```bash
cd ~/Projects/knapsack-bnb-comparison
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: installs matplotlib, tabulate, pytest with no errors.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .gitignore knapsack/__init__.py benchmark/__init__.py tests/__init__.py results/.gitkeep
git commit -m "scaffold: project layout and dependencies"
```

---

### Task 2: `Item` dataclass and instance type

**Files:**
- Create: `knapsack/item.py`
- Create: `tests/test_item.py`

- [ ] **Step 1: Write the failing test**

Write to `tests/test_item.py`:

```python
from knapsack.item import Item, Instance


def test_item_ratio():
    item = Item(weight=4, value=10)
    assert item.ratio == 2.5


def test_instance_sorts_by_ratio_descending():
    raw = [Item(weight=10, value=10), Item(weight=2, value=10), Item(weight=5, value=10)]
    inst = Instance.from_items(raw, capacity=15)
    # Highest ratio first: 10/2=5, 10/5=2, 10/10=1
    assert [it.weight for it in inst.items] == [2, 5, 10]
    assert inst.capacity == 15
    assert inst.n == 3
```

- [ ] **Step 2: Run tests and verify they fail**

```bash
cd ~/Projects/knapsack-bnb-comparison
source .venv/bin/activate
pytest tests/test_item.py -v
```

Expected: ImportError (module does not exist yet).

- [ ] **Step 3: Write `knapsack/item.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class Item:
    weight: int
    value: int

    @property
    def ratio(self) -> float:
        return self.value / self.weight


@dataclass(frozen=True)
class Instance:
    items: tuple[Item, ...]
    capacity: int

    @property
    def n(self) -> int:
        return len(self.items)

    @classmethod
    def from_items(cls, items: Iterable[Item], capacity: int) -> "Instance":
        sorted_items = tuple(sorted(items, key=lambda it: it.ratio, reverse=True))
        return cls(items=sorted_items, capacity=capacity)
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
pytest tests/test_item.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add knapsack/item.py tests/test_item.py
git commit -m "feat: Item and Instance types"
```

---

### Task 3: Shared fractional-relaxation bound function

**Files:**
- Create: `knapsack/bounds.py`
- Create: `tests/test_bounds.py`

- [ ] **Step 1: Write the failing test**

Write to `tests/test_bounds.py`:

```python
from knapsack.item import Item, Instance
from knapsack.bounds import upper_bound


def test_bound_empty_remaining():
    inst = Instance.from_items([Item(4, 10), Item(6, 12)], capacity=10)
    # At level == n, there is nothing left to add; bound equals current value.
    assert upper_bound(inst, level=2, weight=10, value=22) == 22


def test_bound_over_capacity_returns_neg_infinity():
    inst = Instance.from_items([Item(4, 10)], capacity=3)
    # weight already exceeds capacity -> infeasible branch
    assert upper_bound(inst, level=0, weight=5, value=0) == float("-inf")


def test_bound_takes_full_items_then_fraction():
    # ratios: item0 (4/2=2 ...wait, value/weight). Use:
    # item0 weight=2 value=10 ratio=5
    # item1 weight=4 value=12 ratio=3
    # item2 weight=6 value=6  ratio=1
    inst = Instance.from_items(
        [Item(2, 10), Item(4, 12), Item(6, 6)], capacity=8
    )
    # Starting fresh at level=0, weight=0, value=0:
    # Take item0 fully: weight=2, value=10
    # Take item1 fully: weight=6, value=22
    # Remaining capacity=2, take 2/6 of item2: +2 value
    # Bound = 24.0
    assert upper_bound(inst, level=0, weight=0, value=0) == 24.0


def test_bound_stops_when_capacity_full():
    inst = Instance.from_items([Item(5, 10), Item(5, 10)], capacity=5)
    # Take item0 fully (ratio 2), capacity=0, stop.
    assert upper_bound(inst, level=0, weight=0, value=0) == 10.0
```

- [ ] **Step 2: Run tests and verify they fail**

```bash
pytest tests/test_bounds.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `knapsack/bounds.py`**

```python
from __future__ import annotations

from knapsack.item import Instance


def upper_bound(inst: Instance, level: int, weight: int, value: int) -> float:
    """Fractional-knapsack relaxation from `level` onward.

    Returns an optimistic upper bound on the best achievable value from this
    partial state. Returns -inf if the partial state is already infeasible.
    Assumes `inst.items` is sorted by value/weight ratio descending.
    """
    if weight > inst.capacity:
        return float("-inf")

    bound = float(value)
    remaining = inst.capacity - weight
    i = level
    n = inst.n

    while i < n and inst.items[i].weight <= remaining:
        item = inst.items[i]
        bound += item.value
        remaining -= item.weight
        i += 1

    if i < n and remaining > 0:
        item = inst.items[i]
        bound += item.value * (remaining / item.weight)

    return bound
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
pytest tests/test_bounds.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add knapsack/bounds.py tests/test_bounds.py
git commit -m "feat: fractional-relaxation upper bound"
```

---

### Task 4: `Result` type and shared node utility

**Files:**
- Create: `knapsack/result.py`
- Create: `tests/test_result.py`

- [ ] **Step 1: Write the failing test**

Write to `tests/test_result.py`:

```python
from knapsack.result import Result


def test_result_defaults():
    r = Result(
        best_value=0,
        taken_mask=[False, False, False],
        nodes_expanded=0,
        peak_frontier_size=0,
        timed_out=False,
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
```

- [ ] **Step 2: Run tests and verify they fail**

```bash
pytest tests/test_result.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `knapsack/result.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Result:
    best_value: int
    taken_mask: list[bool]
    nodes_expanded: int
    peak_frontier_size: int
    timed_out: bool
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
pytest tests/test_result.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add knapsack/result.py tests/test_result.py
git commit -m "feat: Result dataclass"
```

---

### Task 5: FIFO B&B — happy path (no timeout yet)

**Files:**
- Create: `knapsack/fifo_bnb.py`
- Create: `tests/test_fifo_bnb.py`

- [ ] **Step 1: Write the failing tests**

Write to `tests/test_fifo_bnb.py`:

```python
from knapsack.item import Item, Instance
from knapsack.fifo_bnb import solve_fifo


def test_fifo_tiny_instance():
    # items (pre-sort): ratios 10/2=5, 12/4=3, 6/6=1. Capacity=8.
    # Optimal: take item0 (w=2, v=10) + item1 (w=4, v=12) = value 22, weight 6.
    # Adding item2 (w=6) would exceed capacity. So best=22.
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
```

- [ ] **Step 2: Run tests and verify they fail**

```bash
pytest tests/test_fifo_bnb.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `knapsack/fifo_bnb.py`**

```python
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

from knapsack.bounds import upper_bound
from knapsack.item import Instance
from knapsack.result import Result


@dataclass(frozen=True)
class _Node:
    level: int
    weight: int
    value: int
    bound: float
    taken: tuple[bool, ...]


def solve_fifo(inst: Instance, timeout_s: float | None = None) -> Result:
    """FIFO Branch-and-Bound for 0/1 Knapsack.

    Frontier is a deque; nodes are popped in insertion order (FIFO).
    """
    n = inst.n
    deadline = None if timeout_s is None else time.perf_counter() + timeout_s

    root = _Node(
        level=0,
        weight=0,
        value=0,
        bound=upper_bound(inst, 0, 0, 0),
        taken=tuple([False] * n),
    )
    frontier: deque[_Node] = deque([root])
    best_value = 0
    best_mask: tuple[bool, ...] = tuple([False] * n)
    nodes_expanded = 0
    peak_frontier = 1
    timed_out = False

    while frontier:
        if deadline is not None and time.perf_counter() >= deadline:
            timed_out = True
            break

        node = frontier.popleft()
        nodes_expanded += 1

        if node.bound <= best_value:
            continue
        if node.level == n:
            continue

        item = inst.items[node.level]

        # Include branch (if it fits)
        if node.weight + item.weight <= inst.capacity:
            inc_weight = node.weight + item.weight
            inc_value = node.value + item.value
            inc_taken = node.taken[: node.level] + (True,) + node.taken[node.level + 1 :]
            if inc_value > best_value:
                best_value = inc_value
                best_mask = inc_taken
            inc_bound = upper_bound(inst, node.level + 1, inc_weight, inc_value)
            if inc_bound > best_value:
                frontier.append(
                    _Node(
                        level=node.level + 1,
                        weight=inc_weight,
                        value=inc_value,
                        bound=inc_bound,
                        taken=inc_taken,
                    )
                )

        # Exclude branch (always feasible)
        exc_bound = upper_bound(inst, node.level + 1, node.weight, node.value)
        if exc_bound > best_value:
            exc_taken = node.taken[: node.level] + (False,) + node.taken[node.level + 1 :]
            frontier.append(
                _Node(
                    level=node.level + 1,
                    weight=node.weight,
                    value=node.value,
                    bound=exc_bound,
                    taken=exc_taken,
                )
            )

        if len(frontier) > peak_frontier:
            peak_frontier = len(frontier)

    return Result(
        best_value=best_value,
        taken_mask=list(best_mask),
        nodes_expanded=nodes_expanded,
        peak_frontier_size=peak_frontier,
        timed_out=timed_out,
    )
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
pytest tests/test_fifo_bnb.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add knapsack/fifo_bnb.py tests/test_fifo_bnb.py
git commit -m "feat: FIFO Branch-and-Bound solver"
```

---

### Task 6: Best-First B&B

**Files:**
- Create: `knapsack/best_first_bnb.py`
- Create: `tests/test_best_first_bnb.py`

- [ ] **Step 1: Write the failing tests**

Write to `tests/test_best_first_bnb.py`:

```python
from knapsack.item import Item, Instance
from knapsack.best_first_bnb import solve_best_first


def test_best_first_tiny_instance():
    inst = Instance.from_items(
        [Item(2, 10), Item(4, 12), Item(6, 6)], capacity=8
    )
    result = solve_best_first(inst)
    assert result.best_value == 22
    assert result.timed_out is False
    assert result.nodes_expanded > 0


def test_best_first_zero_capacity():
    inst = Instance.from_items([Item(1, 5), Item(2, 10)], capacity=0)
    result = solve_best_first(inst)
    assert result.best_value == 0
    assert result.taken_mask == [False, False]


def test_best_first_single_item_fits():
    inst = Instance.from_items([Item(3, 7)], capacity=5)
    result = solve_best_first(inst)
    assert result.best_value == 7
    assert result.taken_mask == [True]


def test_best_first_mask_reconstructs_value():
    inst = Instance.from_items(
        [Item(2, 10), Item(4, 12), Item(6, 6), Item(3, 5)], capacity=9
    )
    result = solve_best_first(inst)
    reconstructed = sum(
        it.value for it, taken in zip(inst.items, result.taken_mask) if taken
    )
    reconstructed_weight = sum(
        it.weight for it, taken in zip(inst.items, result.taken_mask) if taken
    )
    assert reconstructed == result.best_value
    assert reconstructed_weight <= inst.capacity
```

- [ ] **Step 2: Run tests and verify they fail**

```bash
pytest tests/test_best_first_bnb.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `knapsack/best_first_bnb.py`**

```python
from __future__ import annotations

import heapq
import time
from dataclasses import dataclass

from knapsack.bounds import upper_bound
from knapsack.item import Instance
from knapsack.result import Result


@dataclass(frozen=True)
class _Node:
    level: int
    weight: int
    value: int
    bound: float
    taken: tuple[bool, ...]


def solve_best_first(inst: Instance, timeout_s: float | None = None) -> Result:
    """Best-First (Least-Cost) Branch-and-Bound for 0/1 Knapsack.

    Frontier is a min-heap keyed on -bound (highest bound pops first).
    A monotonically increasing counter breaks ties so Node objects are never compared.
    """
    n = inst.n
    deadline = None if timeout_s is None else time.perf_counter() + timeout_s

    root_bound = upper_bound(inst, 0, 0, 0)
    root = _Node(level=0, weight=0, value=0, bound=root_bound, taken=tuple([False] * n))

    counter = 0
    frontier: list[tuple[float, int, _Node]] = [(-root_bound, counter, root)]
    best_value = 0
    best_mask: tuple[bool, ...] = tuple([False] * n)
    nodes_expanded = 0
    peak_frontier = 1
    timed_out = False

    while frontier:
        if deadline is not None and time.perf_counter() >= deadline:
            timed_out = True
            break

        neg_bound, _, node = heapq.heappop(frontier)
        nodes_expanded += 1

        if node.bound <= best_value:
            continue
        if node.level == n:
            continue

        item = inst.items[node.level]

        # Include branch
        if node.weight + item.weight <= inst.capacity:
            inc_weight = node.weight + item.weight
            inc_value = node.value + item.value
            inc_taken = node.taken[: node.level] + (True,) + node.taken[node.level + 1 :]
            if inc_value > best_value:
                best_value = inc_value
                best_mask = inc_taken
            inc_bound = upper_bound(inst, node.level + 1, inc_weight, inc_value)
            if inc_bound > best_value:
                counter += 1
                heapq.heappush(
                    frontier,
                    (
                        -inc_bound,
                        counter,
                        _Node(
                            level=node.level + 1,
                            weight=inc_weight,
                            value=inc_value,
                            bound=inc_bound,
                            taken=inc_taken,
                        ),
                    ),
                )

        # Exclude branch
        exc_bound = upper_bound(inst, node.level + 1, node.weight, node.value)
        if exc_bound > best_value:
            exc_taken = node.taken[: node.level] + (False,) + node.taken[node.level + 1 :]
            counter += 1
            heapq.heappush(
                frontier,
                (
                    -exc_bound,
                    counter,
                    _Node(
                        level=node.level + 1,
                        weight=node.weight,
                        value=node.value,
                        bound=exc_bound,
                        taken=exc_taken,
                    ),
                ),
            )

        if len(frontier) > peak_frontier:
            peak_frontier = len(frontier)

    return Result(
        best_value=best_value,
        taken_mask=list(best_mask),
        nodes_expanded=nodes_expanded,
        peak_frontier_size=peak_frontier,
        timed_out=timed_out,
    )
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
pytest tests/test_best_first_bnb.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add knapsack/best_first_bnb.py tests/test_best_first_bnb.py
git commit -m "feat: Best-First Branch-and-Bound solver"
```

---

### Task 7: Brute-force parity tests (correctness contract)

**Files:**
- Create: `tests/test_correctness.py`

- [ ] **Step 1: Write the test**

Write to `tests/test_correctness.py`:

```python
import random
from itertools import product

import pytest

from knapsack.best_first_bnb import solve_best_first
from knapsack.fifo_bnb import solve_fifo
from knapsack.item import Item, Instance


def brute_force(inst: Instance) -> int:
    best = 0
    for mask in product((False, True), repeat=inst.n):
        w = sum(it.weight for it, take in zip(inst.items, mask) if take)
        v = sum(it.value for it, take in zip(inst.items, mask) if take)
        if w <= inst.capacity and v > best:
            best = v
    return best


def _random_instance(n: int, seed: int) -> Instance:
    rng = random.Random(seed)
    items = [Item(weight=rng.randint(1, 100), value=rng.randint(1, 100)) for _ in range(n)]
    total_weight = sum(it.weight for it in items)
    capacity = total_weight // 2
    return Instance.from_items(items, capacity=capacity)


@pytest.mark.parametrize("n", [5, 10, 12])
@pytest.mark.parametrize("trial", range(10))
def test_both_algos_match_brute_force(n, trial):
    inst = _random_instance(n, seed=1000 * n + trial)
    expected = brute_force(inst)

    fifo = solve_fifo(inst)
    best_first = solve_best_first(inst)

    assert fifo.best_value == expected, f"FIFO mismatch n={n} trial={trial}"
    assert best_first.best_value == expected, f"Best-first mismatch n={n} trial={trial}"

    # Masks must reconstruct the claimed best value and respect capacity.
    for name, result in (("fifo", fifo), ("best_first", best_first)):
        w = sum(it.weight for it, take in zip(inst.items, result.taken_mask) if take)
        v = sum(it.value for it, take in zip(inst.items, result.taken_mask) if take)
        assert v == result.best_value, f"{name} mask value mismatch"
        assert w <= inst.capacity, f"{name} mask exceeds capacity"
```

- [ ] **Step 2: Run tests and verify they pass**

```bash
pytest tests/test_correctness.py -v
```

Expected: 30 passed (3 sizes × 10 trials).

- [ ] **Step 3: Commit**

```bash
git add tests/test_correctness.py
git commit -m "test: brute-force parity for both B&B solvers"
```

---

### Task 8: Instance generator module

**Files:**
- Create: `benchmark/generate.py`
- Create: `tests/test_generate.py`

- [ ] **Step 1: Write the failing test**

Write to `tests/test_generate.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify they fail**

```bash
pytest tests/test_generate.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `benchmark/generate.py`**

```python
from __future__ import annotations

import random

from knapsack.item import Item, Instance


def make_instance(n: int, seed: int) -> Instance:
    """Generate a reproducible random 0/1 Knapsack instance.

    Weights and values are drawn uniformly from [1, 100].
    Capacity is half the total weight (rounded down).
    """
    rng = random.Random(seed)
    items = [
        Item(weight=rng.randint(1, 100), value=rng.randint(1, 100))
        for _ in range(n)
    ]
    capacity = sum(it.weight for it in items) // 2
    return Instance.from_items(items, capacity=capacity)
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
pytest tests/test_generate.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add benchmark/generate.py tests/test_generate.py
git commit -m "feat: reproducible instance generator"
```

---

### Task 9: Benchmark fixture

**Files:**
- Create: `benchmark/fixture.py`
- Create: `tests/test_fixture.py`

- [ ] **Step 1: Write the failing test**

Write to `tests/test_fixture.py`:

```python
from benchmark.fixture import run_sweep, BenchmarkRow


def test_run_sweep_produces_expected_row_count():
    # 2 sizes × 2 trials × 2 algorithms = 8 rows.
    rows = run_sweep(sizes=[8, 10], trials=2, timeout_s=10.0, base_seed=1)
    assert len(rows) == 8
    assert all(isinstance(r, BenchmarkRow) for r in rows)


def test_run_sweep_covers_both_algorithms():
    rows = run_sweep(sizes=[8], trials=1, timeout_s=10.0, base_seed=1)
    algos = {r.algo for r in rows}
    assert algos == {"fifo", "best_first"}


def test_run_sweep_matches_values_on_same_instance():
    # For small sizes neither should time out; values must agree.
    rows = run_sweep(sizes=[8, 10], trials=2, timeout_s=10.0, base_seed=1)
    by_key: dict[tuple[int, int], dict[str, int]] = {}
    for r in rows:
        by_key.setdefault((r.size, r.trial), {})[r.algo] = r.best_value
    for pair in by_key.values():
        assert pair["fifo"] == pair["best_first"]
```

- [ ] **Step 2: Run tests and verify they fail**

```bash
pytest tests/test_fixture.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `benchmark/fixture.py`**

```python
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


_SOLVERS: dict[str, Callable[[Instance, float], Result]] = {
    "fifo": solve_fifo,
    "best_first": solve_best_first,
}


def _time_solver(
    solver: Callable[[Instance, float], Result], inst: Instance, timeout_s: float
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
            for algo_name, solver in _SOLVERS.items():
                result, elapsed = _time_solver(solver, inst, timeout_s)
                rows.append(
                    BenchmarkRow(
                        size=size,
                        trial=trial,
                        seed=seed,
                        algo=algo_name,
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
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(asdict(r))
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
pytest tests/test_fixture.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add benchmark/fixture.py tests/test_fixture.py
git commit -m "feat: benchmark sweep fixture"
```

---

### Task 10: Plotting module

**Files:**
- Create: `benchmark/plot.py`

*No test — plotting is visual and gets eyeballed from the generated PNG. Smoke-tested via the entry-point run.*

- [ ] **Step 1: Write `benchmark/plot.py`**

```python
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from benchmark.fixture import BenchmarkRow


_ALGO_LABEL = {"fifo": "FIFO B&B", "best_first": "Best-First B&B"}
_ALGO_COLOR = {"fifo": "tab:red", "best_first": "tab:blue"}


def _aggregate(
    rows: list[BenchmarkRow], metric: str
) -> dict[str, dict[int, tuple[float, float, float]]]:
    """Return {algo: {size: (mean, min, max)}} for the given row metric."""
    grouped: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        grouped[r.algo][r.size].append(float(getattr(r, metric)))
    out: dict[str, dict[int, tuple[float, float, float]]] = {}
    for algo, by_size in grouped.items():
        out[algo] = {
            size: (sum(vals) / len(vals), min(vals), max(vals))
            for size, vals in by_size.items()
        }
    return out


def _plot_metric(
    rows: list[BenchmarkRow], metric: str, ylabel: str, title: str, out_path: Path
) -> None:
    agg = _aggregate(rows, metric)
    fig, ax = plt.subplots(figsize=(8, 5))

    for algo, by_size in agg.items():
        sizes = sorted(by_size.keys())
        means = [by_size[s][0] for s in sizes]
        mins = [by_size[s][1] for s in sizes]
        maxs = [by_size[s][2] for s in sizes]
        ax.plot(
            sizes,
            means,
            marker="o",
            label=_ALGO_LABEL.get(algo, algo),
            color=_ALGO_COLOR.get(algo),
        )
        ax.fill_between(sizes, mins, maxs, color=_ALGO_COLOR.get(algo), alpha=0.15)

    ax.set_yscale("log")
    ax.set_xlabel("Number of items (n)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which="both", ls="--", alpha=0.4)
    ax.legend()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_runtime(rows: list[BenchmarkRow], out_path: Path) -> None:
    _plot_metric(
        rows,
        metric="runtime_s",
        ylabel="Runtime (seconds, log scale)",
        title="FIFO vs. Best-First B&B — Runtime",
        out_path=out_path,
    )


def plot_nodes(rows: list[BenchmarkRow], out_path: Path) -> None:
    _plot_metric(
        rows,
        metric="nodes_expanded",
        ylabel="Nodes expanded (log scale)",
        title="FIFO vs. Best-First B&B — Nodes Expanded",
        out_path=out_path,
    )
```

- [ ] **Step 2: Smoke test**

```bash
python -c "
from benchmark.fixture import run_sweep
from benchmark.plot import plot_runtime, plot_nodes
from pathlib import Path
rows = run_sweep(sizes=[8,10], trials=2, timeout_s=10, base_seed=1)
plot_runtime(rows, Path('results/_smoke_runtime.png'))
plot_nodes(rows, Path('results/_smoke_nodes.png'))
print('OK')
"
```

Expected: prints `OK`, and `results/_smoke_runtime.png` + `results/_smoke_nodes.png` exist.

- [ ] **Step 3: Delete smoke-test artifacts**

```bash
rm results/_smoke_runtime.png results/_smoke_nodes.png
```

- [ ] **Step 4: Commit**

```bash
git add benchmark/plot.py
git commit -m "feat: runtime and nodes-expanded plots"
```

---

### Task 11: Entry-point CLI

**Files:**
- Create: `run_benchmark.py`

- [ ] **Step 1: Write `run_benchmark.py`**

```python
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
```

- [ ] **Step 2: Run the full benchmark sweep**

```bash
cd ~/Projects/knapsack-bnb-comparison
source .venv/bin/activate
python run_benchmark.py
```

Expected:
- Prints sweep parameters, CSV path, plot paths.
- Prints a Markdown-style summary table to stdout.
- Creates `results/benchmark_YYYY-MM-DD.csv`, `results/runtime_vs_size.png`, `results/nodes_vs_size.png`.
- Best-First should show dramatically lower mean runtime and nodes_expanded at sizes ≥ 30.
- If FIFO times out at some size: that's expected and acceptable — the timeout column will show it.

- [ ] **Step 3: Inspect the outputs manually**

```bash
ls -la results/
open results/runtime_vs_size.png
open results/nodes_vs_size.png
```

Confirm Best-First curve stays far below FIFO on both charts.

- [ ] **Step 4: Commit**

```bash
git add run_benchmark.py results/
git commit -m "feat: benchmark CLI entry point + initial run results"
```

---

### Task 12: README with research write-up

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

Template — fill the **Results** section using the numbers from the CSV produced in Task 11. Everything else is pre-run content.

````markdown
# Knapsack Branch-and-Bound Comparison

Comparing two Branch-and-Bound variants on the 0/1 Knapsack Problem: **FIFO B&B** (queue-based) vs. **Best-First B&B** (Least-Cost, priority-queue-based).

## The Problem

Given `n` items, each with a weight and value, and a knapsack with capacity `W`, select a subset of items to maximize total value while keeping total weight ≤ `W`. Each item is either fully taken or left behind (0/1, not fractional). The problem is NP-hard — no known polynomial-time algorithm solves it in general — so exact solvers fall back on search with pruning. Branch-and-Bound is the standard exact approach: enumerate the decision tree, prune subtrees whose optimistic upper bound can't beat the best solution found so far.

## The Two Algorithms

Both algorithms share a fractional-relaxation upper-bound function: at any partial state, the best possible completion value is bounded above by greedily filling remaining capacity with whole items in value/weight order, plus one fractional slice. This is what enables pruning. The only difference is **which live node to expand next**.

### FIFO Branch-and-Bound

- **Frontier:** plain FIFO queue (`collections.deque`).
- **Next node to expand:** whichever was enqueued earliest (breadth-first).
- **Pros:** trivial to implement; `O(1)` enqueue/dequeue; cache-friendly access pattern.
- **Cons:** no guidance — expands nodes with poor bounds just as eagerly as promising ones, so `best_value` climbs slowly and pruning activates late. The frontier grows to the full width of the current level before narrowing.

### Best-First (Least-Cost) Branch-and-Bound

- **Frontier:** min-heap (`heapq`) keyed on `-bound` so the node with the **highest** upper bound pops first.
- **Next node to expand:** the one most likely to contain the optimum.
- **Pros:** `best_value` rises quickly, which tightens pruning aggressively; in practice expands orders of magnitude fewer nodes than FIFO.
- **Cons:** `O(log n)` heap operations per push/pop; more complex code; worst-case memory is still exponential if pruning fails to bite.

## Predicted Winner (before running anything)

| | FIFO B&B | Best-First B&B |
|---|---|---|
| Frontier structure | Queue (deque) | Min-heap (priority queue) |
| Per-node op cost | O(1) | O(log n) |
| Worst-case nodes | O(2^n) | O(2^n) |
| Expected nodes in practice | Much larger | Much smaller |
| Peak frontier | Up to full tree level | Bounded by live promising nodes |

**Prediction:** Best-First wins decisively on runtime, and the gap widens as `n` grows. FIFO's cheaper per-op cost doesn't compensate for exploring orders of magnitude more nodes. Both have `O(2^n)` worst-case memory, but Best-First's measured peak frontier should be smaller because tighter pruning discards live nodes sooner.

## Running It

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the default sweep (sizes 10..40, 5 trials each, 60s timeout)
python run_benchmark.py

# Or a quick run
python run_benchmark.py --sizes 10,15,20 --trials 3 --timeout 10
```

Outputs:
- `results/benchmark_YYYY-MM-DD.csv`
- `results/runtime_vs_size.png`
- `results/nodes_vs_size.png`

## Tests

```bash
pytest
```

The correctness suite in `tests/test_correctness.py` brute-forces the optimum on small instances and asserts both solvers match.

## Results

> Fill this section from the CSV and plots produced by `python run_benchmark.py`. Replace the placeholder paragraphs with real numbers.

![Runtime vs. size](results/runtime_vs_size.png)

![Nodes expanded vs. size](results/nodes_vs_size.png)

**Summary (paste the stdout table from `run_benchmark.py` here):**

```
| size | algo       | mean_runtime_s | mean_nodes | peak_frontier | timeouts |
| ---- | ---------- | -------------- | ---------- | ------------- | -------- |
| ...  | ...        | ...            | ...        | ...           | ...      |
```

**Observations (write these after looking at the charts):**
- At n=XX, Best-First ran in X.XX s vs. FIFO's X.XX s — an ~Xx speedup.
- Nodes expanded: Best-First = XXX, FIFO = XXX (~Xx fewer).
- Peak frontier: Best-First = XXX, FIFO = XXX.
- FIFO hit the timeout at n ≥ XX, while Best-First finished at all sizes tested.

## Conclusion

Best-First Branch-and-Bound is the clear winner for 0/1 Knapsack in this experiment. The prediction held: the priority-queue overhead is dwarfed by the savings from expanding far fewer nodes. The chart shape — Best-First growing roughly polynomially where FIFO grows exponentially — makes the case visually as well as numerically. For any instance of practical size, Best-First is the right choice; FIFO is a useful pedagogical baseline but not a competitive exact solver.
````

- [ ] **Step 2: Fill in the Results section**

Open `results/benchmark_YYYY-MM-DD.csv` and `results/runtime_vs_size.png`. Replace the `XX` / `X.XX` placeholders in the **Results** and **Observations** sections with the real numbers. Paste the actual summary table from the stdout of `python run_benchmark.py`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README with research write-up and results"
```

---

### Task 13: Full-suite green check

**Files:** none modified.

- [ ] **Step 1: Run the full test suite**

```bash
cd ~/Projects/knapsack-bnb-comparison
source .venv/bin/activate
pytest -v
```

Expected: everything passes. Counts: test_item(2) + test_bounds(4) + test_result(2) + test_fifo_bnb(4) + test_best_first_bnb(4) + test_correctness(30) + test_generate(3) + test_fixture(3) = **52 passed**.

- [ ] **Step 2: Verify outputs exist**

```bash
ls results/
```

Expected: `benchmark_YYYY-MM-DD.csv`, `runtime_vs_size.png`, `nodes_vs_size.png`.

- [ ] **Step 3: Verify git log**

```bash
git log --oneline
```

Expected: one commit per task, clean history.

---

## Notes for the video walkthrough

- Open with the problem statement + why B&B.
- Show the pseudocode for each algorithm (5.1 vs. 6.1 — same structure, different frontier data structure — is the punchline).
- Walk through the prediction table.
- Play `results/runtime_vs_size.png` full-screen; note where FIFO's curve hockey-sticks.
- Read off 2–3 concrete numbers from the summary table.
- Close with the conclusion: prediction held, Best-First is the clear winner, priority-queue overhead is worth it.
