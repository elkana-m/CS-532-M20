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
│   ├── models.py              # RouteResult TypedDict
│   ├── network_graph.py       # Topology + BFS reachability
│   ├── route_optimizer.py     # Dijkstra shortest-path
│   ├── sample_topology.py     # Example datacenters and links
│   └── main.py                # Proof-of-concept demonstration
├── tests/
│   ├── __init__.py
│   ├── test_network_graph.py
│   ├── test_route_optimizer.py
│   └── test_failover.py
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

## How to Run Tests

From the project root:

```bash
python -m unittest discover -s tests
```

Tests use Python’s built-in `unittest` module; no third-party test runner is
required.

## Current Limitations

- Topology is static and hand-built (no live cloud APIs)
- Only latency is modeled (no bandwidth, loss, or congestion)
- Single-link failure scenarios are demonstrated; multi-failure sets are not
- No route caching, persistence, CLI flags, or visualization layer
- Not a production control-plane or SDN controller

## Future Extensions

- Larger generated network topologies and performance benchmarking
- Route caching and incremental recomputation
- Multiple simultaneous link failures
- Additional routing metrics (bandwidth, packet loss, congestion)
- CLI, web interface, or visualization layer
- Optional integration with cloud provider network telemetry
