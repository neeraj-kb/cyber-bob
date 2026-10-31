"""Attack path traversal and classification engine."""
import networkx as nx
from typing import List, Tuple, Set, Optional, Dict
from app.config import DEFAULT_PATH_CUTOFF
from app.models import AttackPath, PathClassification


def enumerate_attack_paths(
    G: nx.DiGraph,
    source_nodes: List[str],
    include_entry_nodes: bool = False,
    cutoff: int = DEFAULT_PATH_CUTOFF,
) -> List[AttackPath]:
    """
    Enumerate simple directed attack paths from sources to critical targets.
    
    Classification:
      - confirmed: if every edge along the path has status == 'confirmed'
      - uncertain: if the path traverses any edge with status 'needs_review' or 'unknown'
    """
    sources: Set[str] = set()
    for s in source_nodes:
        if s in G:
            sources.add(s)

    if include_entry_nodes:
        for node_id, data in G.nodes(data=True):
            if data.get("is_entry", False):
                sources.add(node_id)

    # Critical targets: nodes where is_critical is True
    critical_targets: Set[str] = {
        node_id for node_id, data in G.nodes(data=True) if data.get("is_critical", False)
    }

    discovered_paths: List[AttackPath] = []
    seen_path_signatures: Set[Tuple[str, ...]] = set()

    for src in sorted(sources):
        for target in sorted(critical_targets):
            if src == target:
                continue
            if not nx.has_path(G, src, target):
                continue

            try:
                paths_gen = nx.all_simple_paths(G, source=src, target=target, cutoff=cutoff)
                for path in paths_gen:
                    path_tuple = tuple(path)
                    if path_tuple in seen_path_signatures:
                        continue
                    seen_path_signatures.add(path_tuple)

                    edge_keys: List[str] = []
                    uncertain_edges: List[str] = []
                    is_confirmed = True

                    for i in range(len(path) - 1):
                        u, v = path[i], path[i + 1]
                        edge_data = G.get_edge_data(u, v) or {}
                        edge_key = f"{u}->{v}"
                        edge_keys.append(edge_key)

                        edge_status = edge_data.get("status", "unknown")
                        if edge_status != "confirmed":
                            is_confirmed = False
                            uncertain_edges.append(edge_key)

                    classification: PathClassification = "confirmed" if is_confirmed else "uncertain"

                    discovered_paths.append(
                        AttackPath(
                            nodes=path,
                            edges=edge_keys,
                            classification=classification,
                            target=target,
                            uncertain_edges=uncertain_edges,
                        )
                    )
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

    return discovered_paths


def get_reachable_critical_assets(paths: List[AttackPath]) -> Dict[str, Set[str]]:
    """Return sets of critical assets reachable via confirmed paths vs uncertain paths."""
    confirmed_assets: Set[str] = set()
    uncertain_assets: Set[str] = set()

    for p in paths:
        if p.classification == "confirmed":
            confirmed_assets.add(p.target)
        else:
            uncertain_assets.add(p.target)

    return {
        "confirmed": confirmed_assets,
        "uncertain": uncertain_assets,
        "all": confirmed_assets.union(uncertain_assets),
    }

