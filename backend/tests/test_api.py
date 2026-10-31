"""Integration tests for all FastAPI REST route handlers."""
import pytest
from app.main import (
    health_check,
    get_digital_twin,
    add_or_update_node,
    remove_node,
    list_incidents,
    simulate_flight,
    explain_simulation,
    approve_defense,
    verify_simulation,
    get_run_audit,
)
from app.models import Node, SimulationRequest, ExplainRequest, ApprovalRequest
from app.db import init_db, load_seed_data


@pytest.fixture(autouse=True)
def setup_api_db():
    init_db()
    load_seed_data(force=True)


def test_health_check():
    res = health_check()
    assert res["status"] == "healthy"


def test_get_digital_twin():
    twin = get_digital_twin()
    assert len(twin.nodes) >= 8
    assert len(twin.edges) >= 8


def test_twin_node_crud():
    new_node = Node(
        id="test-box-01",
        label="Test Box",
        type="device",
        criticality=2,
        is_entry=False,
        is_critical=False,
    )
    # Create
    created = add_or_update_node(new_node)
    assert created.id == "test-box-01"

    # Verify present
    twin = get_digital_twin()
    assert any(n.id == "test-box-01" for n in twin.nodes)

    # Delete
    remove_node("test-box-01")

    # Verify deleted
    twin_after = get_digital_twin()
    assert not any(n.id == "test-box-01" for n in twin_after.nodes)


def test_list_incidents():
    incidents = list_incidents()
    assert len(incidents) >= 2
    assert any(i.id == "inc-1" for i in incidents)


def test_simulation_workflow_and_approval():
    # 1. Run simulation
    sim_data = simulate_flight(SimulationRequest(incident_id="inc-1"))
    run_id = sim_data.run_id
    assert len(sim_data.baseline_paths) > 0
    assert len(sim_data.candidate_defenses) == 3

    # 2. Explain simulation
    exp_data = explain_simulation(ExplainRequest(run_id=run_id))
    assert exp_data.run_id == run_id
    assert "Missing visibility does not prove safety" in exp_data.uncertainty_warning

    # 3. Approve top defense
    rec_defense_id = sim_data.recommended_defense_id
    assert rec_defense_id is not None
    appr_data = approve_defense(
        ApprovalRequest(
            run_id=run_id,
            defense_id=rec_defense_id,
            approver_note="Approved during integration test",
        )
    )
    assert appr_data["status"] == "approved"
    assert appr_data["verification"]["passed"] is True

    # 4. Verify endpoint
    ver_result = verify_simulation(ExplainRequest(run_id=run_id))
    assert ver_result.passed is True

    # 5. Audit endpoint
    audit_data = get_run_audit(run_id)
    assert audit_data["approved_defense_id"] == rec_defense_id
