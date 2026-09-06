"""
Digital Twin Graph Engine.

Wraps a NetworkX DiGraph representing the global supply chain network,
exposed as a thread-safe singleton (`get_twin()`), so every request
handler in the API layer operates on the same live network state.
"""

from __future__ import annotations

import threading
from copy import deepcopy
from typing import Dict, List, Optional

import networkx as nx

from app.models.schemas import (
    Edge,
    Node,
    NetworkResponse,
    NodeCategory,
    NodeStatus,
    TransportMode,
)


def _seed_nodes() -> List[Node]:
    """Static seed data for the 10 global logistics nodes."""
    return [
        Node(id="port_shanghai", name="Port of Shanghai", category=NodeCategory.PORT,
             lat=31.2304, lng=121.4737, base_capacity=50000),
        Node(id="port_rotterdam", name="Port of Rotterdam", category=NodeCategory.PORT,
             lat=51.9244, lng=4.4777, base_capacity=42000),
        Node(id="port_la", name="Port of Los Angeles", category=NodeCategory.PORT,
             lat=33.7292, lng=-118.2620, base_capacity=38000),
        Node(id="port_dubai", name="Port of Dubai (Jebel Ali)", category=NodeCategory.PORT,
             lat=25.0118, lng=55.0617, base_capacity=30000),
        Node(id="factory_shenzhen", name="Shenzhen Factory Cluster", category=NodeCategory.FACTORY,
             lat=22.5431, lng=114.0579, base_capacity=25000),
        Node(id="factory_frankfurt", name="Frankfurt Manufacturing Hub", category=NodeCategory.FACTORY,
             lat=50.1109, lng=8.6821, base_capacity=18000),
        Node(id="hub_chicago", name="Chicago Distribution Hub", category=NodeCategory.HUB,
             lat=41.8781, lng=-87.6298, base_capacity=22000),
        Node(id="hub_singapore", name="Singapore Transshipment Hub", category=NodeCategory.HUB,
             lat=1.3521, lng=103.8198, base_capacity=28000),
        Node(id="hub_memphis", name="Memphis Air Cargo Hub", category=NodeCategory.HUB,
             lat=35.1495, lng=-90.0490, base_capacity=15000),
        Node(id="hub_leipzig", name="Leipzig Air/Rail Hub", category=NodeCategory.HUB,
             lat=51.3397, lng=12.3731, base_capacity=12000),
    ]


def _seed_edges() -> List[Edge]:
    """Static seed data connecting the 10 nodes into a realistic network."""
    raw = [
        ("e1", "factory_shenzhen", "port_shanghai", TransportMode.ROAD, 1.0, 800.0, 1.0),
        ("e2", "port_shanghai", "hub_singapore", TransportMode.SEA, 4.0, 1200.0, 1.0),
        ("e3", "port_shanghai", "port_la", TransportMode.SEA, 14.0, 2500.0, 1.0),
        ("e4", "hub_singapore", "port_dubai", TransportMode.SEA, 6.0, 1600.0, 1.0),
        ("e5", "port_dubai", "port_rotterdam", TransportMode.SEA, 9.0, 2100.0, 1.0),
        ("e6", "port_rotterdam", "factory_frankfurt", TransportMode.RAIL, 1.0, 400.0, 1.0),
        ("e7", "factory_frankfurt", "hub_leipzig", TransportMode.ROAD, 0.5, 250.0, 1.0),
        ("e8", "port_la", "hub_chicago", TransportMode.RAIL, 2.5, 900.0, 1.0),
        ("e9", "hub_chicago", "hub_memphis", TransportMode.ROAD, 1.0, 350.0, 1.0),
        ("e10", "hub_memphis", "hub_leipzig", TransportMode.AIR, 1.5, 3200.0, 1.0),
        ("e11", "port_shanghai", "port_dubai", TransportMode.SEA, 10.0, 2000.0, 1.0),
        ("e12", "hub_singapore", "port_la", TransportMode.SEA, 16.0, 2800.0, 1.0),
        ("e13", "port_dubai", "hub_leipzig", TransportMode.AIR, 2.0, 4200.0, 1.0),
        ("e14", "factory_shenzhen", "hub_singapore", TransportMode.SEA, 5.0, 1100.0, 1.0),
        ("e15", "port_rotterdam", "hub_chicago", TransportMode.SEA, 11.0, 2300.0, 1.0),
    ]
    return [
        Edge(id=eid, source=src, target=tgt, mode=mode,
             transit_days=days, unit_cost=cost, risk_factor=risk)
        for (eid, src, tgt, mode, days, cost, risk) in raw
    ]


