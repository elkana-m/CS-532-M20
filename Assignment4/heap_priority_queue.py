from dataclasses import dataclass
from typing import List, Optional


# --- Heapsort ---


def heapify(arr: List[int], n: int, i: int) -> None:
    # sift down - swap with bigger child until max-heap holds
    largest = i
    left = 2 * i + 1
    right = 2 * i + 2

    if left < n and arr[left] > arr[largest]:
        largest = left
    if right < n and arr[right] > arr[largest]:
        largest = right

    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)


def build_max_heap(arr: List[int]) -> None:
    # start at last non-leaf, heapify each node up to root
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)


def heap_sort(arr: List[int]) -> List[int]:
    result = arr[:]  # don't modify original
    n = len(result)

    # build max-heap - biggest ends up at index 0
    build_max_heap(result)

    for end in range(n - 1, 0, -1):
        # pull max to the end of the array
        result[0], result[end] = result[end], result[0]
        # fix heap on the smaller part left over
        heapify(result, end, 0)

    return result


# --- Priority Queue ---


@dataclass
class Task:
    task_id: int
    priority: int
    arrival_time: int
    deadline: int
    description: str


def _task_heap_key(task: Task) -> tuple:
    # max-heap: priority first, then earlier deadline, then earlier arrival
    return (task.priority, -task.deadline, -task.arrival_time)


class PriorityQueue:
    # max-heap + dict so we can find tasks by id fast

    def __init__(self) -> None:
        self._heap: List[Task] = []
        self._index_map: dict[int, int] = {}

    def _parent(self, i: int) -> int:
        return (i - 1) // 2

    def _left(self, i: int) -> int:
        return 2 * i + 1

    def _right(self, i: int) -> int:
        return 2 * i + 2

    def _greater(self, i: int, j: int) -> bool:
        return _task_heap_key(self._heap[i]) > _task_heap_key(self._heap[j])

    def _swap(self, i: int, j: int) -> None:
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]
        self._index_map[self._heap[i].task_id] = i
        self._index_map[self._heap[j].task_id] = j

    def _bubble_up(self, i: int) -> None:
        while i > 0:
            parent = self._parent(i)
            if not self._greater(i, parent):
                break
            self._swap(i, parent)
            i = parent

    def _sift_down(self, i: int) -> None:
        size = len(self._heap)
        while True:
            largest = i
            left = self._left(i)
            right = self._right(i)

            if left < size and self._greater(left, largest):
                largest = left
            if right < size and self._greater(right, largest):
                largest = right

            if largest == i:
                break

            self._swap(i, largest)
            i = largest

    def insert(self, task: Task) -> None:
        # O(log n) - add to end, bubble up
        if task.task_id in self._index_map:
            raise ValueError(f"Task id {task.task_id} already exists in the queue.")

        self._heap.append(task)
        index = len(self._heap) - 1
        self._index_map[task.task_id] = index
        self._bubble_up(index)

    def extract_max(self) -> Optional[Task]:
        # O(log n) - grab root, move last to root, sift down
        if self.is_empty():
            return None

        max_task = self._heap[0]
        last = self._heap.pop()
        del self._index_map[max_task.task_id]

        if self._heap:
            self._heap[0] = last
            self._index_map[last.task_id] = 0
            self._sift_down(0)

        return max_task

    def increase_key(self, task_id: int, new_priority: int) -> None:
        # O(log n) - bump priority, bubble up
        if task_id not in self._index_map:
            raise ValueError(f"Task id {task_id} not found in the queue.")
        if new_priority < self._heap[self._index_map[task_id]].priority:
            raise ValueError("increase_key requires new_priority >= current priority.")

        index = self._index_map[task_id]
        self._heap[index].priority = new_priority
        self._bubble_up(index)

    def decrease_key(self, task_id: int, new_priority: int) -> None:
        # O(log n) - lower priority, sift down
        if task_id not in self._index_map:
            raise ValueError(f"Task id {task_id} not found in the queue.")
        if new_priority > self._heap[self._index_map[task_id]].priority:
            raise ValueError("decrease_key requires new_priority <= current priority.")

        index = self._index_map[task_id]
        self._heap[index].priority = new_priority
        self._sift_down(index)

    def is_empty(self) -> bool:
        # O(1)
        return len(self._heap) == 0

    def peek(self) -> Optional[Task]:
        # O(1) - just look at root
        if self.is_empty():
            return None
        return self._heap[0]

    def size(self) -> int:
        return len(self._heap)

    def __repr__(self) -> str:
        if self.is_empty():
            return "PriorityQueue(empty)"
        tasks = [
            f"(id={t.task_id}, pri={t.priority}, deadline={t.deadline}, "
            f"arrival={t.arrival_time})"
            for t in self._heap
        ]
        return f"PriorityQueue([{', '.join(tasks)}])"


