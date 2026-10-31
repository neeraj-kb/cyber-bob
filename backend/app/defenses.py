"""Candidate defense generators, intervention applications, and disruption calculations."""
import networkx as nx
from typing import List, Dict, Tuple, Set, Optional
from collections import Counter
from app.config import EFFORT_SCORES
from app.models import (
    AttackPath,
    DefenseResult,
    DisruptionBreakdown,
    DefenseType,
    Incident,
)


def calculate_disruption(
    G_original: nx.DiGraph,
    G_modified: nx.DiGraph,
    removed_edges: List[Tuple[str, str]],
    removed_nodes: List[str],
) -> DisruptionBreakdown:
    """
    Calculate business disruption according to instruction.md:
      disruption = sum(business_weight of removed edges) + sum(criticality of cut-off dependent nodes)
      
    Orphaned nodes: non-entry nodes whose in-degree became 0 in G_modified (cut off from upstream traffic),
    excluding nodes directly isolated/removed.
    """
    removed_edge_weights: Dict[str, int] = {}
    for u, v in removed_edges:
        edge_key = f"{u}->{v}"
        if G_original.has_edge(u, v):
            weight = G_original[u][v].get("business_weight", 1)
        else:
            weight = 1
        removed_edge_weights[edge_key] = weight

    orphaned_nodes_penalty: Dict[str, int] = {}
    for node_id in G_modified.nodes():
        if node_id in removed_nodes:
            continue
        is_entry = G_original.nodes[node_id].get("is_entry", False)
        orig_in_degree = G_original.in_degree(node_id)
        mod_in_degree = G_modified.in_degree(node_id)
        if not is_entry and orig_in_degree > 0 and mod_in_degree == 0:
            crit = G_original.nodes[node_id].get("criticality", 1)
            orphaned_nodes_penalty[node_id] = crit

    total_disruption = sum(removed_edge_weights.values()) + sum(orphaned_nodes_penalty.values())

    return DisruptionBreakdown(
        removed_edge_weights=removed_edge_weights,
        orphaned_nodes_penalty=orphaned_nodes_penalty,
        total_disruption=total_disruption,
    )


def generate_candidate_defenses(
    G: nx.DiGraph,
    incident: Incident,
    baseline_paths: List[AttackPath],
) -> List[Dict]:
    """
    Generate exactly three candidate defenses deterministically:
    1. Isolate host (compromised or pivot node)
    2. Revoke identity/credential (identity node on attack paths)
    3. Segment or block link (edge appearing in the most confirmed paths)
    """
    candidates: List[Dict] = []

    # 1. Isolate Host
    # Pick compromised node from incident; tie-break by node ID
    target_host = incident.compromised_nodes[0] if incident.compromised_nodes else sorted(list(G.nodes()))[0]
    # If multiple compromised nodes, pick the one appearing in the most paths
    if len(incident.compromised_nodes) > 1:
        node_counts = Counter()
        for p in baseline_paths:
            for n in p.nodes:
                if n in incident.compromised_nodes:
                    node_counts[n] += 1
        if node_counts:
            # Sort by count desc, then node ID asc
            sorted_hosts = sorted(incident.compromised_nodes, key=lambda n: (-node_counts[n], n))
            target_host = sorted_hosts[0]

    host_label = G.nodes[target_host].get("label", target_host) if target_host in G else target_host
    candidates.append({
        "defense_id": f"def-isolate-{target_host}",
        "name": f"Isolate Host: {host_label} ({target_host})",
        "type": "isolate_host",
        "target_id": target_host,
    })

    # 2. Revoke Identity / Credential
    # Find identity nodes traversed in attack paths
    identity_nodes_in_paths = Counter()
    for p in baseline_paths:
        for n in p.nodes:
            if G.has_node(n) and G.nodes[n].get("type") == "identity":
                identity_nodes_in_paths[n] += 1

    if identity_nodes_in_paths:
        # Pick identity appearing in most paths, tie-break by node ID
        target_identity = sorted(
            identity_nodes_in_paths.keys(),
            key=lambda x: (-identity_nodes_in_paths[x], x)
        )[0]
    else:
        # Fallback to any identity node in graph
        identities_in_graph = [n for n, d in G.nodes(data=True) if d.get("type") == "identity"]
        target_identity = sorted(identities_in_graph)[0] if identities_in_graph else "identity-default"

    id_label = G.nodes[target_identity].get("label", target_identity) if target_identity in G else target_identity
    candidates.append({
        "defense_id": f"def-revoke-{target_identity}",
        "name": f"Revoke Identity Credentials: {id_label} ({target_identity})",
        "type": "revoke_identity",
        "target_id": target_identity,
    })

    # 3. Segment or Block Link
    # Pick the edge appearing in the most confirmed paths
    confirmed_edge_counts = Counter()
    total_edge_counts = Counter()

    for p in baseline_paths:
        for edge_key in p.edges:
            total_edge_counts[edge_key] += 1
            if p.classification == "confirmed":
                confirmed_edge_counts[edge_key] += 1

    if confirmed_edge_counts:
        target_edge_key = sorted(
            confirmed_edge_counts.keys(),
            key=lambda e: (-confirmed_edge_counts[e], e)
        )[0]
    elif total_edge_counts:
        target_edge_key = sorted(
            total_edge_counts.keys(),
            key=lambda e: (-total_edge_counts[e], e)
        )[0]
    else:
        # Fallback to first available edge
        target_edge_key = f"{list(G.edges())[0][0]}->{list(G.edges())[0][1]}" if G.edges() else "web-01->app-srv-01"

    candidates.append({
        "defense_id": f"def-block-{target_edge_key.replace('->', '_to_')}",
        "name": f"Block Network Link: {target_edge_key}",
        "type": "block_link",
        "target_id": target_edge_key,
    })

    return candidates


def apply_defense_to_graph(
    G: nx.DiGraph,
    defense_type: DefenseType,
    target_id: str,
) -> Tuple[nx.DiGraph, List[str], List[Tuple[str, str]]]:
    """
    Apply defense intervention to a cloned copy of graph G.
    Returns: (modified_graph, removed_nodes, removed_edges)
    """
    G2 = G.copy()
    removed_nodes: List[str] = []
    removed_edges: List[Tuple[str, str]] = []

    if defense_type == "isolate_host":
        target_node = target_id
        if G2.has_node(target_node):
            incident_edges = list(G2.in_edges(target_node)) + list(G2.out_edges(target_node))
            for u, v in incident_edges:
                removed_edges.append((u, v))
                G2.remove_edge(u, v)
            removed_nodes.append(target_node)

    elif defense_type == "revoke_identity":
        target_identity = target_id
        if G2.has_node(target_identity):
            # Remove all access edges connected to this identity
            incident_edges = list(G2.in_edges(target_identity)) + list(G2.out_edges(target_identity))
            for u, v in incident_edges:
                edge_kind = G2[u][v].get("kind", "access")
                if edge_kind == "access" or True:  # Revoke credential cuts connectivity
                    removed_edges.append((u, v))
                    G2.remove_edge(u, v)

    elif defense_type == "block_link":
        if "->" in target_id:
            src, dst = target_id.split("->", 1)
            if G2.has_edge(src, dst):
                removed_edges.append((src, dst))
                G2.remove_edge(src, dst)

    return G2, removed_nodes, removed_edges

