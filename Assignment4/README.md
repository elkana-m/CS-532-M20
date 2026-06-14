# Assignment 4: Heapsort & Priority Queue

Single-file implementation in `heap_priority_queue.py` — heapsort using a max-heap, plus a priority queue backed by a binary heap.

## How to Run

From the `Assignment4` folder:

```bash
.venv/bin/python heap_priority_queue.py
```

If your virtual environment is already active:

```bash
python heap_priority_queue.py
```

No command-line arguments needed. The script runs all built-in demos and prints results to the terminal.

## What's in the File

- **Heapsort** — `heapify`, `build_max_heap`, `heap_sort` (returns a new sorted list, doesn't touch the original)
- **Priority Queue** — `Task` dataclass + `PriorityQueue` class with insert, extract, increase/decrease key, peek, is_empty, size
- **Index map** — `task_id` → heap index dict for O(log n) priority updates

## Findings

### Heapsort

- Works on random, already-sorted, reverse-sorted, and duplicate-heavy lists
- Original input stays unchanged (we copy first)
- Max-heap pulls the biggest value to the root each round, then we swap it to the end — ends up ascending

### Priority Queue

- Highest priority comes out first
- Tie-breakers: earlier deadline wins, then earlier arrival time
- `increase_key` bubbles the task up; `decrease_key` sifts it down
- `peek` is O(1), insert/extract/key updates are O(log n)
- `extract_max()` on an empty queue returns `None` safely

### Test Results

| Test | Result |
|------|--------|
| Random list `[38, 27, 43, 3, 9, 82, 10]` | Sorted to `[3, 9, 10, 27, 38, 43, 82]` |
| Already sorted | Stays sorted |
| Reverse sorted `[9, 7, 5, 3, 1]` | Sorted to `[1, 3, 5, 7, 9]` |
| Duplicates | Handled correctly |
| Insert 5 tasks | Heap ordering looks right |
| Extract max | Task 5 out first (priority 7, earliest deadline/arrival among ties) |
| Increase key (task 1: 3 → 9) | Task 1 moves to root |
| Decrease key (task 2: 7 → 2) | Task 2 sinks, task 1 stays on top |
| Drain queue | Order: 9 → 7 → 5 → 2 |
| Empty queue extract | Returns `None` |
