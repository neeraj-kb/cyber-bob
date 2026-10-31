"""Graph builder: converts digital twin representations to and from NetworkX DiGraph."""
import networkx as nx
from typing import Optional
from app.models import TwinGraph, Node, Edge
from app.db import get_twin, save_twin


def build_networkx_graph(twin: Optional[TwinGraph] = None) -> nx.DiGraph:
    """Construct a NetworkX DiGraph populated with digital twin nodes and edge attributes."""
    if twin is None:
        twin = get_twin()

    G = nx.DiGraph()

    for node in twin.nodes:
        G.add_node(
            node.id,
            label=node.label,
            type=node.type,
            criticality=node.criticality,
            is_entry=node.is_entry,
            is_critical=node.is_critical,
        )

    for edge in twin.edges:
        G.add_edge(
            edge.src,
            edge.dst,
            kind=edge.kind,
            status=edge.status,
            confidence=edge.confidence,
            last_seen=edge.last_seen,
            evidence_ids=edge.evidence_ids,
            business_weight=edge.business_weight,
        )

    return G


def graph_to_twin(G: nx.DiGraph) -> TwinGraph:
    """Convert a NetworkX DiGraph back into a strongly-typed TwinGraph model."""
    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append(
            Node(
                id=node_id,
                label=data.get("label", node_id),
                type=data.get("type", "device"),
                criticality=data.get("criticality", 1),
                is_entry=data.get("is_entry", False),
                is_critical=data.get("is_critical", False),
            )
        )

    edges = []
    for u, v, data in G.edges(data=True):
        edges.append(
            Edge(
                src=u,
                dst=v,
                kind=data.get("kind", "access"),
                status=data.get("status", "unknown"),
                confidence=data.get("confidence", 0.0),
                last_seen=data.get("last_seen", None),
                evidence_ids=data.get("evidence_ids", []),
                business_weight=data.get("business_weight", 1),
            )
        )

    return TwinGraph(nodes=nodes, edges=edges)


def publish_twin_graph(G: nx.DiGraph) -> TwinGraph:
    """Persist graph state to SQLite and return TwinGraph."""
    twin = graph_to_twin(G)
    save_twin(twin)
    return twin

