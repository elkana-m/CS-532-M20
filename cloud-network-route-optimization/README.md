# Cloud Network Route Optimization and Failover Management

Proof-of-concept system for selecting lowest-latency routes between cloud
datacenters and recovering from network link failures.

## Purpose

Multi-cloud applications often span regions and providers (AWS, Azure, Google
Cloud). Traffic must traverse interconnects whose latency varies, and links can
fail. This project models that problem as a weighted undirected graph and
demonstrates:

- Building and inspecting a cloud network topology
- Computing the lowest-latency path between datacenters
- Checking reachability after failures
- Recalculating failover routes when a link is removed
- Updating link latency and observing route changes

## Real-World Problem Being Modeled

Cloud providers operate regional datacenters connected by backbone and peering
links. An application that must move data from **AWS US-East** to **AWS US-West**
may prefer a multi-hop path through Azure or Google Cloud if that path has
lower total latency. When a critical hop fails, the control plane must detect
that an alternate route still exists and switch to it quickly.

This proof of concept captures that decision logic in a small, extensible
Python codebase—without yet adding APIs, databases, or live cloud integrations.

## Data Structures Used

| Structure | Role |
|---|---|
| **Graph** (nested-dict adjacency list) | Datacenters as nodes; latency (ms) as edge weights |
| **Priority queue** (`heapq`) | Dijkstra expands the lowest-latency candidate first |
| **Hash tables** (`dict`) | Distances, previous-node tracking, lookups, route results |
| **Set** | Visited nodes (Dijkstra settlement and BFS) |
| **Queue** (`collections.deque`) | BFS frontier for reachability checks |

## Dijkstra’s Role

`CloudRouteOptimizer.shortest_path` runs Dijkstra’s algorithm to return the
minimum total-latency path between two datacenters. Results are structured as:

```python
{
    "path": ["AWS US-East", "Azure East US", "..."],
    "total_latency": 49,
    "reachable": True,
}
```

Unreachable destinations return an empty path, `total_latency: None`, and
`reachable: False`.

## BFS’s Role

`CloudNetworkGraph.is_reachable` uses breadth-first search to answer a simpler
question after a failure: *is the destination still connected at all?* This is
cheaper than a full weighted search when only connectivity matters.

## Project Structure

```text
cloud-network-route-optimization/
├── src/
│   ├── __init__.py
│   ├── models.py                 # RouteResult TypedDict
│   ├── network_graph.py          # Topology + BFS + controlled access
│   ├── route_optimizer.py        # Dijkstra + LRU caches + metrics
│   ├── sample_topology.py        # Example datacenters and links
│   ├── topology_generator.py     # Synthetic sparse/dense networks
│   └── main.py                   # Phase 2 + Phase 3 demonstration
├── tests/
│   ├── __init__.py
│   ├── test_network_graph.py
│   ├── test_route_optimizer.py
│   ├── test_failover.py
│   ├── test_phase2_optimizations.py
│   └── test_stress.py
├── benchmarks/
│   ├── __init__.py
│   └── benchmark_routes.py
├── benchmark_results.csv         # Written by the benchmark runner
├── README.md
└── requirements.txt
```

## How to Run the Demonstration

From the project root:

```bash
python -m src.main
```

The demonstration prints labeled sections suitable for academic report
screenshots:

- `CLOUD NETWORK TOPOLOGY`
- `INITIAL ROUTE SELECTION`
- `LINK FAILURE SIMULATION`
- `FAILOVER ROUTE`
- `LATENCY UPDATE`
- `PHASE 3 OPTIMIZATION DEMONSTRATION`

## How to Run Tests

From the project root (optionally add `-v` so each test case name is printed):

```bash
python -m unittest discover -s tests -v
```

Run a single file with the same verbose output:

```bash
python -m unittest tests.test_network_graph -v
python -m unittest tests.test_route_optimizer -v
python -m unittest tests.test_failover -v
python -m unittest tests.test_phase2_optimizations -v
python -m unittest tests.test_stress -v
```

Tests use Python’s built-in `unittest` module; no third-party test runner is
required.

### Test cases

**`tests/test_network_graph.py`** — graph management and BFS

- `test_empty_network`
- `test_adding_a_datacenter`
- `test_adding_same_datacenter_twice`
- `test_adding_and_retrieving_a_link`
- `test_updating_link_latency`
- `test_negative_latency_rejection`
- `test_self_link_rejection`
- `test_removing_an_existing_link`
- `test_removing_a_missing_link`
- `test_unknown_neighbor_lookup`
- `test_bfs_source_equals_destination`
- `test_bfs_disconnected_nodes`
- `test_adjacency_returns_safe_copy`

