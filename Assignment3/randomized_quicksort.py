"""
Randomized Quicksort with three-way partitioning.

Sorts integers in ascending order using a randomly chosen pivot at each step.
Designed for clarity and future extension (e.g., benchmarking hooks).
"""

import random
from typing import List, Tuple


def randomized_quicksort(arr: List[int]) -> List[int]:
    """
    Return a new array containing the elements of arr sorted in ascending order.

    The original array is not modified.
    """
    result = list(arr)
    if len(result) > 1:
        _randomized_quicksort_inplace(result, 0, len(result) - 1)
    return result


def _randomized_quicksort_inplace(arr: List[int], low: int, high: int) -> None:
    """
    Recursively sort arr[low:high + 1] in place.

    Base case: subarrays of size 0 or 1 are already sorted.
    Recursive step: partition around a random pivot, then sort the less-than
    and greater-than regions. Elements equal to the pivot are already in
    their final positions and are not recursed into.
    """
    if low >= high:
        return

    lt, gt = _partition_three_way(arr, low, high)

    _randomized_quicksort_inplace(arr, low, lt - 1)
    _randomized_quicksort_inplace(arr, gt + 1, high)


def _choose_random_pivot_index(arr: List[int], low: int, high: int) -> int:
    """
    Select a pivot index uniformly at random from the current subarray.

    Random pivot selection avoids worst-case O(n^2) behavior on already
    sorted or reverse-sorted inputs that deterministic pivot choices can trigger.
    """
    return random.randint(low, high)


def _swap(arr: List[int], i: int, j: int) -> None:
    """Exchange arr[i] and arr[j]."""
    arr[i], arr[j] = arr[j], arr[i]


def _partition_three_way(arr: List[int], low: int, high: int) -> Tuple[int, int]:
    """
    Three-way partition of arr[low:high + 1] around a randomly chosen pivot.

    After partitioning:
      - arr[low : lt]     contains elements less than the pivot
      - arr[lt : gt + 1]  contains elements equal to the pivot
      - arr[gt + 1 : high + 1] contains elements greater than the pivot

    Returns (lt, gt), the inclusive bounds of the equal-to-pivot region.
    Duplicate-heavy inputs benefit because the equal region is skipped during
    recursion, keeping average time near O(n log n) instead of degrading toward O(n^2).
    """
    pivot_index = _choose_random_pivot_index(arr, low, high)
    pivot_value = arr[pivot_index]

    # Move the pivot value to the front so scanning can start at low + 1.
    _swap(arr, low, pivot_index)

    lt = low       # next position for a "less than" element
    gt = high      # next position for a "greater than" element
    i = low + 1    # current element under inspection

    while i <= gt:
        if arr[i] < pivot_value:
            _swap(arr, lt, i)
            lt += 1
            i += 1
        elif arr[i] > pivot_value:
            _swap(arr, i, gt)
            gt -= 1
        else:
            i += 1

    return lt, gt


def _run_test_case(label: str, arr: List[int]) -> None:
    """Sort arr and print the original alongside the sorted result."""
    original_snapshot = list(arr)
    sorted_result = randomized_quicksort(arr)

    print(f"{label}:")
    print(f"  Original: {original_snapshot}")
    print(f"  Sorted:   {sorted_result}")
    print()


if __name__ == "__main__":
    print("Randomized Quicksort — demonstration\n")

    _run_test_case("Empty array", [])

    _run_test_case("Single-element array", [42])

    _run_test_case(
        "Random array",
        [3, -1, 7, 0, 5, -4, 2, 8, -2, 6],
    )

    _run_test_case(
        "Sorted array",
        [-5, -2, 0, 1, 3, 4, 9],
    )

    _run_test_case(
        "Reverse-sorted array",
        [9, 4, 3, 1, 0, -2, -5],
    )

    _run_test_case(
        "Array with many duplicate values",
        [2, 8, 2, 5, 8, 2, 1, 8, 5, 2, 1, 8],
    )
