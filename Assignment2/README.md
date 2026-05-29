# Sorting Algorithm Analysis

This project compares **Merge Sort** and **Quick Sort** by measuring execution time and peak memory usage across multiple input sizes and data distributions.

## How to Run

From the `Assignment2` directory:

```bash
python3 sorting_analysis.py
```

If you are using the project virtual environment:

```bash
.venv/bin/python sorting_analysis.py
```

**Requirements:** Python 3.8+ (standard library only — no external packages).

The program benchmarks both algorithms on input sizes of 100, 1,000, 10,000, and 50,000 elements, using sorted, reverse sorted, and random data. It prints a comparison table and verifies that each algorithm returns a correctly sorted list without modifying the original input.

## Overall Performance

**Quick Sort performed better overall** in this experiment. It was consistently faster than Merge Sort at every input size and dataset type tested.

At the largest size (50,000 elements), Quick Sort was roughly **3–4× faster**:

| Dataset Type   | Merge Sort | Quick Sort | Speedup |
|----------------|------------|------------|---------|
| Sorted         | 0.091 s    | 0.025 s    | ~3.7×   |
| Reverse sorted | 0.095 s    | 0.033 s    | ~2.9×   |
| Random         | 0.140 s    | 0.032 s    | ~4.4×   |

Quick Sort benefits from sorting in place on a single copy of the array, which reduces allocation overhead. Merge Sort creates many intermediate sub-lists during the divide-and-merge process, which adds memory traffic and Python object creation cost.

## Effect of Dataset Type

### Merge Sort

Merge Sort showed **similar performance across sorted and reverse sorted data**, with only minor differences. Random data was slightly slower at larger sizes (e.g., 0.140 s vs ~0.092 s at n = 50,000).

This matches expectations: Merge Sort always divides the array in half regardless of input order, so its time complexity is **O(n log n) in all cases**. Random data can require slightly more work during merging because elements are interleaved more unevenly between the two halves.

### Quick Sort

Quick Sort also maintained **O(n log n) behavior** on all three dataset types because the implementation uses a **median-of-three pivot** strategy, which avoids the O(n²) worst case on already sorted or reverse sorted input.

- **Sorted data** was the fastest for Quick Sort (0.025 s at n = 50,000).
- **Reverse sorted data** was modestly slower (0.033 s), since partitioning is less balanced even with a good pivot.
- **Random data** fell between the two (0.032 s), with performance close to reverse sorted at large n.

Without a good pivot selection, Quick Sort would degrade to O(n²) on sorted and reverse sorted input. The median-of-three pivot keeps partitions reasonably balanced, which is why all three dataset types stayed in the expected O(n log n) range.

## Comparison with Asymptotic Time Complexity

| Algorithm   | Expected Time Complexity | Observed Behavior |
|-------------|--------------------------|-------------------|
| Merge Sort  | O(n log n) always        | Run time grew smoothly with n and was stable across dataset types, consistent with O(n log n). |
| Quick Sort  | O(n log n) average       | Run time also scaled as O(n log n) here because the pivot strategy avoids worst-case inputs. |

To check scaling, compare n = 1,000 vs n = 50,000 (a 50× increase in n). For an O(n log n) algorithm, we expect roughly a **50 × (log 50000 / log 1000) ≈ 50 × 1.67 ≈ 83×** increase in time.

Observed Merge Sort times on random data: 0.0016 s → 0.140 s (**~88×**). Quick Sort: 0.0004 s → 0.032 s (**~80×**). Both are close to the theoretical O(n log n) growth, with small deviations from constant factors, Python overhead, and cache effects.

At small sizes (n = 100), absolute times are so short that measurement noise dominates, which is why the ratio between algorithms is less meaningful at the smallest scale.

## Memory Usage Differences

| Algorithm   | Expected Space | Observed Peak Memory (n = 50,000) |
|-------------|----------------|-----------------------------------|
| Merge Sort  | O(n)           | ~862–977 KB                       |
| Quick Sort  | O(log n)       | ~391 KB                           |

**Merge Sort uses substantially more memory** because it allocates new sub-lists at every recursive level and during each merge step. Peak memory grows roughly linearly with input size (e.g., ~20 KB at n = 1,000, ~977 KB at n = 50,000 for sorted data).

**Quick Sort uses less memory** because it sorts in place on a single copy of the array. Its auxiliary space comes mainly from the recursion stack, which is O(log n) with balanced partitions. Peak memory stayed near ~391 KB for all dataset types at n = 50,000 and scaled much more slowly with n.

In summary, Quick Sort traded slightly more complex pivot logic for better time and space efficiency in this Python implementation, while Merge Sort offered more predictable performance across input order at the cost of higher memory use.
