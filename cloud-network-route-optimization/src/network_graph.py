"""
Cloud datacenter network graph: adjacency-list topology and BFS reachability.

Data structures used:
  - Graph (adjacency list via nested dicts)
  - Hash tables (dicts) for datacenter lookup and neighbor storage
  - Set for visited-node tracking during BFS
  - Queue (collections.deque) for BFS reachability checks
"""

from __future__ import annotations

from collections import deque
from typing import Dict


class CloudNetworkGraph:
    """
    Weighted undirected graph of cloud datacenters and network links.

    Nodes are datacenter names. Edge weights are link latency in milliseconds.
    The adjacency list is a nested dictionary:

        {
            "AWS US-East": {
                "Azure East US": 12,
                "Google Cloud Iowa": 25,
            },
            ...
        }
    """

    def __init__(self) -> None:
        # Graph: adjacency list — nested dict of neighbors and latency values
        self._adjacency: Dict[str, Dict[str, int]] = {}

    @property
    def adjacency(self) -> Dict[str, Dict[str, int]]:
        """
        Return a safe copy of the adjacency list.

        The internal graph is not exposed for direct modification; callers
        receive nested dictionaries that may be read without mutating state.
        """
        return {
            node: dict(neighbors)
            for node, neighbors in self._adjacency.items()
        }

    # ------------------------------------------------------------------
    # Graph management
    # ------------------------------------------------------------------

    def add_datacenter(self, name: str) -> str:
        """
        Add a datacenter node if it does not already exist.

        Returns:
            A status message indicating whether the datacenter was added
            or already present.
        """
        # Hash table lookup: check whether the datacenter already exists
        if name in self._adjacency:
            return f"Datacenter already exists: {name}"
        self._adjacency[name] = {}
        return f"Datacenter added: {name}"

    def add_link(self, source: str, destination: str, latency: int) -> str:
        """
        Add or update a bidirectional link between two datacenters.

        Missing datacenters are created automatically. An existing link's
        latency is overwritten with the new value.

        Args:
            source: Source datacenter name.
            destination: Destination datacenter name.
            latency: Link latency in milliseconds (must be non-negative).

        Returns:
            A status message describing the action taken.

        Raises:
            ValueError: If latency is negative or source equals destination.
        """
        if latency < 0:
            raise ValueError(f"Latency must be non-negative, got {latency}")
        if source == destination:
            raise ValueError(
                f"Self-links are not allowed: '{source}' -> '{destination}'"
            )

        # Automatically add missing datacenters
        if source not in self._adjacency:
            self.add_datacenter(source)
        if destination not in self._adjacency:
            self.add_datacenter(destination)

        # Bidirectional link (update if already present)
        existed = destination in self._adjacency[source]
        self._adjacency[source][destination] = latency
        self._adjacency[destination][source] = latency

        action = "updated" if existed else "added"
        return (
            f"Link {action}: {source} <-> {destination} ({latency} ms)"
        )

    def remove_link(self, source: str, destination: str) -> bool:
        """
        Remove a bidirectional link without deleting either datacenter.

        Returns:
            True if the link existed and was removed; False otherwise.
        """
        if (
            source not in self._adjacency
            or destination not in self._adjacency
            or destination not in self._adjacency[source]
        ):
            return False

        del self._adjacency[source][destination]
        # Mirror removal; tolerate an already-asymmetric adjacency list
        if source in self._adjacency[destination]:
            del self._adjacency[destination][source]
        return True

    def get_neighbors(self, datacenter: str) -> Dict[str, int]:
        """
        Return the neighbors and latencies for a datacenter.

        Unknown datacenters return an empty dictionary rather than raising.
        """
        # Hash table: datacenter lookup
        neighbors = self._adjacency.get(datacenter)
        if neighbors is None:
            return {}
        return dict(neighbors)

    def display_network(self) -> None:
        """Print every datacenter and its current links in a readable format."""
        if not self._adjacency:
            print("  (empty network — no datacenters)")
            return

        for dc in sorted(self._adjacency):
            neighbors = self._adjacency[dc]
            if not neighbors:
                print(f"  {dc}: (no links)")
                continue
            links = ", ".join(
                f"{neighbor} ({latency} ms)"
                for neighbor, latency in sorted(neighbors.items())
            )
            print(f"  {dc}: {links}")

    # ------------------------------------------------------------------
    # BFS reachability
    # ------------------------------------------------------------------

    def is_reachable(self, source: str, destination: str) -> bool:
        """
        Determine whether destination is reachable from source via BFS.

        Uses collections.deque as the BFS queue and a set for visited nodes.
        Disconnected nodes and identical source/destination are handled.

        Args:
            source: Starting datacenter.
            destination: Target datacenter.

        Returns:
            True if a path exists (including source == destination);
            False if either node is unknown or no path exists.
        """
        if source not in self._adjacency or destination not in self._adjacency:
            return False

        if source == destination:
            return True

        # Queue: BFS frontier
        queue: deque[str] = deque([source])
        # Set: visited nodes
        visited: set[str] = {source}

        while queue:
            current = queue.popleft()
            for neighbor in self._adjacency[current]:
                if neighbor in visited:
                    continue
                if neighbor == destination:
                    return True
                visited.add(neighbor)
                queue.append(neighbor)

        return False
