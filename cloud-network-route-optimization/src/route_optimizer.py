"""
Lowest-latency route selection for cloud network topologies.

Data structures used:
  - Priority queue (heapq) for Dijkstra's algorithm
  - Hash tables (dicts) for distances, previous nodes, lookups, and route results
  - Set for visited-node tracking
"""

from __future__ import annotations

import heapq
from typing import Dict, List, Optional

from .models import RouteResult
from .network_graph import CloudNetworkGraph


class CloudRouteOptimizer:
    """
    Computes lowest-latency routes over a CloudNetworkGraph using Dijkstra.

    Separates route optimization from graph mutation so topology management
    and path selection can evolve independently.
    """

    def __init__(self, graph: CloudNetworkGraph) -> None:
        """
        Bind this optimizer to an existing cloud network graph.

        Args:
            graph: The CloudNetworkGraph whose topology will be queried.
        """
        self._graph = graph

    def shortest_path(self, source: str, destination: str) -> RouteResult:
        """
        Find the lowest-latency route using Dijkstra's algorithm.

        Uses a priority queue (heapq) to process the lowest-latency candidate
        first, hash tables for distance/previous-node tracking, and a set to
        avoid reprocessing settled nodes.

        Args:
            source: Starting datacenter.
            destination: Target datacenter.

        Returns:
            A RouteResult with path, total_latency, and reachable flag.

        Raises:
            KeyError: If source or destination is not in the network.
        """
        # Hash table: datacenter lookup — reject unknown nodes
        adjacency = self._graph.adjacency
        if source not in adjacency:
            raise KeyError(f"Unknown source datacenter: {source}")
        if destination not in adjacency:
            raise KeyError(f"Unknown destination datacenter: {destination}")

        # Identical source and destination
        if source == destination:
            return {
                "path": [source],
                "total_latency": 0,
                "reachable": True,
            }

        # Hash tables: distance tracking and previous-node tracking
        distances: Dict[str, float] = {node: float("inf") for node in adjacency}
        previous: Dict[str, Optional[str]] = {node: None for node in adjacency}
        distances[source] = 0

        # Priority queue (min-heap): (distance, node)
        priority_queue: List[tuple[float, str]] = [(0, source)]
        # Set: track visited (settled) nodes to prevent repeated processing
        visited: set[str] = set()

        while priority_queue:
            current_dist, current = heapq.heappop(priority_queue)

            # Skip stale priority-queue entries when a better distance exists
            if current_dist > distances[current]:
                continue
            if current in visited:
                continue
            visited.add(current)

            if current == destination:
                break

            for neighbor, latency in adjacency[current].items():
                if neighbor in visited:
                    continue
                candidate = current_dist + latency
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    previous[neighbor] = current
                    heapq.heappush(priority_queue, (candidate, neighbor))

        if distances[destination] == float("inf"):
            return {
                "path": [],
                "total_latency": None,
                "reachable": False,
            }

        # Hash table: reconstructed routing information via previous-node dict
        path = self._reconstruct_path(previous, source, destination)
        return {
            "path": path,
            "total_latency": int(distances[destination]),
            "reachable": True,
        }

    def _reconstruct_path(
        self,
        previous: Dict[str, Optional[str]],
        source: str,
        destination: str,
    ) -> List[str]:
        """Rebuild the route by walking the previous-node dictionary backward."""
        path: List[str] = []
        current: Optional[str] = destination
        while current is not None:
            path.append(current)
            if current == source:
                break
            current = previous[current]
        path.reverse()
        return path
