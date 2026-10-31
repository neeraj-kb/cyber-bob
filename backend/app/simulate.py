"""Simulation engine: baseline traversal, counterfactual branching, and comparison."""
import uuid
import datetime
import networkx as nx
from typing import Optional, List, Dict
from app.config import EFFORT_SCORES
from app.models import (
    Incident,
    SimulationRun,
    DefenseResult,
    AttackPath,
)
from app.db import get_incident, save_run
from app.graph_builder import build_networkx_graph
from app.attack_paths import enumerate_attack_paths, get_reachable_critical_assets
from app.defenses import (
    generate_candidate_defenses,
    apply_defense_to_graph,
    calculate_disruption,
)
from app.ranking import rank_defenses


def run_simulation(incident_id: str, G_input: Optional[nx.DiGraph] = None) -> SimulationRun:
    """
    Run baseline attack path discovery, clone counterfactual graphs,
    simulate exactly three candidate defenses, and rank them deterministically.
    """
    incident = get_incident(incident_id)
    if not incident:
        # Fallback default incident if not found in db
        incident = Incident(
            id=incident_id,
            title=f"Simulated Incident {incident_id}",
            compromised_nodes=["web-01"],
        )

    # 1. Base Graph (Must remain immutable!)
    if G_input is not None:
        G = G_input.copy()
    else:
        G = build_networkx_graph()

    # Snapshot baseline nodes/edges count to guarantee immutability
    baseline_nodes_count = G.number_of_nodes()
    baseline_edges_count = G.number_of_edges()

    # 2. Baseline Attack Paths
    baseline_paths = enumerate_attack_paths(G, incident.compromised_nodes)
    baseline_reachable = get_reachable_critical_assets(baseline_paths)
    baseline_critical_assets = sorted(list(baseline_reachable["all"]))

    # 3. Generate exactly 3 candidate defenses
    raw_candidates = generate_candidate_defenses(G, incident, baseline_paths)

    evaluated_defenses: List[DefenseResult] = []

    # 4. Counterfactual Simulation on Cloned Graphs
    for cand in raw_candidates:
        defense_type = cand["type"]
        target_id = cand["target_id"]

        # Intervene only on clone G2; NEVER mutate baseline G
        G2, removed_nodes, removed_edges = apply_defense_to_graph(G, defense_type, target_id)

        # Recompute attack paths on G2
        paths_left = enumerate_attack_paths(G2, incident.compromised_nodes)
        reachable_left = get_reachable_critical_assets(paths_left)

        confirmed_count = len([p for p in paths_left if p.classification == "confirmed"])
        uncertain_count = len([p for p in paths_left if p.classification == "uncertain"])
        critical_assets_left = sorted(list(reachable_left["all"]))

        # Disruption calculation
        disruption_breakdown = calculate_disruption(G, G2, removed_edges, removed_nodes)

        # Fixed effort from config
        effort = EFFORT_SCORES.get(defense_type, 2)

        removed_edge_keys = [f"{u}->{v}" for u, v in removed_edges]

        evaluated_defenses.append(
            DefenseResult(
                defense_id=cand["defense_id"],
                name=cand["name"],
                type=defense_type,
                target_id=target_id,
                removed_nodes=removed_nodes,
                removed_edges=removed_edge_keys,
                confirmed_paths_left=confirmed_count,
                uncertain_paths_left=uncertain_count,
                critical_assets_reachable=critical_assets_left,
                disruption=disruption_breakdown.total_disruption,
                disruption_breakdown=disruption_breakdown,
                effort=effort,
                meets_target=(confirmed_count == 0),
            )
        )

    # Verify baseline graph was not mutated
    assert G.number_of_nodes() == baseline_nodes_count, "Baseline graph nodes were mutated during simulation!"
    assert G.number_of_edges() == baseline_edges_count, "Baseline graph edges were mutated during simulation!"

    # 5. Deterministic Ranking
    ranked_defenses = rank_defenses(evaluated_defenses)

    # Recommended defense is rank 1 if it meets target
    recommended_id = None
    for d in ranked_defenses:
        if d.rank == 1 and d.meets_target:
            recommended_id = d.defense_id
            break

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    sim_run = SimulationRun(
        run_id=run_id,
        incident_id=incident.id,
        timestamp=timestamp,
        baseline_paths=baseline_paths,
        baseline_critical_assets_reachable=baseline_critical_assets,
        candidate_defenses=ranked_defenses,
        recommended_defense_id=recommended_id,
    )

    save_run(sim_run)
    return sim_run

