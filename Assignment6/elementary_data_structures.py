"""Elementary data structures implemented from scratch for study and demonstration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


class EmptyStackError(Exception):
    """Raised when pop() or peek() is called on an empty stack."""


class EmptyQueueError(Exception):
    """Raised when dequeue() or peek() is called on an empty queue."""


class DynamicArray:
    """Dynamic array backed by a Python list with explicit size and capacity tracking."""

    def __init__(self, initial_capacity: int = 4) -> None:
        """Initialize an empty dynamic array with the given starting capacity."""
        if initial_capacity < 1:
            raise ValueError("Initial capacity must be at least 1")
        self._capacity: int = initial_capacity
        self._data: List[Any] = [None] * self._capacity
        self._size: int = 0

    def _validate_index(self, index: int, allow_end: bool = False) -> None:
        """Validate an index for get/set/delete/insert operations."""
        upper_bound = self._size if not allow_end else self._size + 1
        if index < 0 or index >= upper_bound:
            raise IndexError(f"Index {index} out of range for size {self._size}")

    def _resize(self, new_capacity: int) -> None:
        """Grow or shrink internal storage while preserving current elements."""
        new_data = [None] * new_capacity
        for index in range(self._size):
            new_data[index] = self._data[index]
        self._data = new_data
        self._capacity = new_capacity

    def _ensure_capacity_for_insert(self) -> None:
        """Double capacity when the array is full."""
        if self._size == self._capacity:
            self._resize(self._capacity * 2)

    def insert(self, index: int, value: Any) -> None:
        """Insert value at index, shifting existing elements right. Time: O(n)."""
        self._validate_index(index, allow_end=True)
        self._ensure_capacity_for_insert()

        for position in range(self._size, index, -1):
            self._data[position] = self._data[position - 1]

        self._data[index] = value
        self._size += 1

    def append(self, value: Any) -> None:
        """Append value to the end of the array. Time: amortized O(1)."""
        self.insert(self._size, value)

    def delete(self, index: int) -> Any:
        """Delete and return the value at index. Time: O(n)."""
        self._validate_index(index)
        removed = self._data[index]

        for position in range(index, self._size - 1):
            self._data[position] = self._data[position + 1]

        self._size -= 1
        self._data[self._size] = None
        return removed

    def get(self, index: int) -> Any:
        """Return the value at index. Time: O(1)."""
        self._validate_index(index)
        return self._data[index]

    def set(self, index: int, value: Any) -> None:
        """Replace the value at index. Time: O(1)."""
        self._validate_index(index)
        self._data[index] = value

    def size(self) -> int:
        """Return the number of stored elements. Time: O(1)."""
        return self._size

    def is_empty(self) -> bool:
        """Return True if the array contains no elements. Time: O(1)."""
        return self._size == 0

    def capacity(self) -> int:
        """Return current storage capacity. Time: O(1)."""
        return self._capacity

    def traverse(self) -> List[Any]:
        """Return a list containing all stored elements in order. Time: O(n)."""
        return [self._data[index] for index in range(self._size)]


class Matrix:
    """Matrix stored as a two-dimensional Python list."""

    def __init__(self, rows: int, columns: int, fill_value: Any = 0) -> None:
        """Create a rows x columns matrix initialized with fill_value."""
        if rows < 1 or columns < 1:
            raise ValueError("Matrix dimensions must be positive")
        self._rows = rows
        self._columns = columns
        self._data: List[List[Any]] = [
            [fill_value for _ in range(columns)] for _ in range(rows)
        ]

    def _validate_position(self, row: int, column: int) -> None:
        """Validate row and column indexes."""
        if row < 0 or row >= self._rows:
            raise IndexError(f"Row {row} out of range for {self._rows} rows")
        if column < 0 or column >= self._columns:
            raise IndexError(
                f"Column {column} out of range for {self._columns} columns"
            )

    def insert(self, row: int, column: int, value: Any) -> None:
        """Insert value at the given position. Time: O(1)."""
        self._validate_position(row, column)
        self._data[row][column] = value

    def delete(self, row: int, column: int) -> Any:
        """Reset a position to None and return the previous value. Time: O(1)."""
        self._validate_position(row, column)
        previous = self._data[row][column]
        self._data[row][column] = None
        return previous

    def get(self, row: int, column: int) -> Any:
        """Return the value at the given position. Time: O(1)."""
        self._validate_position(row, column)
        return self._data[row][column]

    def set(self, row: int, column: int, value: Any) -> None:
        """Update the value at the given position. Time: O(1)."""
        self._validate_position(row, column)
        self._data[row][column] = value

    def display(self) -> None:
        """Print the matrix row by row. Time: O(rows * columns)."""
        for row in self._data:
            print(row)

    def row_count(self) -> int:
        """Return the number of rows. Time: O(1)."""
        return self._rows

    def column_count(self) -> int:
        """Return the number of columns. Time: O(1)."""
        return self._columns


class ArrayStack:
    """Stack implemented with a dynamic array backing store."""

    def __init__(self, initial_capacity: int = 4) -> None:
        """Initialize an empty stack."""
        self._data: List[Any] = [None] * initial_capacity
        self._size = 0
        self._capacity = initial_capacity

    def _resize(self, new_capacity: int) -> None:
        """Copy elements into a larger array."""
        new_data = [None] * new_capacity
        for index in range(self._size):
            new_data[index] = self._data[index]
        self._data = new_data
        self._capacity = new_capacity

    def push(self, value: Any) -> None:
        """Push value onto the top of the stack. Time: amortized O(1)."""
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._data[self._size] = value
        self._size += 1

    def pop(self) -> Any:
        """
        Remove and return the top value.

        Time: O(1)
        Raises EmptyStackError if the stack is empty.
        """
        if self.is_empty():
            raise EmptyStackError("Cannot pop from an empty stack")
        self._size -= 1
        value = self._data[self._size]
        self._data[self._size] = None
        return value

    def peek(self) -> Any:
        """
        Return the top value without removing it.

        Time: O(1)
        Raises EmptyStackError if the stack is empty.
        """
        if self.is_empty():
            raise EmptyStackError("Cannot peek at an empty stack")
        return self._data[self._size - 1]

    def is_empty(self) -> bool:
        """Return True if the stack has no elements. Time: O(1)."""
        return self._size == 0

    def size(self) -> int:
        """Return the number of elements in the stack. Time: O(1)."""
        return self._size

    def traverse(self) -> List[Any]:
        """Return stack contents from bottom to top. Time: O(n)."""
        return [self._data[index] for index in range(self._size)]


class ArrayQueue:
    """Queue implemented with a circular array."""

    def __init__(self, initial_capacity: int = 4) -> None:
        """Initialize an empty circular queue."""
        if initial_capacity < 1:
            raise ValueError("Initial capacity must be at least 1")
        self._capacity = initial_capacity
        self._data: List[Any] = [None] * self._capacity
        self._front = 0
        self._rear = 0
        self._size = 0

    def _resize(self) -> None:
        """Copy queue elements in order into a larger circular buffer."""
        new_capacity = self._capacity * 2
        new_data: List[Any] = [None] * new_capacity

        for index in range(self._size):
            new_data[index] = self._data[(self._front + index) % self._capacity]

        self._data = new_data
        self._capacity = new_capacity
        self._front = 0
        self._rear = self._size

    def enqueue(self, value: Any) -> None:
        """Add value to the rear of the queue. Time: amortized O(1)."""
        if self._size == self._capacity:
            self._resize()

        self._data[self._rear] = value
        self._rear = (self._rear + 1) % self._capacity
        self._size += 1

    def dequeue(self) -> Any:
        """
        Remove and return the front value.

        Time: O(1)
        Raises EmptyQueueError if the queue is empty.
        """
        if self.is_empty():
            raise EmptyQueueError("Cannot dequeue from an empty queue")

        value = self._data[self._front]
        self._data[self._front] = None
        self._front = (self._front + 1) % self._capacity
        self._size -= 1
        return value

    def peek(self) -> Any:
        """
        Return the front value without removing it.

        Time: O(1)
        Raises EmptyQueueError if the queue is empty.
        """
        if self.is_empty():
            raise EmptyQueueError("Cannot peek at an empty queue")
        return self._data[self._front]

    def is_empty(self) -> bool:
        """Return True if the queue has no elements. Time: O(1)."""
        return self._size == 0

    def size(self) -> int:
        """Return the number of elements in the queue. Time: O(1)."""
        return self._size

    def capacity(self) -> int:
        """Return current storage capacity. Time: O(1)."""
        return self._capacity

    def traverse(self) -> List[Any]:
        """Return queue contents from front to rear. Time: O(n)."""
        return [
            self._data[(self._front + index) % self._capacity]
            for index in range(self._size)
        ]


@dataclass
class ListNode:
    """Node for a singly linked list."""

    value: Any
    next: Optional["ListNode"] = None


class SinglyLinkedList:
    """Singly linked list with explicit head pointer and size tracking."""

    def __init__(self) -> None:
        """Initialize an empty linked list."""
        self._head: Optional[ListNode] = None
        self._size = 0

    def _validate_index(self, index: int, allow_end: bool = False) -> None:
        """Validate an index for indexed operations."""
        upper_bound = self._size if not allow_end else self._size + 1
        if index < 0 or index >= upper_bound:
            raise IndexError(f"Index {index} out of range for size {self._size}")

    def insert_at_beginning(self, value: Any) -> None:
        """Insert value at the front of the list. Time: O(1)."""
        self._head = ListNode(value, self._head)
        self._size += 1

    def insert_at_end(self, value: Any) -> None:
        """Insert value at the end of the list. Time: O(n)."""
        new_node = ListNode(value)
        if self._head is None:
            self._head = new_node
        else:
            current = self._head
            while current.next is not None:
                current = current.next
            current.next = new_node
        self._size += 1

    def insert_at(self, index: int, value: Any) -> None:
        """Insert value at the given index. Time: O(n)."""
        self._validate_index(index, allow_end=True)
        if index == 0:
            self.insert_at_beginning(value)
            return

        new_node = ListNode(value)
        current = self._head
        for _ in range(index - 1):
            current = current.next  # type: ignore[union-attr]
        new_node.next = current.next
        current.next = new_node
        self._size += 1

    def delete_by_value(self, value: Any) -> bool:
        """Delete the first node containing value. Time: O(n)."""
        if self._head is None:
            return False

        if self._head.value == value:
            self._head = self._head.next
            self._size -= 1
            return True

        current = self._head
        while current.next is not None:
            if current.next.value == value:
                current.next = current.next.next
                self._size -= 1
                return True
            current = current.next
        return False

    def delete_at(self, index: int) -> Any:
        """Delete and return the value at index. Time: O(n)."""
        self._validate_index(index)
        if index == 0:
            removed = self._head.value  # type: ignore[union-attr]
            self._head = self._head.next
            self._size -= 1
            return removed

        current = self._head
        for _ in range(index - 1):
            current = current.next  # type: ignore[union-attr]
        removed = current.next.value
        current.next = current.next.next
        self._size -= 1
        return removed

    def search(self, value: Any) -> int:
        """Return the index of value, or -1 if not found. Time: O(n)."""
        current = self._head
        index = 0
        while current is not None:
            if current.value == value:
                return index
            current = current.next
            index += 1
        return -1

    def get(self, index: int) -> Any:
        """Return the value at index. Time: O(n)."""
        self._validate_index(index)
        current = self._head
        for _ in range(index):
            current = current.next  # type: ignore[union-attr]
        return current.value  # type: ignore[union-attr]

    def traverse(self) -> List[Any]:
        """Return all values from head to tail. Time: O(n)."""
        values: List[Any] = []
        current = self._head
        while current is not None:
            values.append(current.value)
            current = current.next
        return values

    def size(self) -> int:
        """Return the number of nodes in the list. Time: O(1)."""
        return self._size

    def is_empty(self) -> bool:
        """Return True if the list has no nodes. Time: O(1)."""
        return self._size == 0


@dataclass
class TreeNode:
    """Node for a rooted tree."""

    value: Any
    children: List["TreeNode"] = field(default_factory=list)


class RootedTree:
    """Simple rooted tree with depth-first and breadth-first traversals."""

    def __init__(self, root_value: Any) -> None:
        """Create a tree with a single root node."""
        self.root = TreeNode(root_value)

    def add_child(self, parent: TreeNode, child_value: Any) -> TreeNode:
        """Add a child node to parent and return the new node. Time: O(1)."""
        child = TreeNode(child_value)
        parent.children.append(child)
        return child

    def search(self, value: Any) -> Optional[TreeNode]:
        """Return the first node containing value, or None. Time: O(n)."""
        def find(node: TreeNode) -> Optional[TreeNode]:
            if node.value == value:
                return node
            for child in node.children:
                result = find(child)
                if result is not None:
                    return result
            return None

        return find(self.root)

    def depth_first_traversal(self) -> List[Any]:
        """Return node values in pre-order depth-first order. Time: O(n)."""
        result: List[Any] = []

        def visit(node: TreeNode) -> None:
            result.append(node.value)
            for child in node.children:
                visit(child)

        visit(self.root)
        return result

    def breadth_first_traversal(self) -> List[Any]:
        """Return node values in breadth-first order. Time: O(n)."""
        result: List[Any] = []
        queue: ArrayQueue = ArrayQueue()
        queue.enqueue(self.root)

        while not queue.is_empty():
            node = queue.dequeue()
            result.append(node.value)
            for child in node.children:
                queue.enqueue(child)

        return result


def _print_state(state: Any) -> None:
    """Print the current state of a data structure."""
    print(f"  State: {state}")


def _demonstrate_dynamic_array() -> None:
    print("DYNAMIC ARRAY DEMONSTRATION")
    print("=" * 40)

    array = DynamicArray(initial_capacity=2)
    print("Operation: create DynamicArray(capacity=2)")
    print("  State: size=0, capacity=2, contents=[]")

    for value in [10, 20]:
        array.append(value)
        print(f"Operation: append({value})")
        print(f"  Result: size={array.size()}, capacity={array.capacity()}")
        _print_state(array.traverse())

    array.append(30)
    print("Operation: append(30) [triggers resize]")
    print(f"  Result: size={array.size()}, capacity={array.capacity()}")
    _print_state(array.traverse())

    array.insert(0, 5)
    print("Operation: insert(0, 5)")
    print(f"  Result: inserted at beginning")
    _print_state(array.traverse())

    array.insert(2, 15)
    print("Operation: insert(2, 15)")
    print(f"  Result: inserted in middle")
    _print_state(array.traverse())

    end_index = array.size()
    array.insert(end_index, 40)
    print(f"Operation: insert({end_index}, 40)")
    print("  Result: inserted at end")
    _print_state(array.traverse())

    print(f"Operation: get(2) -> {array.get(2)}")
    array.set(2, 99)
    print("Operation: set(2, 99)")
    _print_state(array.traverse())

    removed = array.delete(1)
    print(f"Operation: delete(1) -> {removed}")
    _print_state(array.traverse())

    print(f"Final contents: {array.traverse()}")
    print(f"Final size: {array.size()}, capacity: {array.capacity()}")
    print()


def _demonstrate_matrix() -> None:
    print("MATRIX DEMONSTRATION")
    print("=" * 40)

    matrix = Matrix(3, 3)
    print("Operation: create Matrix(3, 3)")
    print("  Initial matrix:")
    matrix.display()

    positions = [(0, 0, 1), (0, 2, 2), (1, 1, 3), (2, 0, 4), (2, 2, 5)]
    for row, column, value in positions:
        matrix.insert(row, column, value)
        print(f"Operation: insert({row}, {column}, {value})")

    print(f"Operation: get(1, 1) -> {matrix.get(1, 1)}")
    matrix.set(1, 1, 9)
    print("Operation: set(1, 1, 9)")

    deleted = matrix.delete(0, 2)
    print(f"Operation: delete(0, 2) -> {deleted}")

    print("  Current matrix:")
    matrix.display()
    print(f"Rows: {matrix.row_count()}, Columns: {matrix.column_count()}")
    print()


def _demonstrate_stack() -> None:
    print("STACK DEMONSTRATION")
    print("=" * 40)

    stack = ArrayStack()
    for value in [1, 2, 3, 4]:
        stack.push(value)
        print(f"Operation: push({value})")
        _print_state(stack.traverse())

    print(f"Operation: peek() -> {stack.peek()}")
    print(f"Operation: size() -> {stack.size()}")

    while not stack.is_empty():
        value = stack.pop()
        print(f"Operation: pop() -> {value}")
        _print_state(stack.traverse())

    print(f"Operation: is_empty() -> {stack.is_empty()}")

    try:
        stack.pop()
    except EmptyStackError as error:
        print(f"Operation: pop() on empty stack -> {error}")
    print()


def _demonstrate_queue() -> None:
    print("QUEUE DEMONSTRATION")
    print("=" * 40)

    queue = ArrayQueue(initial_capacity=3)
    print("Operation: create ArrayQueue(capacity=3)")

    for value in [10, 20, 30]:
        queue.enqueue(value)
        print(f"Operation: enqueue({value})")
        print(
            f"  Result: size={queue.size()}, capacity={queue.capacity()}, "
            f"contents={queue.traverse()}"
        )

    print("Operation: enqueue(40) [triggers resize]")
    queue.enqueue(40)
    print(
        f"  Result: size={queue.size()}, capacity={queue.capacity()}, "
        f"contents={queue.traverse()}"
    )

    print(f"Operation: peek() -> {queue.peek()}")
    print(f"Operation: dequeue() -> {queue.dequeue()}")
    print(f"  State after dequeue: {queue.traverse()}")

    queue.enqueue(50)
    print("Operation: enqueue(50) [demonstrates circular wrap-around]")
    print(
        f"  Result: front={queue._front}, rear={queue._rear}, "
        f"contents={queue.traverse()}"
    )

    while not queue.is_empty():
        value = queue.dequeue()
        print(f"Operation: dequeue() -> {value}")
        _print_state(queue.traverse())

    print(f"Operation: is_empty() -> {queue.is_empty()}")

    try:
        queue.dequeue()
    except EmptyQueueError as error:
        print(f"Operation: dequeue() on empty queue -> {error}")
    print()


def _demonstrate_linked_list() -> None:
    print("SINGLY LINKED LIST DEMONSTRATION")
    print("=" * 40)

    linked_list = SinglyLinkedList()

    linked_list.insert_at_beginning(3)
    print("Operation: insert_at_beginning(3)")
    _print_state(linked_list.traverse())

    linked_list.insert_at_end(7)
    print("Operation: insert_at_end(7)")
    _print_state(linked_list.traverse())

    linked_list.insert_at(1, 5)
    print("Operation: insert_at(1, 5)")
    _print_state(linked_list.traverse())

    print(f"Operation: traverse() -> {linked_list.traverse()}")
    print(f"Operation: search(5) -> {linked_list.search(5)}")
    print(f"Operation: search(99) -> {linked_list.search(99)}")

    deleted_value = linked_list.delete_by_value(5)
    print(f"Operation: delete_by_value(5) -> success={deleted_value}")
    _print_state(linked_list.traverse())

    removed = linked_list.delete_at(0)
    print(f"Operation: delete_at(0) -> {removed}")
    _print_state(linked_list.traverse())

    linked_list.insert_at_end(11)
    linked_list.insert_at_end(13)
    print(f"Operation: get(0) -> {linked_list.get(0)}")
    print(f"Final list: {linked_list.traverse()}")
    print(f"Final size: {linked_list.size()}")
    print()


def _demonstrate_rooted_tree() -> None:
    print("ROOTED TREE DEMONSTRATION")
    print("=" * 40)

    tree = RootedTree("Root")
    print("Operation: create RootedTree('Root')")

    child_a = tree.add_child(tree.root, "A")
    child_b = tree.add_child(tree.root, "B")
    tree.add_child(child_a, "A1")
    tree.add_child(child_a, "A2")
    tree.add_child(child_b, "B1")

    print("Operation: add children A, B and grandchildren A1, A2, B1")
    print(f"Operation: depth_first_traversal() -> {tree.depth_first_traversal()}")
    print(f"Operation: breadth_first_traversal() -> {tree.breadth_first_traversal()}")

    found = tree.search("A2")
    print(f"Operation: search('A2') -> {'found' if found else 'not found'}")
    print()


if __name__ == "__main__":
    _demonstrate_dynamic_array()
    _demonstrate_matrix()
    _demonstrate_stack()
    _demonstrate_queue()
    _demonstrate_linked_list()
    _demonstrate_rooted_tree()
