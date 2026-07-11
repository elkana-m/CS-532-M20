# Assignment 6: Selection Algorithms

Implementation of two linear-time selection algorithms for finding the **kth smallest element** in an array. Both use **1-based indexing** (`k=1` is the minimum) and **do not modify** the original input.

## Files

| File | Description |
|------|-------------|
| `selection_algorithms.py` | Algorithms, correctness demos, and benchmarks |
| `selection_benchmark_results.csv` | Benchmark output (generated after running the script) |

## Algorithms

### Deterministic Selection — Median of Medians

`deterministic_select(arr, k)` chooses a pivot by:

1. Splitting the array into groups of five
2. Finding the median of each group
3. Recursively selecting the median of those medians as the pivot

Three-way partitioning (less / equal / greater) handles duplicates efficiently.

| | Complexity |
|---|------------|
| Worst-case time | O(n) |
| Expected time | O(n) |
| Space | O(n) — partition copies at each recursion level |

### Randomized Selection — Randomized Quickselect

`randomized_select(arr, k)` picks a pivot uniformly at random from the current subarray and applies the same three-way partition.

| | Complexity |
|---|------------|
| Expected time | O(n) |
| Worst-case time | O(n²) |
| Space | O(n) — partition copies at each recursion level |

## Usage

```python
from selection_algorithms import deterministic_select, randomized_select

arr = [3, 1, 4, 1, 5, 9, 2, 6, 5]
k = 4

print(deterministic_select(arr, k))  # 3
print(randomized_select(arr, k))     # 3
print(arr)                           # unchanged: [3, 1, 4, 1, 5, 9, 2, 6, 5]
```

Both functions raise `ValueError` when:

- the array is empty
- `k < 1`
- `k > len(arr)`

## Running

Requires **Python 3.7+** (stdlib only — no external packages).

```bash
python3 selection_algorithms.py
```

The script runs two sections:

1. **Correctness demos** — random, sorted, reverse-sorted, duplicate-heavy, negative, and single-element arrays; results are checked against `sorted(arr)[k - 1]`.
2. **Benchmarks** — sizes 100, 1,000, 5,000, 10,000, and 50,000 across four dataset types; each configuration is averaged over 5 runs and written to `selection_benchmark_results.csv`.

## Benchmark CSV Columns

| Column | Description |
|--------|-------------|
| `dataset_type` | `random`, `sorted`, `reverse-sorted`, or `duplicate-heavy` |
| `input_size` | Number of elements |
| `k` | Target rank — median: `(n + 1) // 2` |
| `deterministic_runtime` | Average seconds for Median of Medians |
| `randomized_runtime` | Average seconds for Randomized Quickselect |

## Notes

- Full-array sorting is **not** used for selection; sorting groups of at most five elements (inside Median of Medians) is allowed.
- Randomized selection typically runs faster in practice due to lower constant overhead, even though both algorithms are linear in expected time.