**`tests/test_route_optimizer.py`** — Dijkstra shortest-path

- `test_lowest_latency_route_selection`
- `test_multiple_routes_different_costs`
- `test_equal_cost_alternative_routes`
- `test_unknown_source`
- `test_unknown_destination`
- `test_source_equals_destination`
- `test_unreachable_destination`
- `test_correct_path_reconstruction`
- `test_correct_total_latency`

**`tests/test_failover.py`** — failure, failover, and latency updates

- `test_link_failure_with_valid_alternate_route`
- `test_link_failure_with_no_remaining_route`
- `test_route_recalculation_after_failure`
- `test_route_restoration`
- `test_route_change_after_latency_update`

**`tests/test_phase2_optimizations.py`** — caching, versioning, no full-graph copy

**`tests/test_stress.py`** — large/sparse/chain/star topologies and cache stress

## Phase 3: Performance Optimization and Scalability

Phase 2 copied the entire adjacency list (`O(V + E)` time and memory) before
every Dijkstra call via `CloudNetworkGraph.adjacency`. On large topologies that
copy dominated route calculation and allocated a full duplicate of the graph
on each query.

### Controlled neighbor access

`CloudRouteOptimizer` no longer reads `adjacency`. It uses:

- `contains_datacenter()` — O(1) average membership
- `iter_neighbors()` — iterate edges in place without copying the graph
- `datacenters()` / `datacenter_count()` / `link_count()` — lightweight metadata

The `adjacency` property remains for debugging and tests only.

### Topology versioning

`CloudNetworkGraph.topology_version` increments only when the graph actually
changes (new datacenter, new link, real latency change, successful link
removal). Duplicate datacenter inserts, missing-link removals, and same-latency
re-asserts do not bump the version. Route cache keys include this version so
stale results cannot be reused after mutations.

### Bounded LRU route caching

`CloudRouteOptimizer` keeps an `OrderedDict` LRU of

`(source, destination, topology_version) -> RouteResult`

with a configurable `cache_capacity` (default 128; `0` disables caching).

- Hits move entries to the most-recent end
- Inserts evict the least-recently used entry when over capacity
- Returned results defensively copy the path list
- Obsolete-version entries are purged periodically

An optional small **source-tree LRU** (default 16 entries) memoizes a full
single-source Dijkstra tree so many destinations from one source share one
shortest-path computation. Each tree costs `O(V)` memory, so the bound prevents
`O(V²)` growth.

### Why the cache is bounded

Unbounded `(source, destination)` maps grow without limit under exploratory or
automated workloads. A fixed capacity caps memory while still accelerating the
hot routes a control plane revisits.

### Theoretical complexity

```text
Graph storage: O(V + E)
Dijkstra with binary heap: O((V + E) log V)
BFS reachability: O(V + E)
Uncached route space: O(V + E)
Cached repeated route lookup: approximately O(1), excluding safe result copying
```

A cache hit may still take `O(P)` time to copy a returned path of length `P`
when defensive copying is used.

### Benchmark methodology

`python -m benchmarks.benchmark_routes` generates connected sparse networks
(100 → 10,000 nodes), compares uncached Dijkstra, cold optimized miss, warm
cache hit, and post-mutation recalculation, records median `perf_counter`
runtime and `tracemalloc` peak memory, and writes `benchmark_results.csv`.

### Stress-testing approach

`tests/test_stress.py` exercises thousands of nodes, chain/star shapes,
disconnects, equal-cost paths, rapid failure/restore, latency churn, cache
eviction/invalidation, and extreme latencies—asserting correctness, not
machine-specific timing thresholds.

### Memory-management strategy

- Adjacency list (not dense matrices) for sparse cloud topologies
- No full-graph copy on the routing hot path
- Bounded route and source-tree LRUs
- Incremental `link_count` / topology version metadata
- Synthetic generators prefer sparse connected graphs

### Current Phase 3 limitations

- Caches are process-local (no shared/distributed cache)
- Source-tree memoization trades early-exit Dijkstra for multi-destination reuse
  when enabled
- Benchmarks measure Python-level time/memory, not kernel networking
- Still no live cloud APIs, multi-metric costs, or persistence layer

## How to Run Benchmarks

```bash
python -m benchmarks.benchmark_routes
```

## Current Limitations

- No live cloud provider APIs or telemetry
- Only latency is modeled (no bandwidth, loss, or congestion)
- Single-process in-memory topology
- Not a production control-plane or SDN controller

## Future Extensions

- Multi-failure scenarios and priority-aware failover policies
- Additional routing metrics (bandwidth, packet loss, congestion)
- Incremental / dynamic shortest-path algorithms
- CLI, web interface, or visualization layer
- Optional integration with cloud provider network telemetry
