# Assignment 6: Selection Algorithms & Elementary Data Structures

Python implementations for an algorithms and data structures assignment. All code uses **stdlib only** (Python 3.7+).

## Files

| File | Description |
|------|-------------|
| `selection_algorithms.py` | kth-element selection, correctness demos, and benchmarks |
| `selection_benchmark_results.csv` | Benchmark output (generated after running the script) |
| `elementary_data_structures.py` | Arrays, matrices, stacks, queues, linked lists, and a rooted tree |

---

## Selection Algorithms

Two linear-time algorithms for finding the **kth smallest element** in an array. Both use **1-based indexing** (`k=1` is the minimum) and **do not modify** the original input.

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

Both functions raise `ValueError` when the array is empty, `k < 1`, or `k > len(arr)`.

```python
from selection_algorithms import deterministic_select, randomized_select

arr = [3, 1, 4, 1, 5, 9, 2, 6, 5]
print(deterministic_select(arr, k=4))  # 3
print(randomized_select(arr, k=4))    # 3
```

```bash
python3 selection_algorithms.py
```

Runs correctness demos (checked against `sorted(arr)[k - 1]`) and benchmarks at sizes 100–50,000, writing results to `selection_benchmark_results.csv`.

| CSV column | Description |
|------------|-------------|
| `dataset_type` | `random`, `sorted`, `reverse-sorted`, or `duplicate-heavy` |
| `input_size` | Number of elements |
| `k` | Target rank — median: `(n + 1) // 2` |
| `deterministic_runtime` | Average seconds for Median of Medians |
| `randomized_runtime` | Average seconds for Randomized Quickselect |

---

## Elementary Data Structures

Implementations built from scratch using Python lists only as raw storage — no `collections.deque`, no library stack/queue abstractions.

### DynamicArray

Resizable array with separate `_size` and `_capacity` tracking. Doubles capacity when full.

| Operation | Complexity |
|-----------|------------|
| `append`, `get`, `set`, `size`, `is_empty` | O(1) amortized / O(1) |
| `insert`, `delete` | O(n) |

### Matrix

2D list initialized by row/column count. `delete(row, col)` resets a cell to `None`.

| Operation | Complexity |
|-----------|------------|
| `insert`, `get`, `set`, `delete` | O(1) |
| `display` | O(rows × columns) |

### ArrayStack

Array-backed stack with automatic resize. Raises `EmptyStackError` on empty `pop()` / `peek()`.

| Operation | Complexity |
|-----------|------------|
| `push` | O(1) amortized |
| `pop`, `peek`, `is_empty`, `size` | O(1) |

### ArrayQueue

Circular buffer with `front`, `rear`, `size`, and `capacity`. Doubles when full; avoids O(n) shifts at index 0. Raises `EmptyQueueError` on empty `dequeue()` / `peek()`.

| Operation | Complexity |
|-----------|------------|
| `enqueue` | O(1) amortized |
| `dequeue`, `peek`, `is_empty`, `size` | O(1) |

### SinglyLinkedList

`ListNode` dataclass (`value`, `next`) with explicit head and size tracking.

| Operation | Complexity |
|-----------|------------|
| `insert_at_beginning` | O(1) |
| `insert_at_end`, `insert_at`, `delete_at`, `delete_by_value`, `search`, `get` | O(n) |

### RootedTree (optional)

`TreeNode` dataclass with a list of children. Supports `add_child`, `search`, depth-first traversal, and breadth-first traversal (BFS uses the custom `ArrayQueue`).

```python
from elementary_data_structures import DynamicArray, ArrayStack, SinglyLinkedList

arr = DynamicArray()
arr.append(10)
stack = ArrayStack()
stack.push(1)
```

```bash
python3 elementary_data_structures.py
```

Prints six demonstration sections — one per data structure — showing each operation, its result, and the current state of the structure.

---

## Notes

- Selection: full-array sorting is **not** used; sorting groups of at most five elements (inside Median of Medians) is allowed.
- Randomized selection typically runs faster in practice due to lower constant overhead.
- Data structures: Python lists are used only as underlying storage containers, not as drop-in replacements for the ADTs being implemented.
