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
    print()


if __name__ == "__main__":
    run_demonstration()
