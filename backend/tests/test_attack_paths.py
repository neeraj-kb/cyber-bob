"""Unit tests for path enumeration and confirmed vs uncertain path classification."""
import networkx as nx
from app.models import AttackPath
from app.attack_paths import enumerate_attack_paths, get_reachable_critical_assets


def test_path_enumeration_and_classification():
    G = nx.DiGraph()
    # Nodes: src=web-01, hop=app-01, target=db-01 (critical)
    G.add_node("web-01", is_critical=False, is_entry=True)
    G.add_node("app-01", is_critical=False, is_entry=False)
    G.add_node("db-01", is_critical=True, is_entry=False)

    # Edge 1: confirmed, Edge 2: confirmed
    G.add_edge("web-01", "app-01", status="confirmed", business_weight=3)
    G.add_edge("app-01", "db-01", status="confirmed", business_weight=4)

    paths = enumerate_attack_paths(G, source_nodes=["web-01"])
    assert len(paths) == 1
    assert paths[0].classification == "confirmed"
    assert paths[0].target == "db-01"
    assert paths[0].nodes == ["web-01", "app-01", "db-01"]
    assert paths[0].uncertain_edges == []


def test_path_with_stale_or_unknown_edge_is_uncertain():
    G = nx.DiGraph()
    G.add_node("web-01", is_critical=False, is_entry=True)
    G.add_node("jump-01", is_critical=False, is_entry=False)
    G.add_node("db-01", is_critical=True, is_entry=False)

    # First link is needs_review, second is confirmed
    G.add_edge("web-01", "jump-01", status="needs_review", business_weight=2)
    G.add_edge("jump-01", "db-01", status="confirmed", business_weight=5)

    paths = enumerate_attack_paths(G, source_nodes=["web-01"])
    assert len(paths) == 1
    assert paths[0].classification == "uncertain"
    assert "web-01->jump-01" in paths[0].uncertain_edges


def test_reachable_assets_separation():
    G = nx.DiGraph()
    G.add_node("src", is_critical=False)
    G.add_node("crit-1", is_critical=True)
    G.add_node("crit-2", is_critical=True)

    # Path to crit-1 is confirmed
    G.add_edge("src", "crit-1", status="confirmed")
    # Path to crit-2 is uncertain
    G.add_edge("src", "crit-2", status="unknown")

    paths = enumerate_attack_paths(G, source_nodes=["src"])
    reachable = get_reachable_critical_assets(paths)

    assert "crit-1" in reachable["confirmed"]
    assert "crit-2" in reachable["uncertain"]
    assert "crit-1" not in reachable["uncertain"]

