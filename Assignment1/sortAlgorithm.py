# Insertion Sort in monotonically decreasing order

def insertion_sort_desc(arr) -> list[int]:
    # Traverse from the second element to the end
    for j in range(1, len(arr)):
        key = arr[j]
        i = j - 1

        # Move elements that are smaller than key
        # to one position ahead
        while i >= 0 and arr[i] < key:
            arr[i + 1] = arr[i]
            i -= 1

        arr[i + 1] = key

    return arr


# array to be sorted
numbers = [5, 2, 4, 6, 1, 3]

print(f"\noriginal array: {numbers}")
sorted_numbers = insertion_sort_desc(numbers)
print(f"sorted array: {sorted_numbers}\n")