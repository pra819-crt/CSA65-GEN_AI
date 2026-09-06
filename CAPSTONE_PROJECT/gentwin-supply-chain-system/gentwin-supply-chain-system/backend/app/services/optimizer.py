"""
Resilience Optimization Engine.

Computes baseline, disrupted, and AI-optimized alternative routes through
the Digital Twin using a weighted Dijkstra's algorithm:

    weight = (transit_days * delay_mult) + alpha * (unit_cost * cost_mult * risk_factor)

The "optimized" pass excludes edges/nodes currently marked as disrupted,
forcing the algorithm to find a genuinely alternate path when one exists.
The "baseline" pass always uses risk_factor=1.0 (pristine conditions),
ignoring any live risk_factor mutations left over from a prior disruption,
so it represents a true pre-disruption reference point.
"""

from __future__ import annotations

from typing import Tuple

import networkx as nx

from app.core.config import get_settings
from app.models.schemas import Edge, RouteResult
from app.services.twin_engine import SupplyChainTwin


class RouteNotFoundError(Exception):
    """Raised when no path exists between source and target under given constraints."""


def _edge_weight(
    edge: Edge, delay_mult: float, cost_mult: float, alpha: float, use_live_risk: bool
) -> float:
    risk = edge.risk_factor if use_live_risk else 1.0
    return (edge.transit_days * delay_mult) + alpha * (
        edge.unit_cost * cost_mult * risk
    )


def _build_weighted_view(
    twin: SupplyChainTwin,
    delay_mult: float,
    cost_mult: float,
    alpha: float,
    exclude_disrupted: bool = False,
    use_live_risk: bool = True,
) -> nx.DiGraph:
    """Build a lightweight weighted view of the graph for a single Dijkstra pass."""
    graph = twin.get_graph()
    view = nx.DiGraph()

    for node_id, ndata in graph.nodes(data=True):
        node = ndata["data"]
        if exclude_disrupted and node.current_status.value == "Disrupted":
            continue
        view.add_node(node_id)

    for u, v, edata in graph.edges(data=True):
        edge: Edge = edata["data"]
        if exclude_disrupted and edge.is_disrupted:
            continue
        if u not in view.nodes or v not in view.nodes:
            continue
        w = _edge_weight(edge, delay_mult, cost_mult, alpha, use_live_risk)
        view.add_edge(u, v, weight=w, edge_ref=edge)

    return view


def _path_to_result(view: nx.DiGraph, path: list) -> RouteResult:
    edge_ids = []
    total_cost = 0.0
    total_days = 0.0
    total_weight = 0.0

    for u, v in zip(path[:-1], path[1:]):
        edge: Edge = view.edges[u, v]["edge_ref"]
        edge_ids.append(edge.id)
        total_cost += edge.unit_cost
        total_days += edge.transit_days
        total_weight += view.edges[u, v]["weight"]

    return RouteResult(
        path=path,
        edge_ids=edge_ids,
        total_cost=round(total_cost, 2),
        total_transit_days=round(total_days, 2),
        total_weight=round(total_weight, 4),
        feasible=True,
    )


def _infeasible_result() -> RouteResult:
    return RouteResult(
        path=[], edge_ids=[], total_cost=0.0, total_transit_days=0.0,
        total_weight=float("inf"), feasible=False,
    )


def _shortest_path(
    twin: SupplyChainTwin,
    source: str,
    target: str,
    delay_mult: float,
    cost_mult: float,
    alpha: float,
    exclude_disrupted: bool = False,
    use_live_risk: bool = True,
) -> RouteResult:
    view = _build_weighted_view(
        twin, delay_mult, cost_mult, alpha, exclude_disrupted, use_live_risk
    )
    if source not in view.nodes or target not in view.nodes:
        return _infeasible_result()
    try:
        path = nx.dijkstra_path(view, source, target, weight="weight")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return _infeasible_result()
    return _path_to_result(view, path)


def compute_route_comparison(
    twin: SupplyChainTwin,
    source: str,
    target: str,
    delay_multiplier: float,
    cost_multiplier: float,
) -> Tuple[RouteResult, RouteResult, RouteResult, float, float, float]:
    """
    Compute baseline / disrupted / optimized routes and derived KPIs.

    Returns:
        (baseline, disrupted, optimized, time_to_recovery_days,
         cost_overhead_pct, time_saved_days)
    """
    settings = get_settings()
    alpha = settings.ALPHA_COST_WEIGHT

    baseline = _shortest_path(
        twin, source, target, 1.0, 1.0, alpha, exclude_disrupted=False, use_live_risk=False
    )
    disrupted = _shortest_path(
        twin, source, target, delay_multiplier, cost_multiplier, alpha,
        exclude_disrupted=False, use_live_risk=True,
    )
    optimized = _shortest_path(
        twin, source, target, delay_multiplier, cost_multiplier, alpha,
        exclude_disrupted=True, use_live_risk=True,
    )
    if not optimized.feasible:
        optimized = disrupted

    disrupted_edges = [e for e in twin.get_all_edges() if e.is_disrupted]
    ttr_days = settings.DEFAULT_TTR_BASE_DAYS * max(1, len(disrupted_edges)) * delay_multiplier

    if baseline.feasible and baseline.total_cost > 0:
        cost_overhead_pct = round(
            ((optimized.total_cost - baseline.total_cost) / baseline.total_cost) * 100, 2
        )
    else:
        cost_overhead_pct = 0.0

    if disrupted.feasible and optimized.feasible:
        time_saved_days = round(disrupted.total_transit_days - optimized.total_transit_days, 2)
    else:
        time_saved_days = 0.0

    return baseline, disrupted, optimized, round(ttr_days, 2), cost_overhead_pct, time_saved_days
