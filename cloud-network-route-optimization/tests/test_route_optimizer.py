"""Unit tests for CloudRouteOptimizer Dijkstra shortest-path behavior."""

from __future__ import annotations

import unittest

from src.network_graph import CloudNetworkGraph
from src.route_optimizer import CloudRouteOptimizer
from src.sample_topology import build_sample_network


class TestRouteOptimizer(unittest.TestCase):
    """Tests for lowest-latency route selection and edge cases."""

    def test_lowest_latency_route_selection(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(graph)
        result = optimizer.shortest_path("AWS US-East", "AWS US-West")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["total_latency"], 49)
        self.assertEqual(
            result["path"],
            [
                "AWS US-East",
                "Azure East US",
                "Google Cloud Iowa",
                "Google Cloud Oregon",
                "AWS US-West",
            ],
        )

    def test_multiple_routes_different_costs(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("S", "MidFast", 5)
        graph.add_link("MidFast", "T", 5)  # total 10
        graph.add_link("S", "MidSlow", 8)
        graph.add_link("MidSlow", "T", 8)  # total 16
        optimizer = CloudRouteOptimizer(graph)
        result = optimizer.shortest_path("S", "T")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["total_latency"], 10)
        self.assertEqual(result["path"], ["S", "MidFast", "T"])

    def test_equal_cost_alternative_routes(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("S", "A", 4)
        graph.add_link("A", "T", 6)  # total 10
        graph.add_link("S", "B", 3)
        graph.add_link("B", "T", 7)  # total 10
        optimizer = CloudRouteOptimizer(graph)
        result = optimizer.shortest_path("S", "T")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["total_latency"], 10)
        self.assertEqual(result["path"][0], "S")
        self.assertEqual(result["path"][-1], "T")

    def test_unknown_source(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_datacenter("A")
        optimizer = CloudRouteOptimizer(graph)
        with self.assertRaises(KeyError):
            optimizer.shortest_path("Missing", "A")

    def test_unknown_destination(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_datacenter("A")
        optimizer = CloudRouteOptimizer(graph)
        with self.assertRaises(KeyError):
            optimizer.shortest_path("A", "Missing")

    def test_source_equals_destination(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_datacenter("A")
        optimizer = CloudRouteOptimizer(graph)
        result = optimizer.shortest_path("A", "A")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["total_latency"], 0)
        self.assertEqual(result["path"], ["A"])

    def test_unreachable_destination(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_datacenter("A")
        graph.add_datacenter("B")
        optimizer = CloudRouteOptimizer(graph)
        result = optimizer.shortest_path("A", "B")
        self.assertFalse(result["reachable"])
        self.assertEqual(result["path"], [])
        self.assertIsNone(result["total_latency"])

    def test_correct_path_reconstruction(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("S", "A", 2)
        graph.add_link("A", "B", 3)
        graph.add_link("B", "T", 4)
        optimizer = CloudRouteOptimizer(graph)
        result = optimizer.shortest_path("S", "T")
        self.assertEqual(result["path"], ["S", "A", "B", "T"])

    def test_correct_total_latency(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("S", "A", 2)
        graph.add_link("A", "B", 3)
        graph.add_link("B", "T", 4)
        optimizer = CloudRouteOptimizer(graph)
        result = optimizer.shortest_path("S", "T")
        self.assertEqual(result["total_latency"], 9)
        self.assertTrue(result["reachable"])


if __name__ == "__main__":
    unittest.main()
