"""
Lowest-latency route selection for cloud network topologies.

Data structures used:
  - Priority queue (heapq) for Dijkstra's algorithm
  - Hash tables (dicts) for distances, previous nodes, lookups, and route results
  - Set for visited-node tracking
  - OrderedDict for bounded LRU route and source-tree caches (Phase 3)
"""

from __future__ import annotations

import heapq
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Union

from .models import RouteResult
from .network_graph import CloudNetworkGraph

# Cache key: (source, destination, topology_version)
_CacheKey = Tuple[str, str, int]
# Source-tree key: (source, topology_version)
_SourceTreeKey = Tuple[str, int]
_MetricsValue = Union[int, float, bool]


class CloudRouteOptimizer:
    """
    Computes lowest-latency routes over a CloudNetworkGraph using Dijkstra.

    Separates route optimization from graph mutation so topology management
    and path selection can evolve independently.

    Phase 3 adds bounded LRU caching keyed by topology version so repeated
    queries avoid recomputing Dijkstra while mutations invalidate safely.
    """

    def __init__(
        self,
        graph: CloudNetworkGraph,
        cache_capacity: int = 128,
        source_tree_capacity: int = 16,
    ) -> None:
        """
        Bind this optimizer to an existing cloud network graph.

        Args:
            graph: The CloudNetworkGraph whose topology will be queried.
            cache_capacity: Max source-destination route results to retain.
                Use 0 to disable route caching. Must not be negative.
            source_tree_capacity: Max single-source Dijkstra trees to retain.
                Use 0 to disable source-tree memoization (early-exit Dijkstra
                only). Must not be negative.

        Raises:
            ValueError: If either capacity is negative.
        """
        if cache_capacity < 0:
            raise ValueError(
                f"cache_capacity must be non-negative, got {cache_capacity}"
            )
        if source_tree_capacity < 0:
            raise ValueError(
                f"source_tree_capacity must be non-negative, "
                f"got {source_tree_capacity}"
            )

        self._graph = graph
        self._cache_capacity = cache_capacity
        self._source_tree_capacity = source_tree_capacity

        # PHASE 3 OPTIMIZATION:
        # Bounded LRU of (source, destination, topology_version) -> RouteResult.
        # Repeated identical route requests return in approximately O(1) time
        # (plus O(P) for a defensive path copy) instead of rerunning Dijkstra.
        # OrderedDict moves hits to the end; the front entry is least recently used.
        self._route_cache: OrderedDict[_CacheKey, RouteResult] = OrderedDict()
        self._cache_hits: int = 0
        self._cache_misses: int = 0

        # PHASE 3 OPTIMIZATION:
        # Bounded LRU of complete single-source shortest-path trees.
        # Memory trade-off: each entry stores O(V) distance/previous maps, so
        # capacity is kept small (default 16) to avoid O(V²) growth when many
        # sources are queried. Enables multiple destination lookups from one
        # source to share a single Dijkstra execution.
        self._source_tree_cache: OrderedDict[
            _SourceTreeKey,
            Tuple[Dict[str, float], Dict[str, Optional[str]]],
        ] = OrderedDict()
        self._dijkstra_executions: int = 0

        self._last_metrics: Dict[str, _MetricsValue] = {
            "nodes_settled": 0,
            "edges_examined": 0,
            "heap_pushes": 0,
            "heap_pops": 0,
            "cache_hit": False,
            "source_tree_hit": False,
            "dijkstra_executed": False,
            "execution_time_seconds": 0.0,
        }

    def clear_cache(self) -> None:
        """Clear route and source-tree caches and reset hit/miss counters."""
        self._route_cache.clear()
        self._source_tree_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def cache_info(self) -> Dict[str, int]:
        """
        Report route-cache statistics.

        Returns:
            hits, misses, current size, and configured capacity.
        """
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "current_size": len(self._route_cache),
            "capacity": self._cache_capacity,
        }

    def last_run_metrics(self) -> Dict[str, _MetricsValue]:
        """Return performance counters from the most recent shortest_path call."""
        return dict(self._last_metrics)

    def dijkstra_execution_count(self) -> int:
        """Return how many full Dijkstra runs have executed since construction."""
        return self._dijkstra_executions

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
        started = time.perf_counter()

        # PHASE 3 OPTIMIZATION:
        # Avoid copying the entire O(V + E) adjacency structure before every
        # shortest-path calculation. The optimizer now reads neighbors through
        # controlled graph access methods.
        if not self._graph.contains_datacenter(source):
            raise KeyError(f"Unknown source datacenter: {source}")
        if not self._graph.contains_datacenter(destination):
            raise KeyError(f"Unknown destination datacenter: {destination}")

        version = self._graph.topology_version
        cache_key: _CacheKey = (source, destination, version)

        # PHASE 3 OPTIMIZATION:
        # Serve repeated (source, destination, version) queries from the LRU
        # without rerunning Dijkstra.
        if self._cache_capacity > 0 and cache_key in self._route_cache:
            self._cache_hits += 1
            self._route_cache.move_to_end(cache_key)
            result = self._copy_route_result(self._route_cache[cache_key])
            self._last_metrics = {
                "nodes_settled": 0,
                "edges_examined": 0,
                "heap_pushes": 0,
                "heap_pops": 0,
                "cache_hit": True,
                "source_tree_hit": False,
                "dijkstra_executed": False,
                "execution_time_seconds": time.perf_counter() - started,
            }
            return result

        if self._cache_capacity > 0:
            self._cache_misses += 1

        # Identical source and destination
        if source == destination:
            result = {
                "path": [source],
                "total_latency": 0,
                "reachable": True,
            }
            self._store_route(cache_key, result)
            self._last_metrics = {
                "nodes_settled": 0,
                "edges_examined": 0,
                "heap_pushes": 0,
                "heap_pops": 0,
                "cache_hit": False,
                "source_tree_hit": False,
                "dijkstra_executed": False,
                "execution_time_seconds": time.perf_counter() - started,
            }
            return self._copy_route_result(result)

        source_tree_hit = False
        distances: Dict[str, float]
        previous: Dict[str, Optional[str]]
        run_metrics: Dict[str, int]

        tree_key: _SourceTreeKey = (source, version)
        if (
            self._source_tree_capacity > 0
            and tree_key in self._source_tree_cache
        ):
            # PHASE 3 OPTIMIZATION:
            # Reuse a cached single-source tree for a different destination
            # under the same topology version — one Dijkstra, many lookups.
            self._source_tree_cache.move_to_end(tree_key)
            distances, previous = self._source_tree_cache[tree_key]
            source_tree_hit = True
            run_metrics = {
                "nodes_settled": 0,
                "edges_examined": 0,
                "heap_pushes": 0,
                "heap_pops": 0,
            }
        else:
            build_full_tree = self._source_tree_capacity > 0
            distances, previous, run_metrics = self._run_dijkstra(
                source,
                destination=None if build_full_tree else destination,
            )
            if build_full_tree:
                self._store_source_tree(tree_key, distances, previous)

        if distances.get(destination, float("inf")) == float("inf"):
            result = {
                "path": [],
                "total_latency": None,
                "reachable": False,
            }
        else:
            # Hash table: reconstructed routing information via previous-node dict
            path = self._reconstruct_path(previous, source, destination)
            result = {
                "path": path,
                "total_latency": int(distances[destination]),
                "reachable": True,
            }

        self._store_route(cache_key, result)
        self._purge_stale_cache_entries(version)
        self._last_metrics = {
            "nodes_settled": run_metrics["nodes_settled"],
            "edges_examined": run_metrics["edges_examined"],
            "heap_pushes": run_metrics["heap_pushes"],
            "heap_pops": run_metrics["heap_pops"],
            "cache_hit": False,
            "source_tree_hit": source_tree_hit,
            "dijkstra_executed": not source_tree_hit,
            "execution_time_seconds": time.perf_counter() - started,
        }
        return self._copy_route_result(result)

    def _run_dijkstra(
        self,
        source: str,
        destination: Optional[str],
    ) -> Tuple[Dict[str, float], Dict[str, Optional[str]], Dict[str, int]]:
        """
        Execute Dijkstra from source.

        If destination is provided, stop early once that node is settled.
        If destination is None, compute the full single-source tree.

        PHASE 3 OPTIMIZATION:
        Neighbor iteration uses iter_neighbors() — no full adjacency copy.
        Distances are initialized lazily so we allocate O(visited) entries
        rather than pre-building a dict for every node on huge graphs when
        early exit applies; full-tree mode still visits all reachable nodes.
        """
        self._dijkstra_executions += 1

        # Hash tables: distance tracking and previous-node tracking
        distances: Dict[str, float] = {source: 0.0}
        previous: Dict[str, Optional[str]] = {source: None}

        # Priority queue (min-heap): (distance, node)
        priority_queue: List[Tuple[float, str]] = [(0.0, source)]
        # Set: track visited (settled) nodes to prevent repeated processing.
        # PHASE 3 OPTIMIZATION:
        # Keep the visited set: once a nonnegative-weight node is settled,
        # its distance is final. Skipping settled nodes avoids re-examining
        # their adjacency lists when stale heap entries are later popped.
        visited: set[str] = set()

        nodes_settled = 0
        edges_examined = 0
        heap_pushes = 1
        heap_pops = 0

        while priority_queue:
            current_dist, current = heapq.heappop(priority_queue)
            heap_pops += 1

            # Skip stale priority-queue entries when a better distance exists
            if current_dist > distances.get(current, float("inf")):
                continue
            if current in visited:
                continue
            visited.add(current)
            nodes_settled += 1

            if destination is not None and current == destination:
                break

            for neighbor, latency in self._graph.iter_neighbors(current):
                edges_examined += 1
                if neighbor in visited:
                    continue
                candidate = current_dist + latency
                best = distances.get(neighbor, float("inf"))
                if candidate < best:
                    distances[neighbor] = candidate
                    previous[neighbor] = current
                    heapq.heappush(priority_queue, (candidate, neighbor))
                    heap_pushes += 1

        metrics = {
            "nodes_settled": nodes_settled,
            "edges_examined": edges_examined,
            "heap_pushes": heap_pushes,
            "heap_pops": heap_pops,
        }
        return distances, previous, metrics

    def _store_route(self, key: _CacheKey, result: RouteResult) -> None:
        """Insert a route into the bounded LRU cache if caching is enabled."""
        if self._cache_capacity <= 0:
            return
        stored = self._copy_route_result(result)
        if key in self._route_cache:
            self._route_cache.move_to_end(key)
        self._route_cache[key] = stored
        while len(self._route_cache) > self._cache_capacity:
            self._route_cache.popitem(last=False)

    def _store_source_tree(
        self,
        key: _SourceTreeKey,
        distances: Dict[str, float],
        previous: Dict[str, Optional[str]],
    ) -> None:
        """Insert a single-source tree into the bounded source-tree LRU."""
        if self._source_tree_capacity <= 0:
            return
        if key in self._source_tree_cache:
            self._source_tree_cache.move_to_end(key)
        self._source_tree_cache[key] = (distances, previous)
        while len(self._source_tree_cache) > self._source_tree_capacity:
            self._source_tree_cache.popitem(last=False)

    def _purge_stale_cache_entries(self, current_version: int) -> None:
        """
        PHASE 3 OPTIMIZATION:
        Periodically drop cache entries whose topology_version no longer
        matches the live graph so obsolete keys do not accumulate after
        many mutations (versioned keys already prevent incorrect hits).
        """
        stale_routes = [
            key for key in self._route_cache if key[2] != current_version
        ]
        for key in stale_routes:
            del self._route_cache[key]

        stale_trees = [
            key
            for key in self._source_tree_cache
            if key[1] != current_version
        ]
        for key in stale_trees:
            del self._source_tree_cache[key]

    @staticmethod
    def _copy_route_result(result: RouteResult) -> RouteResult:
        """Return a safe copy so callers cannot mutate cached path lists."""
        return {
            "path": list(result["path"]),
            "total_latency": result["total_latency"],
            "reachable": result["reachable"],
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
            current = previous.get(current)
        path.reverse()
        return path
