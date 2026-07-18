#!/usr/bin/env python3
"""
Cloud Network Route Optimization and Failover Management — Proof of Concept

Demonstrates core data structures and routing behavior for selecting
lowest-latency paths between cloud datacenters and recovering from link failures.

Run from the project root:

    python -m src.main
"""

from __future__ import annotations

from .models import RouteResult
from .route_optimizer import CloudRouteOptimizer
from .sample_topology import build_sample_network


def _print_section(title: str) -> None:
    """Print a clearly labeled section header for academic report screenshots."""
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def _print_route(label: str, result: RouteResult) -> None:
    """Print a structured route result."""
    print(f"  {label}")
    if result["reachable"]:
        print(f"    Path:           {' -> '.join(result['path'])}")
        print(f"    Total latency:  {result['total_latency']} ms")
        print(f"    Reachable:      {result['reachable']}")
    else:
        print("    Path:           (none)")
        print("    Total latency:  None")
        print(f"    Reachable:      {result['reachable']}")


def run_demonstration() -> None:
    """
    End-to-end proof-of-concept: topology build, route selection,
    link failure / failover, and latency update.
    """
    _print_section("CLOUD NETWORK TOPOLOGY")
    print("Adding datacenters and links...\n")
    graph = build_sample_network()
    print("\nCurrent network:")
    graph.display_network()

    optimizer = CloudRouteOptimizer(graph)
    source = "AWS US-East"
    destination = "AWS US-West"

    _print_section("INITIAL ROUTE SELECTION")
    initial = optimizer.shortest_path(source, destination)
    _print_route(f"Lowest-latency route: {source} -> {destination}", initial)
    print(f"  BFS reachability check: {graph.is_reachable(source, destination)}")

    assert initial["reachable"] is True
    assert initial["total_latency"] == 49
    assert initial["path"] == [
        "AWS US-East",
        "Azure East US",
        "Google Cloud Iowa",
        "Google Cloud Oregon",
        "AWS US-West",
    ]
    assert graph.is_reachable(source, destination) is True

    # Fail one hop on the selected route: Google Cloud Iowa <-> Google Cloud Oregon
    failed_a, failed_b = "Google Cloud Iowa", "Google Cloud Oregon"

    _print_section("LINK FAILURE SIMULATION")
    removed = graph.remove_link(failed_a, failed_b)
    print(f"  Removed link: {failed_a} <-> {failed_b}")
    print(f"  Removal succeeded: {removed}")
    still_reachable = graph.is_reachable(source, destination)
    print(f"  Destination still reachable (BFS): {still_reachable}")
    assert removed is True
    assert still_reachable is True

    _print_section("FAILOVER ROUTE")
    failover = optimizer.shortest_path(source, destination)
    _print_route("Recalculated route after failure", failover)
    assert failover["reachable"] is True
    assert failover["total_latency"] == 56

    _print_section("LATENCY UPDATE")
    # Restore the failed link, then make the Azure East -> Azure West hop cheaper
    print(f"  {graph.add_link(failed_a, failed_b, 18)}")
    restored = optimizer.shortest_path(source, destination)
    _print_route("Route after restoring failed link", restored)
    assert restored["total_latency"] == 49

    print(f"  {graph.add_link('Azure East US', 'Azure West US', 15)}")
    updated = optimizer.shortest_path(source, destination)
    _print_route(
        "Route after lowering Azure East US <-> Azure West US to 15 ms",
        updated,
    )
    # New path: East -> Azure East (12) -> Azure West (15) -> West (14) = 41
    assert updated["reachable"] is True
    assert updated["total_latency"] == 41
    assert updated["path"] == [
        "AWS US-East",
        "Azure East US",
        "Azure West US",
        "AWS US-West",
    ]
    print(
        "  Route changed after latency update: "
        f"{restored['total_latency']} ms -> {updated['total_latency']} ms"
    )

    _print_section("PHASE 3 OPTIMIZATION DEMONSTRATION")
    # Fresh optimizer so cache stats reflect only this section
    phase2 = CloudRouteOptimizer(graph, cache_capacity=128)
    version_before = graph.topology_version

    first = phase2.shortest_path(source, destination)
    metrics_first = phase2.last_run_metrics()
    info_first = phase2.cache_info()
    print("  1) First route request (cache miss — Dijkstra runs)")
    _print_route("    Result", first)
    print(f"    Cache hit:          {metrics_first['cache_hit']}")
    print(f"    Dijkstra executed:  {metrics_first['dijkstra_executed']}")
    print(f"    Nodes settled:      {metrics_first['nodes_settled']}")
    print(f"    Edges examined:     {metrics_first['edges_examined']}")
    print(
        f"    Cache stats:        hits={info_first['hits']} "
        f"misses={info_first['misses']} size={info_first['current_size']}"
    )

    second = phase2.shortest_path(source, destination)
    metrics_second = phase2.last_run_metrics()
    info_second = phase2.cache_info()
    print("  2) Repeated route request (cache hit)")
    _print_route("    Result", second)
    print(f"    Cache hit:          {metrics_second['cache_hit']}")
    print(f"    Same path/latency:  {second == first}")
    print(
        f"    Cache stats:        hits={info_second['hits']} "
        f"misses={info_second['misses']} size={info_second['current_size']}"
    )
    assert second == first
    assert metrics_second["cache_hit"] is True

    print("  3) Link latency update (topology version changes)")
    print(f"    Topology version before: {version_before}")
    print(f"  {graph.add_link('AWS US-East', 'Google Cloud Iowa', 40)}")
    print(f"    Topology version after:  {graph.topology_version}")
    assert graph.topology_version > version_before

    third = phase2.shortest_path(source, destination)
    metrics_third = phase2.last_run_metrics()
    info_third = phase2.cache_info()
    print("  4) New optimized route after invalidation")
    _print_route("    Result", third)
    print(f"    Cache hit:          {metrics_third['cache_hit']}")
    print(f"    Dijkstra executed:  {metrics_third['dijkstra_executed']}")
    print(f"    Previous cache unused: {metrics_third['cache_hit'] is False}")
    print(
        f"  5) Cache stats: hits={info_third['hits']} "
        f"misses={info_third['misses']} size={info_third['current_size']}"
        f"/{info_third['capacity']}"
    )
    print(
        f"     Route metrics: settled={metrics_third['nodes_settled']} "
        f"edges={metrics_third['edges_examined']} "
        f"heap_push={metrics_third['heap_pushes']} "
        f"heap_pop={metrics_third['heap_pops']}"
    )
    assert metrics_third["cache_hit"] is False
    print()


if __name__ == "__main__":
    run_demonstration()