# --- Tests ---


def _print_queue_state(label: str, pq: PriorityQueue) -> None:
    print(f"  Queue state after {label}: {pq}")
    print(f"  Queue size: {pq.size()}, is_empty: {pq.is_empty()}")
    peeked = pq.peek()
    if peeked:
        print(
            f"  Peek -> id={peeked.task_id}, priority={peeked.priority}, "
            f"deadline={peeked.deadline}"
        )
    else:
        print("  Peek -> None")


def _run_heapsort_demo(name: str, data: List[int]) -> None:
    print(f"\n--- Heapsort: {name} ---")
    print(f"  Original list: {data}")
    sorted_data = heap_sort(data)
    print(f"  Sorted list:   {sorted_data}")
    print(f"  Input unchanged: {data}")


def _run_priority_queue_demos() -> None:
    print("\n" + "=" * 60)
    print("PRIORITY QUEUE DEMONSTRATIONS")
    print("=" * 60)

    pq = PriorityQueue()

    print("\n--- Priority Queue: Insertion ---")
    tasks = [
        Task(1, priority=3, arrival_time=10, deadline=50, description="Low priority"),
        Task(2, priority=7, arrival_time=5, deadline=30, description="High priority"),
        Task(3, priority=5, arrival_time=8, deadline=20, description="Medium priority"),
        Task(4, priority=7, arrival_time=12, deadline=25, description="Same priority, later deadline"),
        Task(5, priority=7, arrival_time=3, deadline=25, description="Same priority/deadline, earlier arrival"),
    ]
    for task in tasks:
        pq.insert(task)
        print(
            f"  Inserted: id={task.task_id}, priority={task.priority}, "
            f"deadline={task.deadline}, arrival={task.arrival_time}"
        )
    _print_queue_state("all insertions", pq)

    print("\n--- Priority Queue: Peek ---")
    top = pq.peek()
    print(
        f"  Highest-priority task (peek): id={top.task_id}, "
        f"priority={top.priority}, deadline={top.deadline}, arrival={top.arrival_time}"
    )
    _print_queue_state("peek (no removal)", pq)

    print("\n--- Priority Queue: Extract Max ---")
    extracted = pq.extract_max()
    print(
        f"  Task extracted: id={extracted.task_id}, priority={extracted.priority}, "
        f"deadline={extracted.deadline}, arrival={extracted.arrival_time}"
    )
    _print_queue_state("extract_max", pq)

    print("\n--- Priority Queue: Increase Key ---")
    print("  Increasing task id=1 priority from 3 to 9")
    pq.increase_key(1, 9)
    _print_queue_state("increase_key(1, 9)", pq)

    print("\n--- Priority Queue: Decrease Key ---")
    print("  Decreasing task id=2 priority from 7 to 2")
    pq.decrease_key(2, 2)
    _print_queue_state("decrease_key(2, 2)", pq)

    print("\n--- Priority Queue: Is Empty ---")
    print(f"  is_empty before draining: {pq.is_empty()}")

    print("\n  Draining remaining tasks in priority order:")
    while not pq.is_empty():
        task = pq.extract_max()
        print(
            f"    Extracted: id={task.task_id}, priority={task.priority}, "
            f"deadline={task.deadline}, arrival={task.arrival_time}"
        )

    print(f"  is_empty after draining: {pq.is_empty()}")

    print("\n--- Priority Queue: Extract from Empty Queue ---")
    result = pq.extract_max()
    print(f"  extract_max() on empty queue returned: {result}")
    print(f"  is_empty: {pq.is_empty()}")


if __name__ == "__main__":
    print("=" * 60)
    print("HEAPSORT DEMONSTRATIONS")
    print("=" * 60)

    _run_heapsort_demo("random list", [38, 27, 43, 3, 9, 82, 10])
    _run_heapsort_demo("already sorted list", [1, 2, 3, 4, 5, 6, 7])
    _run_heapsort_demo("reverse-sorted list", [9, 7, 5, 3, 1])
    _run_heapsort_demo("list with duplicates", [4, 1, 4, 2, 8, 2, 8, 1])

    _run_priority_queue_demos()

    print("\n" + "=" * 60)
    print("ALL DEMONSTRATIONS COMPLETE")
    print("=" * 60)
