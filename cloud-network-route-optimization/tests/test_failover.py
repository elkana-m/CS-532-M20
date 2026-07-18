"""Unit tests for link failure, failover routing, and latency updates."""

from __future__ import annotations

import unittest

from src.network_graph import CloudNetworkGraph
from src.route_optimizer import CloudRouteOptimizer
from src.sample_topology import build_sample_network


class TestFailover(unittest.TestCase):
    """Tests for failover behavior under link failure and latency change."""

    def test_link_failure_with_valid_alternate_route(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("S", "A", 1)
        graph.add_link("A", "T", 1)  # primary total 2
        graph.add_link("S", "B", 5)
        graph.add_link("B", "T", 5)  # alternate total 10
        optimizer = CloudRouteOptimizer(graph)

        primary = optimizer.shortest_path("S", "T")
        self.assertEqual(primary["total_latency"], 2)

        self.assertTrue(graph.remove_link("S", "A"))
        self.assertTrue(graph.is_reachable("S", "T"))

        alternate = optimizer.shortest_path("S", "T")
        self.assertTrue(alternate["reachable"])
        self.assertEqual(alternate["total_latency"], 10)
        self.assertEqual(alternate["path"], ["S", "B", "T"])

    def test_link_failure_with_no_remaining_route(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("S", "T", 3)
        optimizer = CloudRouteOptimizer(graph)

        self.assertTrue(graph.is_reachable("S", "T"))
        self.assertTrue(graph.remove_link("S", "T"))
        self.assertFalse(graph.is_reachable("S", "T"))

        cut = optimizer.shortest_path("S", "T")
        self.assertFalse(cut["reachable"])
        self.assertEqual(cut["path"], [])
        self.assertIsNone(cut["total_latency"])

    def test_route_recalculation_after_failure(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(graph)
        source, destination = "AWS US-East", "AWS US-West"

        initial = optimizer.shortest_path(source, destination)
        self.assertEqual(initial["total_latency"], 49)

        removed = graph.remove_link("Google Cloud Iowa", "Google Cloud Oregon")
        self.assertTrue(removed)
        self.assertTrue(graph.is_reachable(source, destination))

        failover = optimizer.shortest_path(source, destination)
        self.assertTrue(failover["reachable"])
        self.assertEqual(failover["total_latency"], 56)
        # Oregon link is down, so the Iowa <-> Oregon hop cannot appear
        path = failover["path"]
        iowa_oregon_adjacent = (
            "Google Cloud Iowa" in path
            and "Google Cloud Oregon" in path
            and abs(
                path.index("Google Cloud Iowa") - path.index("Google Cloud Oregon")
            )
            == 1
        )
        self.assertFalse(iowa_oregon_adjacent)

    def test_route_restoration(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(graph)
        source, destination = "AWS US-East", "AWS US-West"

        graph.remove_link("Google Cloud Iowa", "Google Cloud Oregon")
        failover = optimizer.shortest_path(source, destination)
        self.assertEqual(failover["total_latency"], 56)

        graph.add_link("Google Cloud Iowa", "Google Cloud Oregon", 18)
        restored = optimizer.shortest_path(source, destination)
        self.assertEqual(restored["total_latency"], 49)
        self.assertEqual(
            restored["path"],
            [
                "AWS US-East",
                "Azure East US",
                "Google Cloud Iowa",
                "Google Cloud Oregon",
                "AWS US-West",
            ],
        )

    def test_route_change_after_latency_update(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(graph)
        source, destination = "AWS US-East", "AWS US-West"

        before = optimizer.shortest_path(source, destination)
        self.assertEqual(before["total_latency"], 49)

        graph.add_link("Azure East US", "Azure West US", 15)
        after = optimizer.shortest_path(source, destination)
        self.assertTrue(after["reachable"])
        self.assertEqual(after["total_latency"], 41)
        self.assertEqual(
            after["path"],
            [
                "AWS US-East",
                "Azure East US",
                "Azure West US",
                "AWS US-West",
            ],
        )
        self.assertNotEqual(before["path"], after["path"])


if __name__ == "__main__":
    unittest.main()
