"""
Reproducible synthetic cloud network topology generators.

PHASE 3 OPTIMIZATION:
Sparse connected graphs match adjacency-list storage and realistic cloud
backbone assumptions, enabling scalability benchmarks without dense O(V²)
memory blow-ups.
"""

from __future__ import annotations

import random
from typing import List, Tuple

from .network_graph import CloudNetworkGraph


def _region_name(index: int) -> str:
    """Format a unique synthetic datacenter name."""
    return f"Region-{index:05d}"


def generate_connected_sparse_network(
    node_count: int,
    extra_edges_per_node: int = 2,
    min_latency: int = 1,
    max_latency: int = 100,
    seed: int = 42,
) -> CloudNetworkGraph:
    """
    Generate a connected sparse undirected network.

    Builds a spanning chain first (guarantees connectivity), then adds random
    extra links while avoiding self-links and duplicates.

    Args:
        node_count: Number of datacenter nodes (must be >= 1).
        extra_edges_per_node: Approximate extra undirected edges per node.
        min_latency: Inclusive lower bound for random link latency (ms).
        max_latency: Inclusive upper bound for random link latency (ms).
        seed: RNG seed for reproducible topologies.

    Returns:
        A connected CloudNetworkGraph with synthetic Region-XXXXX names.

    Raises:
        ValueError: If arguments are invalid.
    """
    if node_count < 1:
        raise ValueError(f"node_count must be >= 1, got {node_count}")
    if extra_edges_per_node < 0:
        raise ValueError(
            f"extra_edges_per_node must be >= 0, got {extra_edges_per_node}"
        )
    if min_latency < 0 or max_latency < min_latency:
        raise ValueError(
            f"Invalid latency range: [{min_latency}, {max_latency}]"
        )

    rng = random.Random(seed)
    graph = CloudNetworkGraph()
    names: List[str] = [_region_name(i) for i in range(node_count)]

    for name in names:
        graph.add_datacenter(name)

    if node_count == 1:
        return graph

    # Spanning chain — guarantees the graph is connected
    for i in range(node_count - 1):
        latency = rng.randint(min_latency, max_latency)
        graph.add_link(names[i], names[i + 1], latency)

    # Extra random edges for a sparse but richer topology
    target_extra = extra_edges_per_node * node_count
    attempts = 0
    max_attempts = max(target_extra * 10, node_count * 10)
    added = 0
    while added < target_extra and attempts < max_attempts:
        attempts += 1
        a, b = rng.sample(range(node_count), 2)
        source, destination = names[a], names[b]
        if destination in graph.get_neighbors(source):
            continue
        latency = rng.randint(min_latency, max_latency)
        graph.add_link(source, destination, latency)
        added += 1

    return graph


def generate_chain_network(
    node_count: int,
    latency: int = 1,
) -> CloudNetworkGraph:
    """Generate a path graph Region-00000 — ... — Region-(n-1)."""
    if node_count < 1:
        raise ValueError(f"node_count must be >= 1, got {node_count}")
    if latency < 0:
        raise ValueError(f"latency must be non-negative, got {latency}")

    graph = CloudNetworkGraph()
    names = [_region_name(i) for i in range(node_count)]
    for name in names:
        graph.add_datacenter(name)
    for i in range(node_count - 1):
        graph.add_link(names[i], names[i + 1], latency)
    return graph


def generate_star_network(
    leaf_count: int,
    latency: int = 1,
) -> CloudNetworkGraph:
    """
    Generate a star: Region-00000 is the hub; remaining nodes are leaves.

    Total nodes = leaf_count + 1.
    """
    if leaf_count < 0:
        raise ValueError(f"leaf_count must be >= 0, got {leaf_count}")
    if latency < 0:
        raise ValueError(f"latency must be non-negative, got {latency}")

    graph = CloudNetworkGraph()
    hub = _region_name(0)
    graph.add_datacenter(hub)
    for i in range(1, leaf_count + 1):
        leaf = _region_name(i)
        graph.add_link(hub, leaf, latency)
    return graph


def generate_dense_network(
    node_count: int,
    min_latency: int = 1,
    max_latency: int = 50,
    seed: int = 7,
) -> CloudNetworkGraph:
    """
    Generate a small near-complete graph for sparse-vs-dense comparisons.

    Intended only for modest node_count values (e.g. <= 200).
    """
    if node_count < 1:
        raise ValueError(f"node_count must be >= 1, got {node_count}")
    if node_count > 200:
        raise ValueError(
            "generate_dense_network refuses node_count > 200 to avoid "
            "excessive memory use"
        )
    if min_latency < 0 or max_latency < min_latency:
        raise ValueError(
            f"Invalid latency range: [{min_latency}, {max_latency}]"
        )

    rng = random.Random(seed)
    graph = CloudNetworkGraph()
    names = [_region_name(i) for i in range(node_count)]
    for name in names:
        graph.add_datacenter(name)
    for i in range(node_count):
        for j in range(i + 1, node_count):
            latency = rng.randint(min_latency, max_latency)
            graph.add_link(names[i], names[j], latency)
    return graph


def reproducible_endpoints(
    node_count: int,
) -> Tuple[str, str]:
    """Return first and last synthetic region names for stable benchmarks."""
    if node_count < 1:
        raise ValueError(f"node_count must be >= 1, got {node_count}")
    return _region_name(0), _region_name(node_count - 1)
