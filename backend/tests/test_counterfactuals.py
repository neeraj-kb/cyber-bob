"""Unit tests ensuring counterfactual simulation does not mutate the baseline graph."""
import networkx as nx
from app.models import Incident
from app.simulate import run_simulation


def test_baseline_graph_immutability():
    G = nx.DiGraph()
    G.add_node("web-01", is_critical=False, is_entry=True, label="Web Server", type="device", criticality=3)
    G.add_node("app-01", is_critical=False, is_entry=False, label="App Server", type="app", criticality=3)
    G.add_node("cust-db", is_critical=True, is_entry=False, label="Database", type="data", criticality=5)

    G.add_edge("web-01", "app-01", kind="access", status="confirmed", confidence=0.9, business_weight=4, evidence_ids=["ev1"], last_seen=None)
    G.add_edge("app-01", "cust-db", kind="dependency", status="confirmed", confidence=0.95, business_weight=5, evidence_ids=["ev2"], last_seen=None)

    orig_nodes = sorted(list(G.nodes()))
    orig_edges = sorted(list(G.edges()))
    orig_attrs = {n: dict(G.nodes[n]) for n in G.nodes()}

    # Run simulation with an explicit graph
    sim_run = run_simulation(incident_id="inc-1", G_input=G)

    # Assert G has not changed in any way
    assert sorted(list(G.nodes())) == orig_nodes
    assert sorted(list(G.edges())) == orig_edges
    for n in G.nodes():
        assert dict(G.nodes[n]) == orig_attrs[n]

    # Candidate defenses should have evaluated and produced results
    assert len(sim_run.candidate_defenses) == 3

