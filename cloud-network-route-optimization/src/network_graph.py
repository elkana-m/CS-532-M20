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
from typing import Dict, Iterator, Tuple


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
        # PHASE 3 OPTIMIZATION:
        # Topology version increments only on real structural or weight changes.
        # Route caches key on this version so stale results invalidate safely
        # without scanning or clearing the entire cache on every mutation.
        self._topology_version: int = 0
        # PHASE 3 OPTIMIZATION:
        # Maintain an undirected edge count incrementally so link_count() is
        # O(1) instead of scanning all adjacency lists on large graphs.
        self._edge_count: int = 0

    @property
    def topology_version(self) -> int:
        """
        Monotonic version of the graph structure and link weights.

        Used by route caches to invalidate results after topology changes.
        """
        return self._topology_version

    @property
    def adjacency(self) -> Dict[str, Dict[str, int]]:
        """
        Return a safe copy of the adjacency list.

        Kept for debugging and tests. Optimized routing must not use this
        property; prefer contains_datacenter / iter_neighbors instead.
        """
        return {
            node: dict(neighbors)
            for node, neighbors in self._adjacency.items()
        }

    # ------------------------------------------------------------------
    # PHASE 3: controlled read-only graph access
    # ------------------------------------------------------------------

    def contains_datacenter(self, name: str) -> bool:
        """Return True if the datacenter exists. O(1) average lookup."""
        # Hash table membership — no graph copy required
        return name in self._adjacency

    def datacenters(self) -> Tuple[str, ...]:
        """
        Return an immutable snapshot of datacenter names.

        Copies only node identifiers (O(V)), not the full edge structure.
        """
        return tuple(self._adjacency.keys())

    def iter_neighbors(self, datacenter: str) -> Iterator[Tuple[str, int]]:
        """
        Iterate (neighbor, latency) pairs without copying the whole graph.

        Yields directly from the internal neighbor mapping. Callers must not
        retain references for mutation; the optimizer only reads values.
        """
        # PHASE 3 OPTIMIZATION:
        # Avoid copying the entire O(V + E) adjacency structure before every
        # shortest-path calculation. The optimizer now reads neighbors through
        # controlled graph access methods.
        neighbors = self._adjacency.get(datacenter)
        if not neighbors:
            return
        yield from neighbors.items()

    def datacenter_count(self) -> int:
        """Return the number of datacenter nodes. O(1)."""
        return len(self._adjacency)

    def link_count(self) -> int:
        """Return the number of undirected links. O(1)."""
        return self._edge_count

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
        # PHASE 3 OPTIMIZATION:
        # Increment topology version only when the graph actually changes so
        # cached routes keyed by version remain valid for no-op duplicates.
        self._topology_version += 1
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
        if existed and self._adjacency[source][destination] == latency:
            # PHASE 3 OPTIMIZATION:
            # Same latency is a no-op — do not bump topology_version so caches
            # stay valid when callers re-assert an unchanged weight.
            return (
                f"Link updated: {source} <-> {destination} ({latency} ms)"
            )

        self._adjacency[source][destination] = latency
        self._adjacency[destination][source] = latency
        if not existed:
            self._edge_count += 1
        # PHASE 3 OPTIMIZATION:
        # New links and real weight changes invalidate cached routes via
        # topology_version; see CloudRouteOptimizer cache keys.
        self._topology_version += 1

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
        self._edge_count -= 1
        # PHASE 3 OPTIMIZATION:
        # Successful removal changes connectivity — bump version so cached
        # routes and reachability results cannot be reused incorrectly.
        self._topology_version += 1
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

        PHASE 3 OPTIMIZATION:
        Reads neighbors directly from the internal adjacency lists (no full
        graph copy). Stops immediately when the destination is found.
        Worst-case time remains O(V + E).

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
            # Direct neighbor iteration — no adjacency copy
            for neighbor in self._adjacency[current]:
                if neighbor in visited:
                    continue
                if neighbor == destination:
                    return True
                visited.add(neighbor)
                queue.append(neighbor)

        return False
