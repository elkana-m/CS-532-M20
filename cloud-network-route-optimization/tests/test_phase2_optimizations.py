"""Phase 3 optimization unit tests: caching, versioning, and no adjacency copy."""

from __future__ import annotations

import unittest
from unittest.mock import PropertyMock, patch

from src.network_graph import CloudNetworkGraph
from src.route_optimizer import CloudRouteOptimizer
from src.sample_topology import build_sample_network


class TestPhase2Optimizations(unittest.TestCase):
    """Verify Phase 3 performance optimizations preserve correctness."""

    def test_shortest_path_does_not_copy_adjacency(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=0)

        with patch.object(
            CloudNetworkGraph,
            "adjacency",
            new_callable=PropertyMock,
        ) as mocked_adjacency:
            mocked_adjacency.side_effect = AssertionError(
                "shortest_path must not use adjacency property copies"
            )
            result = optimizer.shortest_path("AWS US-East", "AWS US-West")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["total_latency"], 49)

    def test_repeated_route_queries_produce_cache_hit(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=32)
        optimizer.shortest_path("AWS US-East", "AWS US-West")
        info_after_miss = optimizer.cache_info()
        self.assertEqual(info_after_miss["misses"], 1)
        self.assertEqual(info_after_miss["hits"], 0)

        optimizer.shortest_path("AWS US-East", "AWS US-West")
        info_after_hit = optimizer.cache_info()
        self.assertEqual(info_after_hit["hits"], 1)
        self.assertTrue(optimizer.last_run_metrics()["cache_hit"])

    def test_link_update_invalidates_cached_result(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=32)
        before = optimizer.shortest_path("AWS US-East", "AWS US-West")
        self.assertEqual(before["total_latency"], 49)

        graph.add_link("Azure East US", "Azure West US", 15)
        after = optimizer.shortest_path("AWS US-East", "AWS US-West")
        self.assertEqual(after["total_latency"], 41)
        self.assertFalse(optimizer.last_run_metrics()["cache_hit"])
        self.assertNotEqual(before["path"], after["path"])

    def test_link_removal_invalidates_cached_result(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=32)
        before = optimizer.shortest_path("AWS US-East", "AWS US-West")
        self.assertEqual(before["total_latency"], 49)

        graph.remove_link("Google Cloud Iowa", "Google Cloud Oregon")
        after = optimizer.shortest_path("AWS US-East", "AWS US-West")
        self.assertEqual(after["total_latency"], 56)
        self.assertFalse(optimizer.last_run_metrics()["cache_hit"])

    def test_new_datacenter_increments_topology_version(self) -> None:
        graph = CloudNetworkGraph()
        version = graph.topology_version
        graph.add_datacenter("AWS US-East")
        self.assertEqual(graph.topology_version, version + 1)

    def test_duplicate_datacenter_does_not_increment_topology_version(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_datacenter("AWS US-East")
        version = graph.topology_version
        graph.add_datacenter("AWS US-East")
        self.assertEqual(graph.topology_version, version)

    def test_same_latency_update_does_not_increment_topology_version(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("A", "B", 10)
        version = graph.topology_version
        graph.add_link("A", "B", 10)
        self.assertEqual(graph.topology_version, version)

    def test_cache_capacity_is_enforced(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("S", "A", 1)
        graph.add_link("S", "B", 1)
        graph.add_link("S", "C", 1)
        optimizer = CloudRouteOptimizer(
            graph, cache_capacity=2, source_tree_capacity=0
        )
        optimizer.shortest_path("S", "A")
        optimizer.shortest_path("S", "B")
        optimizer.shortest_path("S", "C")
        info = optimizer.cache_info()
        self.assertEqual(info["capacity"], 2)
        self.assertLessEqual(info["current_size"], 2)
        self.assertEqual(info["current_size"], 2)

    def test_lru_entries_evicted_first(self) -> None:
        graph = CloudNetworkGraph()
        graph.add_link("S", "A", 1)
        graph.add_link("S", "B", 1)
        graph.add_link("S", "C", 1)
        optimizer = CloudRouteOptimizer(
            graph, cache_capacity=2, source_tree_capacity=0
        )
        optimizer.shortest_path("S", "A")
        optimizer.shortest_path("S", "B")
        # Re-access A so B becomes the least recently used entry
        optimizer.shortest_path("S", "A")
        optimizer.shortest_path("S", "C")  # evicts B; cache holds A and C

        optimizer.shortest_path("S", "A")
        self.assertTrue(optimizer.last_run_metrics()["cache_hit"])
        optimizer.shortest_path("S", "C")
        self.assertTrue(optimizer.last_run_metrics()["cache_hit"])

        hits_before = optimizer.cache_info()["hits"]
        optimizer.shortest_path("S", "B")  # B was LRU-evicted
        self.assertEqual(optimizer.cache_info()["hits"], hits_before)
        self.assertFalse(optimizer.last_run_metrics()["cache_hit"])

    def test_returned_cached_paths_cannot_mutate_store(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=8)
        first = optimizer.shortest_path("AWS US-East", "AWS US-West")
        first["path"].append("MUTATED")
        second = optimizer.shortest_path("AWS US-East", "AWS US-West")
        self.assertTrue(optimizer.last_run_metrics()["cache_hit"])
        self.assertNotIn("MUTATED", second["path"])
        self.assertEqual(second["total_latency"], 49)

    def test_cached_and_uncached_results_identical(self) -> None:
        graph = build_sample_network(verbose=False)
        cached = CloudRouteOptimizer(graph, cache_capacity=16)
        uncached = CloudRouteOptimizer(
            graph, cache_capacity=0, source_tree_capacity=0
        )
        a = cached.shortest_path("AWS US-East", "AWS US-West")
        b = uncached.shortest_path("AWS US-East", "AWS US-West")
        self.assertEqual(a, b)
        a2 = cached.shortest_path("AWS US-East", "AWS US-West")
        self.assertEqual(a2, b)

    def test_failover_remains_correct_with_caching(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(graph, cache_capacity=32)
        initial = optimizer.shortest_path("AWS US-East", "AWS US-West")
        self.assertEqual(initial["total_latency"], 49)

        graph.remove_link("Google Cloud Iowa", "Google Cloud Oregon")
        self.assertTrue(graph.is_reachable("AWS US-East", "AWS US-West"))
        failover = optimizer.shortest_path("AWS US-East", "AWS US-West")
        self.assertTrue(failover["reachable"])
        self.assertEqual(failover["total_latency"], 56)

    def test_source_tree_reuses_one_dijkstra_for_many_destinations(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(
            graph, cache_capacity=0, source_tree_capacity=8
        )
        source = "AWS US-East"
        destinations = [
            "Azure East US",
            "Google Cloud Iowa",
            "Google Cloud Oregon",
            "AWS US-West",
        ]
        for dest in destinations:
            result = optimizer.shortest_path(source, dest)
            self.assertTrue(result["reachable"])
        # One Dijkstra builds the tree; later destinations reuse it
        self.assertEqual(optimizer.dijkstra_execution_count(), 1)
        self.assertTrue(optimizer.last_run_metrics()["source_tree_hit"])

    def test_negative_cache_capacity_rejected(self) -> None:
        graph = CloudNetworkGraph()
        with self.assertRaises(ValueError):
            CloudRouteOptimizer(graph, cache_capacity=-1)

    def test_caching_disabled_with_capacity_zero(self) -> None:
        graph = build_sample_network(verbose=False)
        optimizer = CloudRouteOptimizer(
            graph, cache_capacity=0, source_tree_capacity=0
        )
        optimizer.shortest_path("AWS US-East", "AWS US-West")
        optimizer.shortest_path("AWS US-East", "AWS US-West")
        info = optimizer.cache_info()
        self.assertEqual(info["capacity"], 0)
        self.assertEqual(info["current_size"], 0)
        self.assertEqual(info["hits"], 0)


if __name__ == "__main__":
    unittest.main()
