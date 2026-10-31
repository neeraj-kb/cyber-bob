"""Post-approval verification engine and digital twin update routine."""
from typing import Optional
from app.models import VerificationResult, ApprovalRequest
from app.db import (
    get_run,
    get_twin,
    save_twin,
    save_approval,
    save_verification,
    get_incident,
)
from app.graph_builder import build_networkx_graph, graph_to_twin
from app.defenses import apply_defense_to_graph
from app.attack_paths import enumerate_attack_paths, get_reachable_critical_assets


def verify_approval(request: ApprovalRequest) -> VerificationResult:
    """
    Apply the approved defense to the digital twin (simulated only),
    recompute paths, and verify that zero confirmed paths remain to critical assets.
    """
    run_dict = get_run(request.run_id)
    if not run_dict:
        raise ValueError(f"Simulation run '{request.run_id}' not found")

    candidate_defenses = run_dict.get("candidate_defenses", [])
    chosen_defense = next((d for d in candidate_defenses if d.get("defense_id") == request.defense_id), None)
    if not chosen_defense:
        raise ValueError(f"Defense '{request.defense_id}' not found in candidate defenses of run '{request.run_id}'")

    # Snapshot baseline from run before any changes to verify immutability
    stored_baseline_paths = run_dict.get("baseline_paths", [])
    stored_incident_id = run_dict.get("incident_id")

    # 1. Load current live twin graph
    current_twin = get_twin()
    G = build_networkx_graph(current_twin)

    # 2. Apply defense to live twin graph
    defense_type = chosen_defense.get("type")
    target_id = chosen_defense.get("target_id")
    G_updated, removed_nodes, removed_edges = apply_defense_to_graph(G, defense_type, target_id)

    # 3. Save updated twin back to SQLite
    updated_twin = graph_to_twin(G_updated)
    save_twin(updated_twin)

    # 4. Re-run attack path discovery on updated twin
    incident = get_incident(stored_incident_id)
    compromised_nodes = incident.compromised_nodes if incident else ["web-01"]
    updated_paths = enumerate_attack_paths(G_updated, compromised_nodes)
    updated_reachable = get_reachable_critical_assets(updated_paths)

    confirmed_paths = [p for p in updated_paths if p.classification == "confirmed"]
    uncertain_paths = [p for p in updated_paths if p.classification == "uncertain"]

    confirmed_count = len(confirmed_paths)
    uncertain_count = len(uncertain_paths)
    critical_assets_left = sorted(list(updated_reachable["all"]))

    # Pass criteria: strictly zero confirmed paths left
    passed = (confirmed_count == 0)

    if passed:
        message = (
            f"VERIFICATION PASSED: Confirmed attack paths successfully reduced to 0. "
            f"Applied intervention '{chosen_defense.get('name')}' to twin."
        )
        if uncertain_count > 0:
            message += f" Note: {uncertain_count} residual uncertain path(s) remain flagged for manual operator triage."
    else:
        message = (
            f"VERIFICATION FAILED: {confirmed_count} confirmed attack path(s) still reach critical assets "
            f"({', '.join(critical_assets_left)})."
        )

    verification_result = VerificationResult(
        run_id=request.run_id,
        defense_id=request.defense_id,
        passed=passed,
        confirmed_paths_left=confirmed_count,
        uncertain_paths_left=uncertain_count,
        remaining_critical_assets=critical_assets_left,
        residual_uncertain_paths=uncertain_paths,
        message=message,
    )

    # 5. Persist approval and verification results
    save_approval(request.run_id, request.defense_id, request.approver_note)
    save_verification(request.run_id, verification_result)

    # Verify that stored baseline for this run was preserved
    persisted_run = get_run(request.run_id)
    assert persisted_run is not None
    assert len(persisted_run.get("baseline_paths", [])) == len(stored_baseline_paths), (
        "Baseline paths in stored run were corrupted during verification!"
    )

    return verification_result

