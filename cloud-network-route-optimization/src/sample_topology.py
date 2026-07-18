"""Sample multi-cloud datacenter topology for the proof-of-concept demonstration."""

from __future__ import annotations

from typing import List, Tuple

from .network_graph import CloudNetworkGraph

DATACENTERS: List[str] = [
    "AWS US-East",
    "AWS US-West",
    "Azure East US",
    "Azure West US",
    "Google Cloud Iowa",
    "Google Cloud Oregon",
]

SAMPLE_LINKS: List[Tuple[str, str, int]] = [
    ("AWS US-East", "Azure East US", 12),
    ("AWS US-East", "Google Cloud Iowa", 25),
    ("Azure East US", "Google Cloud Iowa", 10),
    ("Azure East US", "Azure West US", 30),
    ("Google Cloud Iowa", "Google Cloud Oregon", 18),
    ("Google Cloud Oregon", "AWS US-West", 9),
    ("Azure West US", "AWS US-West", 14),
    ("Google Cloud Iowa", "Azure West US", 20),
]


def build_sample_network(*, verbose: bool = True) -> CloudNetworkGraph:
    """
    Construct the sample multi-cloud topology used in the demonstration.

    Args:
        verbose: When True, print status messages while adding nodes and links.

    Returns:
        A fully constructed CloudNetworkGraph with all sample datacenters
        and bidirectional links.
    """
    graph = CloudNetworkGraph()
    for name in DATACENTERS:
        message = graph.add_datacenter(name)
        if verbose:
            print(f"  {message}")
    if verbose:
        print()
    for source, destination, latency in SAMPLE_LINKS:
        message = graph.add_link(source, destination, latency)
        if verbose:
            print(f"  {message}")
    return graph
