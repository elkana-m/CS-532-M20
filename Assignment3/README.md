# Assignment 3 — Randomized Quicksort & Hash Table with Chaining

Two Python implementations for CS-532-M20: a randomized quicksort with three-way partitioning, and a hash table that resolves collisions via chaining with dynamic resizing.

## Requirements

- Python 3.10+ (tested with Python 3.14)
- A virtual environment is included in this directory (`.venv`)

## How to Run

From the `Assignment3` directory:

```bash
# Activate the virtual environment (optional)
source .venv/bin/activate

# Run randomized quicksort demo
python randomized_quicksort.py

# Run hash table demo
python hash_table_chaining.py
```

If `python` is not available, use the venv interpreter directly:

```bash
.venv/bin/python randomized_quicksort.py
.venv/bin/python hash_table_chaining.py
```

Each file includes a built-in demo under `if __name__ == "__main__":` that prints results to the terminal.

## Files

| File | Description |
|---|---|
| `randomized_quicksort.py` | Randomized quicksort with three-way partitioning |
| `hash_table_chaining.py` | Hash table with chaining, universal hashing, and dynamic resizing |

## Findings

### Randomized Quicksort

- **Correctness across edge cases.** The algorithm handles empty arrays, single-element arrays, negative numbers, already-sorted input, reverse-sorted input, and arrays with many duplicates. In every test case, the original array is left unchanged and a new sorted array is returned.
- **Random pivot selection helps avoid worst-case behavior.** Choosing the pivot uniformly at random from each subarray prevents the O(n²) degradation that deterministic quicksort suffers on sorted or reverse-sorted input.
- **Three-way partitioning is effective for duplicates.** On an input like `[2, 8, 2, 5, 8, 2, 1, 8, 5, 2, 1, 8]`, elements equal to the pivot are grouped in place and skipped during recursion. This keeps performance closer to O(n log n) on duplicate-heavy data instead of recursing on many single-element partitions.

### Hash Table with Chaining

- **Chaining handles collisions cleanly.** With a small initial capacity of 4, multiple keys hash to the same bucket and are stored in per-bucket linked lists. After 9 inserts, chain lengths of 2 show that collisions occurred and were resolved without data loss.
- **Universal hashing distributes keys reasonably.** Using `h(k) = ((a * hash(k) + b) mod p) mod m` with random constants `a` and `b` spreads both string and integer keys across buckets, even when the table is small.
- **Dynamic resizing keeps the load factor balanced.** The table grows from capacity 4 → 16 when the load factor exceeds 0.75 (triggered on the 4th insert), and shrinks from 16 → 8 when deletions bring the load factor below 0.25. Capacity never drops below the initial size of 4.
- **All core operations work as expected.** Search returns the correct value for existing keys and `None` for missing keys. Insert updates existing keys in place without increasing the element count. Delete returns `True` for removed keys and `False` for keys that were never stored.

### Takeaways

Both implementations avoid Python's built-in shortcuts (`sorted()`, `.sort()`, and `dict` for hash storage) and instead demonstrate the underlying algorithmic ideas directly. The demo output confirms correctness and makes the behavior of partitioning, collision resolution, and resizing easy to observe — a useful foundation for future benchmarking work.
