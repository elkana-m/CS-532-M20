"""Selection algorithms for finding the kth smallest element in an array."""

from __future__ import annotations

import csv
import random
import time
from typing import List, Tuple


def _validate_input(arr: List[int], k: int) -> None:
    """Validate array and k before selection."""
    if not arr:
        raise ValueError("Array cannot be empty")
    if k < 1:
        raise ValueError("k must be at least 1")
    if k > len(arr):
        raise ValueError("k cannot exceed array length")


def _median_of_five(group: List[int]) -> int:
    """Return the median of a group containing at most five elements."""
    # Sorting groups of at most five elements is allowed for Median of Medians.
    sorted_group = sorted(group)
    return sorted_group[len(sorted_group) // 2]


def _three_way_partition(
    arr: List[int], pivot: int
) -> Tuple[List[int], List[int], List[int]]:
    """
    Partition arr into three buckets relative to pivot:
    elements less than, equal to, and greater than pivot.
    """
    less: List[int] = []
    equal: List[int] = []
    greater: List[int] = []

    for value in arr:
        if value < pivot:
            less.append(value)
        elif value > pivot:
            greater.append(value)
        else:
            equal.append(value)

    return less, equal, greater


def _deterministic_select_inplace(subarr: List[int], k: int) -> int:
    """
    Median-of-Medians selection on a mutable copy of the subarray.

    Worst-case time: O(n)
    Expected time: O(n)
    Space complexity: O(n) due to recursive partitioning copies.
    """
    if len(subarr) == 1:
        return subarr[0]

    pivot = _median_of_medians_pivot(subarr)
    less, equal, greater = _three_way_partition(subarr, pivot)

    if k <= len(less):
        return _deterministic_select_inplace(less, k)
    if k <= len(less) + len(equal):
        return pivot
    return _deterministic_select_inplace(greater, k - len(less) - len(equal))


def _median_of_medians_pivot(arr: List[int]) -> int:
    """Choose a pivot using the Median of Medians strategy."""
    n = len(arr)
    if n <= 5:
        return _median_of_five(arr)

    medians = [_median_of_five(arr[i : i + 5]) for i in range(0, n, 5)]
    median_index = (len(medians) + 1) // 2
    return _deterministic_select_inplace(medians, median_index)


def deterministic_select(arr: List[int], k: int) -> int:
    """
    Return the kth smallest element using deterministic Median-of-Medians selection.

    k is 1-based (k=1 returns the smallest element).
    The original array is not modified.
    """
    _validate_input(arr, k)
    return _deterministic_select_inplace(arr.copy(), k)


def _randomized_select_inplace(subarr: List[int], k: int) -> int:
    """
    Randomized quickselect on a mutable copy of the subarray.

    Expected time: O(n)
    Worst-case time: O(n^2)
    Space complexity: O(n) due to recursive partitioning copies.
    """
    if len(subarr) == 1:
        return subarr[0]

    pivot_index = random.randrange(len(subarr))
    pivot = subarr[pivot_index]
    less, equal, greater = _three_way_partition(subarr, pivot)

    if k <= len(less):
        return _randomized_select_inplace(less, k)
    if k <= len(less) + len(equal):
        return pivot
    return _randomized_select_inplace(greater, k - len(less) - len(equal))


def randomized_select(arr: List[int], k: int) -> int:
    """
    Return the kth smallest element using randomized quickselect.

    k is 1-based (k=1 returns the smallest element).
    The original array is not modified.
    """
    _validate_input(arr, k)
    return _randomized_select_inplace(arr.copy(), k)


def _generate_dataset(dataset_type: str, size: int) -> List[int]:
    """Create benchmark datasets of the requested type and size."""
    if dataset_type == "random":
        return [random.randint(-size, size) for _ in range(size)]
    if dataset_type == "sorted":
        return list(range(size))
    if dataset_type == "reverse-sorted":
        return list(range(size, 0, -1))
    if dataset_type == "duplicate-heavy":
        return [random.randint(0, max(1, size // 10)) for _ in range(size)]
    raise ValueError(f"Unknown dataset type: {dataset_type}")


def _run_benchmark(
    sizes: List[int],
    dataset_types: List[str],
    runs: int = 5,
) -> List[dict]:
    """Benchmark both algorithms and return rows for reporting and CSV export."""
    results: List[dict] = []

    for dataset_type in dataset_types:
        for size in sizes:
            data = _generate_dataset(dataset_type, size)
            k = (size + 1) // 2
            expected = sorted(data)[k - 1]

            deterministic_times: List[float] = []
            randomized_times: List[float] = []

            for _ in range(runs):
                det_result = deterministic_select(data, k)
                if det_result != expected:
                    raise RuntimeError(
                        f"Deterministic select failed for {dataset_type}, n={size}"
                    )

                start = time.perf_counter()
                deterministic_select(data, k)
                deterministic_times.append(time.perf_counter() - start)

                rand_result = randomized_select(data, k)
                if rand_result != expected:
                    raise RuntimeError(
                        f"Randomized select failed for {dataset_type}, n={size}"
                    )

                start = time.perf_counter()
                randomized_select(data, k)
                randomized_times.append(time.perf_counter() - start)

            results.append(
                {
                    "dataset_type": dataset_type,
                    "input_size": size,
                    "k": k,
                    "deterministic_runtime": sum(deterministic_times) / runs,
                    "randomized_runtime": sum(randomized_times) / runs,
                }
            )

    return results


def _print_benchmark_table(results: List[dict]) -> None:
    """Print benchmark results in a formatted table."""
    header = (
        f"{'Dataset Type':<18}"
        f"{'Input Size':>12}"
        f"{'k':>8}"
        f"{'Deterministic (s)':>20}"
        f"{'Randomized (s)':>18}"
    )
    print("\nBenchmark Results")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for row in results:
        print(
            f"{row['dataset_type']:<18}"
            f"{row['input_size']:>12}"
            f"{row['k']:>8}"
            f"{row['deterministic_runtime']:>20.6f}"
            f"{row['randomized_runtime']:>18.6f}"
        )


def _save_benchmark_csv(results: List[dict], filename: str) -> None:
    """Save benchmark results to a CSV file."""
    fieldnames = [
        "dataset_type",
        "input_size",
        "k",
        "deterministic_runtime",
        "randomized_runtime",
    ]
    with open(filename, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def _run_correctness_demo() -> None:
    """Demonstrate both algorithms on representative test cases."""
    random.seed(42)

    test_cases = [
        ("random array", [random.randint(-20, 20) for _ in range(12)], 5),
        ("sorted array", list(range(1, 11)), 4),
        ("reverse-sorted array", list(range(10, 0, -1)), 7),
        ("duplicate values", [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5], 6),
        ("negative values", [-5, -1, -8, 0, 3, -2, 7], 3),
        ("single-element array", [42], 1),
    ]

    print("Correctness Demonstration")
    print("=" * 80)

    for name, arr, k in test_cases:
        original_copy = arr.copy()
        expected = sorted(arr)[k - 1]
        det_result = deterministic_select(arr, k)
        rand_result = randomized_select(arr, k)

        print(f"\nTest case: {name}")
        print(f"Original array: {arr}")
        print(f"k: {k}")
        print(f"Deterministic result: {det_result}")
        print(f"Randomized result: {rand_result}")
        print(f"Expected (sorted): {expected}")
        print(f"Deterministic matches expected: {det_result == expected}")
        print(f"Randomized matches expected: {rand_result == expected}")
        print(f"Original array unchanged: {arr == original_copy}")


if __name__ == "__main__":
    _run_correctness_demo()

    benchmark_sizes = [100, 1_000, 5_000, 10_000, 50_000]
    benchmark_dataset_types = [
        "random",
        "sorted",
        "reverse-sorted",
        "duplicate-heavy",
    ]

    random.seed(123)
    benchmark_results = _run_benchmark(benchmark_sizes, benchmark_dataset_types, runs=5)
    _print_benchmark_table(benchmark_results)
    _save_benchmark_csv(benchmark_results, "selection_benchmark_results.csv")
    print("\nBenchmark results saved to selection_benchmark_results.csv")
