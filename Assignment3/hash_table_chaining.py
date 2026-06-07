"""
Hash table with chaining for collision resolution.

Uses a universal-style hash function and dynamic resizing based on load factor.
Designed for clarity and future extension (e.g., benchmarking hooks).
"""

import random
from typing import Any, List, Optional, Tuple

# Large prime used in the universal hash function denominator step.
_DEFAULT_PRIME = 2_147_483_647

# Load-factor thresholds that trigger table resizing.
_LOAD_FACTOR_GROW_THRESHOLD = 0.75
_LOAD_FACTOR_SHRINK_THRESHOLD = 0.25


class HashTableChaining:
    """
    Hash table that resolves collisions by chaining key-value pairs in lists.

    Each bucket is a Python list of (key, value) pairs. The table grows when
    load factor exceeds 0.75 and shrinks when it falls below 0.25, never
    dropping below the initial capacity.
    """

    def __init__(self, initial_capacity: int = 8) -> None:
        if initial_capacity < 1:
            raise ValueError("initial_capacity must be at least 1")

        self._initial_capacity = initial_capacity
        self._capacity = initial_capacity
        self._size = 0

        # Universal hash constants: a in [1, p-1], b in [0, p-1].
        self._p = _DEFAULT_PRIME
        self._a = random.randint(1, self._p - 1)
        self._b = random.randint(0, self._p - 1)

        # Table storage: list of chains (no dict used for main storage).
        self._table: List[List[Tuple[Any, Any]]] = [[] for _ in range(self._capacity)]

    @property
    def size(self) -> int:
        """Number of key-value pairs currently stored."""
        return self._size

    @property
    def capacity(self) -> int:
        """Current number of buckets in the table."""
        return self._capacity

    @property
    def load_factor(self) -> float:
        """Ratio of stored elements to table capacity."""
        if self._capacity == 0:
            return 0.0
        return self._size / self._capacity

    def _hash(self, key: Any) -> int:
        """
        Universal-style hash function:

            h(k) = ((a * hash(k) + b) mod p) mod m

        where m is the table size, p is a large prime, and a, b are random
        constants chosen at construction time. Python's hash() supplies a
        numeric representation for string and integer keys.
        """
        key_hash = hash(key)
        return ((self._a * key_hash + self._b) % self._p) % self._capacity

    def insert(self, key: Any, value: Any) -> None:
        """
        Add a new key-value pair or update the value if the key already exists.

        The key is hashed to a bucket index. If multiple keys map to the same
        index (a collision), the pair is appended to that bucket's chain list.
        Resizing is triggered when the load factor exceeds the grow threshold.
        """
        index = self._hash(key)
        chain = self._table[index]

        for i, (existing_key, _) in enumerate(chain):
            if existing_key == key:
                chain[i] = (key, value)
                return

        chain.append((key, value))
        self._size += 1

        if self.load_factor > _LOAD_FACTOR_GROW_THRESHOLD:
            self._resize(self._capacity * 2)

    def search(self, key: Any) -> Optional[Any]:
        """
        Return the value associated with key, or None if the key is not found.

        The bucket is located via the hash function, then the chain at that
        bucket is scanned linearly for a matching key.
        """
        index = self._hash(key)
        for existing_key, value in self._table[index]:
            if existing_key == key:
                return value
        return None

    def delete(self, key: Any) -> bool:
        """
        Remove the key-value pair for key.

        Returns True if the key was found and removed, False otherwise.
        Resizing is triggered when the load factor falls below the shrink
        threshold (but capacity never drops below the initial capacity).
        """
        index = self._hash(key)
        chain = self._table[index]

        for i, (existing_key, _) in enumerate(chain):
            if existing_key == key:
                del chain[i]
                self._size -= 1

                if (
                    self.load_factor < _LOAD_FACTOR_SHRINK_THRESHOLD
                    and self._capacity > self._initial_capacity
                ):
                    new_capacity = max(self._initial_capacity, self._capacity // 2)
                    if new_capacity < self._capacity:
                        self._resize(new_capacity)

                return True

        return False

    def _resize(self, new_capacity: int) -> None:
        """
        Rehash all existing key-value pairs into a table with new_capacity.

        Bucket indices change when m changes, so every entry must be inserted
        into a fresh table rather than moved by index.
        """
        old_table = self._table

        self._capacity = new_capacity
        self._table = [[] for _ in range(self._capacity)]

        for chain in old_table:
            for key, value in chain:
                index = self._hash(key)
                self._table[index].append((key, value))

    def chain_lengths(self) -> List[int]:
        """Return the length of each bucket chain (useful for collision demos)."""
        return [len(chain) for chain in self._table]

    def __repr__(self) -> str:
        return (
            f"HashTableChaining(size={self._size}, capacity={self._capacity}, "
            f"load_factor={self.load_factor:.2f})"
        )


def _print_table_state(label: str, table: HashTableChaining) -> None:
    """Print capacity, size, load factor, and per-bucket chain lengths."""
    print(f"{label}")
    print(f"  {table}")
    print(f"  Chain lengths: {table.chain_lengths()}")
    print()


def _run_test_case(label: str, action, table: HashTableChaining) -> None:
    """Execute a demo action and print the result alongside table state."""
    print(f"{label}")
    result = action()
    if result is not None:
        print(f"  Result: {result}")
    print(f"  {table}")
    print()


if __name__ == "__main__":
    print("Hash Table with Chaining — demonstration\n")

    # Small initial capacity makes collisions likely for the demo.
    table = HashTableChaining(initial_capacity=4)
    _print_table_state("Initial empty table", table)

    print("Inserting key-value pairs (strings and integers):")
    pairs = [
        ("apple", 10),
        ("banana", 20),
        (42, "forty-two"),
        ("cherry", 30),
        ("date", 40),
        (99, "ninety-nine"),
        ("elderberry", 50),
        ("fig", 60),
        ("grape", 70),
    ]
    for key, value in pairs:
        table.insert(key, value)
        print(f"  insert({key!r}, {value!r}) -> size={table.size}, load_factor={table.load_factor:.2f}")

    print()
    _print_table_state("After inserts (note collisions in chain lengths)", table)

    _run_test_case(
        "Search existing key 'banana'",
        lambda: table.search("banana"),
        table,
    )

    _run_test_case(
        "Search existing integer key 42",
        lambda: table.search(42),
        table,
    )

    _run_test_case(
        "Search missing key 'mango'",
        lambda: table.search("mango"),
        table,
    )

    _run_test_case(
        "Update existing key 'apple' to value 100",
        lambda: table.insert("apple", 100) or table.search("apple"),
        table,
    )

    _run_test_case(
        "Delete existing key 'date'",
        lambda: table.delete("date"),
        table,
    )

    _run_test_case(
        "Attempt to delete missing key 'mango'",
        lambda: table.delete("mango"),
        table,
    )

    print("Deleting keys to trigger shrink resize:")
    keys_to_delete = ["banana", "cherry", "elderberry", "fig", "grape"]
    for key in keys_to_delete:
        deleted = table.delete(key)
        print(
            f"  delete({key!r}) -> {deleted}, "
            f"capacity={table.capacity}, load_factor={table.load_factor:.2f}"
        )

    print()
    _print_table_state("Final table state after deletions", table)

    print("Remaining entries:")
    for key in ["apple", 42, 99]:
        print(f"  search({key!r}) -> {table.search(key)!r}")