class SupplyChainTwin:
    """
    Thread-safe singleton managing the live Digital Twin graph.

    All mutating operations (apply_disruption, reset_network) acquire
    an internal RLock so concurrent API / WebSocket requests cannot
    corrupt graph state.
    """

    _instance: Optional["SupplyChainTwin"] = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "SupplyChainTwin":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        self._lock = threading.RLock()
        self._graph: nx.DiGraph = nx.DiGraph()
        self._baseline_nodes: List[Node] = _seed_nodes()
        self._baseline_edges: List[Edge] = _seed_edges()
        self._build_baseline()

    def _build_baseline(self) -> None:
        with self._lock:
            self._graph.clear()
            for node in self._baseline_nodes:
                self._graph.add_node(node.id, data=node.model_copy(deep=True))
            for edge in self._baseline_edges:
                self._graph.add_edge(
                    edge.source, edge.target, key=edge.id, data=edge.model_copy(deep=True)
                )

    # ------------------------------------------------------------------
    # Read accessors
    # ------------------------------------------------------------------

    def get_graph(self) -> nx.DiGraph:
        """Return the live graph object (callers should not mutate directly)."""
        with self._lock:
            return self._graph

    def get_node(self, node_id: str) -> Optional[Node]:
        with self._lock:
            if node_id not in self._graph.nodes:
                return None
            return self._graph.nodes[node_id]["data"]

    def get_edge_by_id(self, edge_id: str) -> Optional[Edge]:
        with self._lock:
            for _, _, edata in self._graph.edges(data=True):
                edge: Edge = edata["data"]
                if edge.id == edge_id:
                    return edge
        return None

    def get_all_edges(self) -> List[Edge]:
        with self._lock:
            return [edata["data"] for _, _, edata in self._graph.edges(data=True)]

    def get_all_nodes(self) -> List[Node]:
        with self._lock:
            return [ndata["data"] for _, ndata in self._graph.nodes(data=True)]

    def get_network_json(self) -> NetworkResponse:
        """Serialize the current graph state to the API response contract."""
        with self._lock:
            nodes = deepcopy(self.get_all_nodes())
            edges = deepcopy(self.get_all_edges())
            return NetworkResponse(nodes=nodes, edges=edges)

    # ------------------------------------------------------------------
    # Mutating operations
    # ------------------------------------------------------------------

    def apply_disruption(
        self,
        node_ids: List[str],
        edge_ids: List[str],
        delay_mult: float,
        cost_mult: float,
    ) -> None:
        """
        Mark the given nodes/edges as disrupted and stamp the disrupted
        edges with an inflated risk_factor derived from the AI-provided
        delay/cost multipliers, so downstream optimization reflects it.
        """
        with self._lock:
            for nid in node_ids:
                if nid in self._graph.nodes:
                    node: Node = self._graph.nodes[nid]["data"]
                    node.current_status = NodeStatus.DISRUPTED

            edge_id_set = set(edge_ids)
            for _, _, edata in self._graph.edges(data=True):
                edge: Edge = edata["data"]
                if edge.id in edge_id_set:
                    edge.is_disrupted = True
                    # Risk factor scales with the combined severity of the disruption.
                    edge.risk_factor = max(1.0, delay_mult * cost_mult)

    def reset_network(self) -> None:
        """Reset the graph back to the current baseline (default seed, or the
        user's own generated chain if one has been loaded via
        load_custom_network)."""
        self._build_baseline()

    def load_custom_network(self, nodes: List[Node], edges: List[Edge]) -> None:
        """
        Replace the entire network with a user-supplied chain (e.g. generated
        from their own free-text description) and make it the new baseline,
        so subsequent resets return to *this* chain rather than the demo seed.
        """
        with self._lock:
            self._baseline_nodes = deepcopy(nodes)
            self._baseline_edges = deepcopy(edges)
            self._build_baseline()

    def restore_default_demo_network(self) -> None:
        """Discard any custom chain and go back to the built-in demo network."""
        with self._lock:
            self._baseline_nodes = _seed_nodes()
            self._baseline_edges = _seed_edges()
            self._build_baseline()

    # ------------------------------------------------------------------
    # Metrics helpers (used by API layer for header summary metrics)
    # ------------------------------------------------------------------

    def summary_metrics(self) -> Dict[str, float]:
        with self._lock:
            nodes = self.get_all_nodes()
            edges = self.get_all_edges()
            disrupted_edges = [e for e in edges if e.is_disrupted]
            avg_delay = (
                sum(e.risk_factor for e in disrupted_edges) / len(disrupted_edges)
                if disrupted_edges
                else 1.0
            )
            return {
                "active_nodes": float(len(nodes)),
                "disrupted_routes": float(len(disrupted_edges)),
                "avg_latency_delay_pct": round((avg_delay - 1.0) * 100, 2),
            }


def get_twin() -> SupplyChainTwin:
    """FastAPI dependency-friendly accessor for the singleton twin instance."""
    return SupplyChainTwin()
