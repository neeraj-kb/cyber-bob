"""Unit tests for disruption score and breakdown calculation."""
import networkx as nx
from app.defenses import calculate_disruption, apply_defense_to_graph


def test_disruption_calculation_simple_cut():
    G = nx.DiGraph()
    G.add_node("n1", is_entry=True, criticality=2)
    G.add_node("n2", is_entry=False, criticality=3)
    G.add_edge("n1", "n2", business_weight=4)

    G2, removed_nodes, removed_edges = apply_defense_to_graph(G, "block_link", "n1->n2")

    breakdown = calculate_disruption(G, G2, removed_edges, removed_nodes)

    # Edge weight = 4.
    # n2 lost its only incoming edge and is not entry, so orphaned penalty = criticality(3).
    # Total = 4 + 3 = 7.
    assert breakdown.removed_edge_weights == {"n1->n2": 4}
    assert breakdown.orphaned_nodes_penalty == {"n2": 3}
    assert breakdown.total_disruption == 7


def test_disruption_calculation_multiple_edges():
    G = nx.DiGraph()
    G.add_node("host", is_entry=False, criticality=3)
    G.add_node("upstream", is_entry=True, criticality=2)
    G.add_node("downstream1", is_entry=False, criticality=4)
    G.add_node("downstream2", is_entry=False, criticality=5)

    G.add_edge("upstream", "host", business_weight=3)
    G.add_edge("host", "downstream1", business_weight=2)
    G.add_edge("host", "downstream2", business_weight=4)

    # Also downstream2 has another upstream link, so it's NOT orphaned!
    G.add_node("other_srv", is_entry=True, criticality=2)
    G.add_edge("other_srv", "downstream2", business_weight=2)

    G2, removed_nodes, removed_edges = apply_defense_to_graph(G, "isolate_host", "host")
    breakdown = calculate_disruption(G, G2, removed_edges, removed_nodes)

    # Sum of severed edges: 3 + 2 + 4 = 9
    # downstream1 becomes orphaned (in-degree 0, was 1): penalty = 4
    # downstream2 still has in-degree 1 from other_srv: penalty = 0
    # host is directly isolated, so excluded from orphan penalties
    assert breakdown.total_disruption == 9 + 4

