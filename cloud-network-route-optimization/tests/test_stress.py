"""Stress and scalability tests for Phase 3 cloud routing."""

from __future__ import annotations

import unittest

from src.network_graph import CloudNetworkGraph
from src.route_optimizer import CloudRouteOptimizer
from src.topology_generator import (
    generate_chain_network,
    generate_connected_sparse_network,
    generate_star_network,
    reproducible_endpoints,
)


class TestStress(unittest.TestCase):
    """Correctness under large and adversarial topologies (no timing asserts)."""

    def test_thousands_of_nodes_sparse(self) -> None:
        graph = generate_connected_sparse_network(node_count=2000, seed=1)
        source, destination = reproducible_endpoints(2000)
        optimizer = CloudRouteOptimizer(
            graph, cache_capacity=32, source_tree_capacity=0
        )
        result = optimizer.shortest_path(source, destination)
        self.assertTrue(result["reachable"])
        self.assertIsNotNone(result["total_latency"])
        self.assertGreaterEqual(result["total_latency"], 1)
        self.assertEqual(result["path"][0], source)
        self.assertEqual(result["path"][-1], destination)
        self.assertEqual(graph.datacenter_count(), 2000)

    def test_long_chain_topology(self) -> None:
        n = 1500
        graph = generate_chain_network(n, latency=2)
        source, destination = reproducible_endpoints(n)
        optimizer = CloudRouteOptimizer(
            graph, cache_capacity=8, source_tree_capacity=0
        )
        result = optimizer.shortest_path(source, destination)
        self.assertTrue(result["reachable"])
        self.assertEqual(result["total_latency"], 2 * (n - 1))
        self.assertEqual(len(result["path"]), n)

    def test_star_topology(self) -> None:
        graph = generate_star_network(leaf_count=500, latency=5)
        optimizer = CloudRouteOptimizer(
            graph, cache_capacity=8, source_tree_capacity=0
        )
        result = optimizer.shortest_path("Region-00001", "Region-00500")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["total_latency"], 10)
        self.assertEqual(
            result["path"],
            ["Region-00001", "Region-00000", "Region-00500"],
        )

    def test_disconnected_graph(self) -> None:
        graph = CloudNetworkGraph()
        for i in range(50):
            graph.add_datacenter(f"Isolated-{i}")
        optimizer = CloudRouteOptimizer(graph, cache_capacity=4)
        result = optimizer.shortest_path("Isolated-0", "Isolated-49")
        self.assertFalse(result["reachable"])
        self.assertEqual(result["path"], [])
        self.assertIsNone(result["total_latency"])
        self.assertFalse(graph.is_reachable("Isolated-0", "Isolated-49"))

    def test_multiple_equal_cost_routes(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("S", "A", 4)
        graph.add_link("A", "T", 6)
        graph.add_link("S", "B", 3)
        graph.add_link("B", "T", 7)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=4)
        result = optimizer.shortest_path("S", "T")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["total_latency"], 10)
        self.assertEqual(result["path"][0], "S")
        self.assertEqual(result["path"][-1], "T")

    def test_repeated_route_requests(self) -> None:
        graph = generate_connected_sparse_network(node_count=300, seed=3)
        source, destination = reproducible_endpoints(300)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=64)
        first = optimizer.shortest_path(source, destination)
        hits_before = optimizer.cache_info()["hits"]
        for _ in range(20):
            again = optimizer.shortest_path(source, destination)
            self.assertEqual(again, first)
        self.assertGreater(optimizer.cache_info()["hits"], hits_before)

    def test_rapid_link_removal_and_restoration(self) -> None:
        graph = generate_chain_network(40, latency=1)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=16)
        source, destination = reproducible_endpoints(40)
        baseline = optimizer.shortest_path(source, destination)
        self.assertEqual(baseline["total_latency"], 39)

        for _ in range(10):
            self.assertTrue(
                graph.remove_link("Region-00010", "Region-00011")
            )
            cut = optimizer.shortest_path(source, destination)
            self.assertFalse(cut["reachable"])
            graph.add_link("Region-00010", "Region-00011", 1)
            restored = optimizer.shortest_path(source, destination)
            self.assertEqual(restored["total_latency"], 39)

    def test_repeated_latency_changes(self) -> None:
        graph = generate_chain_network(20, latency=5)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=16)
        source, destination = reproducible_endpoints(20)
        for weight in (5, 7, 3, 9, 1):
            graph.add_link("Region-00000", "Region-00001", weight)
            result = optimizer.shortest_path(source, destination)
            expected = weight + 5 * 18
            self.assertEqual(result["total_latency"], expected)

    def test_cache_eviction_after_exceeding_capacity(self) -> None:
        graph = CloudNetworkGraph()
        hub = "Hub"
        graph.add_datacenter(hub)
        for i in range(10):
            graph.add_link(hub, f"Leaf-{i}", i + 1)
        optimizer = CloudRouteOptimizer(
            graph, cache_capacity=3, source_tree_capacity=0
        )
        for i in range(10):
            optimizer.shortest_path(hub, f"Leaf-{i}")
        info = optimizer.cache_info()
        self.assertEqual(info["current_size"], 3)
        self.assertLessEqual(info["current_size"], info["capacity"])

    def test_cache_invalidation_after_topology_mutation(self) -> None:
        graph = generate_connected_sparse_network(node_count=80, seed=9)
        source, destination = reproducible_endpoints(80)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=16)
        optimizer.shortest_path(source, destination)
        misses_before = optimizer.cache_info()["misses"]
        version_before = graph.topology_version

        peer, latency = next(graph.iter_neighbors(source))
        graph.add_link(source, peer, latency + 5)
        self.assertGreater(graph.topology_version, version_before)

        optimizer.shortest_path(source, destination)
        self.assertGreater(optimizer.cache_info()["misses"], misses_before)
        self.assertFalse(optimizer.last_run_metrics()["cache_hit"])

    def test_caching_disabled_capacity_zero(self) -> None:
        graph = generate_star_network(20)
        optimizer = CloudRouteOptimizer(
            graph, cache_capacity=0, source_tree_capacity=0
        )
        optimizer.shortest_path("Region-00000", "Region-00010")
        optimizer.shortest_path("Region-00000", "Region-00010")
        self.assertEqual(optimizer.cache_info()["hits"], 0)
        self.assertEqual(optimizer.cache_info()["current_size"], 0)

    def test_extremely_high_valid_latency(self) -> None:
        graph = CloudNetworkGraph()
        high = 10**9
        graph.add_link("A", "B", high)
        graph.add_link("B", "C", high)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=4)
        result = optimizer.shortest_path("A", "C")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["total_latency"], 2 * high)

    def test_many_isolated_datacenters(self) -> None:
        graph = CloudNetworkGraph()
        for i in range(1000):
            graph.add_datacenter(f"DC-{i}")
        self.assertEqual(graph.datacenter_count(), 1000)
        self.assertEqual(graph.link_count(), 0)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=8)
        result = optimizer.shortest_path("DC-0", "DC-999")
        self.assertFalse(result["reachable"])

    def test_opposite_ends_of_large_graph(self) -> None:
        n = 3000
        graph = generate_connected_sparse_network(
            node_count=n, extra_edges_per_node=1, seed=11
        )
        source, destination = reproducible_endpoints(n)
        optimizer = CloudRouteOptimizer(
            graph, cache_capacity=8, source_tree_capacity=0
        )
        result = optimizer.shortest_path(source, destination)
        self.assertTrue(graph.is_reachable(source, destination))
        self.assertTrue(result["reachable"])
        self.assertEqual(result["path"][0], source)
        self.assertEqual(result["path"][-1], destination)

    def test_topology_version_changes_only_when_graph_changes(self) -> None:
        graph = CloudNetworkGraph()
        v0 = graph.topology_version
        graph.add_datacenter("A")
        self.assertEqual(graph.topology_version, v0 + 1)
        v1 = graph.topology_version
        graph.add_datacenter("A")
        self.assertEqual(graph.topology_version, v1)
        graph.add_link("A", "B", 3)
        v2 = graph.topology_version
        self.assertGreater(v2, v1)
        graph.add_link("A", "B", 3)
        self.assertEqual(graph.topology_version, v2)
        self.assertFalse(graph.remove_link("A", "Z"))
        self.assertEqual(graph.topology_version, v2)
        self.assertTrue(graph.remove_link("A", "B"))
        self.assertGreater(graph.topology_version, v2)


if __name__ == "__main__":
    unittest.main()
