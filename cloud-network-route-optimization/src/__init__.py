"""
Cloud Network Route Optimization and Failover Management System.

Core package for modeling cloud datacenter topologies, selecting
lowest-latency routes, and managing link failover.
"""

from .models import RouteResult
from .network_graph import CloudNetworkGraph
from .route_optimizer import CloudRouteOptimizer

__all__ = [
    "RouteResult",
    "CloudNetworkGraph",
    "CloudRouteOptimizer",
]
