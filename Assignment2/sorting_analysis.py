"""
Sorting algorithm analysis: Merge Sort vs Quick Sort.

Compares execution time and peak memory usage across different input sizes
and data distributions (sorted, reverse sorted, random).
"""

import random
import time
import tracemalloc
from typing import Callable, List, Tuple


def merge_sort(arr: List[int]) -> List[int]:
    """
    Merge Sort: divide the array in half, recursively sort each half,
    then merge the two sorted halves into one sorted list.
    Time: O(n log n), Space: O(n).
    """
    if len(arr) <= 1:
        return arr[:]

    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return _merge(left, right)


def _merge(left: List[int], right: List[int]) -> List[int]:
    """Merge two sorted lists into a single sorted list."""
    merged: List[int] = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def quick_sort(arr: List[int]) -> List[int]:
    """
    Quick Sort: choose a pivot, partition elements around it,
    then recursively sort the left and right partitions.
    Time: O(n log n) average, O(n^2) worst case; Space: O(log n) average.
    """
    if len(arr) <= 1:
        return arr[:]

    # Work on a copy so the original list is never modified.
    arr_copy = arr[:]
    _quick_sort_inplace(arr_copy, 0, len(arr_copy) - 1)
    return arr_copy


def _quick_sort_inplace(arr: List[int], low: int, high: int) -> None:
    """In-place quick sort helper using Lomuto partition."""
    while low < high:
        pivot_index = _partition(arr, low, high)
        # Recurse on the smaller partition first to limit stack depth.
        if pivot_index - low < high - pivot_index:
            _quick_sort_inplace(arr, low, pivot_index - 1)
            low = pivot_index + 1
        else:
            _quick_sort_inplace(arr, pivot_index + 1, high)
            high = pivot_index - 1


def _partition(arr: List[int], low: int, high: int) -> int:
    """
    Partition around a median-of-three pivot to avoid O(n^2) on
    already sorted or reverse-sorted input.
    """
    mid = (low + high) // 2
    if arr[low] > arr[mid]:
        arr[low], arr[mid] = arr[mid], arr[low]
    if arr[low] > arr[high]:
        arr[low], arr[high] = arr[high], arr[low]
    if arr[mid] > arr[high]:
        arr[mid], arr[high] = arr[high], arr[mid]

    # Move pivot to the second-to-last position.
    arr[mid], arr[high - 1] = arr[high - 1], arr[mid]
    pivot = arr[high - 1]

    i = low
    for j in range(low, high - 1):
        if arr[j] <= pivot:
            arr[i], arr[j] = arr[j], arr[i]
            i += 1

    arr[i], arr[high - 1] = arr[high - 1], arr[i]
    return i


def generate_dataset(size: int, dataset_type: str) -> List[int]:
    """Create a dataset of the given size and distribution."""
    if dataset_type == "sorted":
        return list(range(size))
    if dataset_type == "reverse sorted":
        return list(range(size - 1, -1, -1))
    if dataset_type == "random":
        return [random.randint(0, size * 10) for _ in range(size)]
    raise ValueError(f"Unknown dataset type: {dataset_type}")


def measure_sort(
    sort_func: Callable[[List[int]], List[int]], arr: List[int]
) -> Tuple[List[int], float, int]:
    """Run a sort function and return the result, elapsed time, and peak memory."""
    tracemalloc.start()
    start = time.perf_counter()
    result = sort_func(arr)
    elapsed = time.perf_counter() - start
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak_memory


def format_memory(bytes_used: int) -> str:
    """Format byte count as KB or MB for display."""
    if bytes_used >= 1024 * 1024:
        return f"{bytes_used / (1024 * 1024):.2f} MB"
    return f"{bytes_used / 1024:.2f} KB"


def run_benchmarks() -> None:
    """Benchmark merge sort and quick sort across sizes and dataset types."""
    sizes = [100, 1_000, 10_000, 50_000]
    dataset_types = ["sorted", "reverse sorted", "random"]
    algorithms = [
        ("Merge Sort", merge_sort),
        ("Quick Sort", quick_sort),
    ]

    headers = [
        "Algorithm",
        "Dataset Type",
        "Input Size",
        "Execution Time",
        "Peak Memory",
    ]
    rows: List[List[str]] = []

    for size in sizes:
        for dataset_type in dataset_types:
            data = generate_dataset(size, dataset_type)
            expected = sorted(data)

            for name, sort_func in algorithms:
                original = data[:]
                result, elapsed, peak_memory = measure_sort(sort_func, data)

                assert data == original, f"{name} modified the input list"
                assert result == expected, f"{name} produced incorrect output"

                rows.append([
                    name,
                    dataset_type,
                    f"{size:,}",
                    f"{elapsed:.6f} s",
                    format_memory(peak_memory),
                ])

    col_widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    separator = "-+-".join("-" * width for width in col_widths)
    header_line = " | ".join(
        header.ljust(col_widths[i]) for i, header in enumerate(headers)
    )

    print("\nSorting Algorithm Comparison\n")
    print(header_line)
    print(separator)
    for row in rows:
        print(" | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)))


if __name__ == "__main__":
    random.seed(42)
    run_benchmarks()
