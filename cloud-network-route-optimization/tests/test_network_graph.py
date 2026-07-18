"""Unit tests for CloudNetworkGraph management and BFS reachability."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from src.network_graph import CloudNetworkGraph


class TestNetworkGraph(unittest.TestCase):
    """Tests for graph construction, mutation, lookup, and reachability."""

    def test_empty_network(self) -> None:
        empty = CloudNetworkGraph()
        self.assertEqual(empty.get_neighbors("AWS US-East"), {})
        self.assertFalse(empty.is_reachable("A", "B"))
        self.assertEqual(empty.adjacency, {})
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            empty.display_network()
        self.assertIn("empty network", buffer.getvalue())

    def test_adding_a_datacenter(self) -> None:
        graph = CloudNetworkGraph()
        message = graph.add_datacenter("AWS US-East")
        self.assertIn("added", message.lower())
        self.assertIn("AWS US-East", graph.adjacency)
        self.assertEqual(graph.get_neighbors("AWS US-East"), {})

    def test_adding_same_datacenter_twice(self) -> None:
        graph = CloudNetworkGraph()
        first = graph.add_datacenter("AWS US-East")
        second = graph.add_datacenter("AWS US-East")
        self.assertIn("added", first.lower())
        self.assertIn("already exists", second.lower())

    def test_adding_and_retrieving_a_link(self) -> None:
        graph = CloudNetworkGraph()
        message = graph.add_link("AWS US-East", "Azure East US", 12)
        self.assertIn("added", message.lower())
        self.assertEqual(
            graph.get_neighbors("AWS US-East"),
            {"Azure East US": 12},
        )
        self.assertEqual(
            graph.get_neighbors("Azure East US"),
            {"AWS US-East": 12},
        )

    def test_updating_link_latency(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("AWS US-East", "Azure East US", 12)
        message = graph.add_link("AWS US-East", "Azure East US", 8)
        self.assertIn("updated", message.lower())
        self.assertEqual(graph.get_neighbors("AWS US-East")["Azure East US"], 8)
        self.assertEqual(graph.get_neighbors("Azure East US")["AWS US-East"], 8)

    def test_negative_latency_rejection(self) -> None:
        graph = CloudNetworkGraph()
        with self.assertRaises(ValueError) as context:
            graph.add_link("A", "B", -5)
        message = str(context.exception).lower()
        self.assertTrue("non-negative" in message or "negative" in message)

    def test_self_link_rejection(self) -> None:
        graph = CloudNetworkGraph()
        with self.assertRaises(ValueError) as context:
            graph.add_link("A", "A", 10)
        self.assertIn("self", str(context.exception).lower())

    def test_removing_an_existing_link(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("AWS US-East", "Azure East US", 12)
        self.assertTrue(graph.remove_link("AWS US-East", "Azure East US"))
        self.assertEqual(graph.get_neighbors("AWS US-East"), {})
        self.assertEqual(graph.get_neighbors("Azure East US"), {})
        # Datacenters remain after link removal
        self.assertIn("AWS US-East", graph.adjacency)
        self.assertIn("Azure East US", graph.adjacency)

    def test_removing_a_missing_link(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_datacenter("A")
        graph.add_datacenter("B")
        self.assertFalse(graph.remove_link("A", "B"))

    def test_unknown_neighbor_lookup(self) -> None:
        graph = CloudNetworkGraph()
        self.assertEqual(graph.get_neighbors("Missing Datacenter"), {})

    def test_bfs_source_equals_destination(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_datacenter("A")
        self.assertTrue(graph.is_reachable("A", "A"))

    def test_bfs_disconnected_nodes(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_datacenter("A")
        graph.add_datacenter("B")
        self.assertFalse(graph.is_reachable("A", "B"))

    def test_adjacency_returns_safe_copy(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("A", "B", 5)
        snapshot = graph.adjacency
        snapshot["A"]["B"] = 99
        snapshot["C"] = {}
        self.assertEqual(graph.get_neighbors("A")["B"], 5)
        self.assertNotIn("C", graph.adjacency)


if __name__ == "__main__":
    unittest.main()
