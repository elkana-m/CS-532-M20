"""Shared data models for cloud network route results."""

from __future__ import annotations

from typing import List, Optional, TypedDict


class RouteResult(TypedDict):
    """Structured result returned by shortest_path."""

    path: List[str]
    total_latency: Optional[int]
    reachable: bool
