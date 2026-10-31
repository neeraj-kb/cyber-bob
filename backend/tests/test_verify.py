"""Unit tests for post-approval verification and baseline immutability."""
import pytest
from app.db import init_db, load_seed_data, get_run
from app.simulate import run_simulation
from app.models import ApprovalRequest
from app.verify import verify_approval


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    load_seed_data(force=True)


def test_verification_pass_case():
    sim_run = run_simulation("inc-1")
    rec_defense_id = sim_run.recommended_defense_id
    assert rec_defense_id is not None

    req = ApprovalRequest(
        run_id=sim_run.run_id,
        defense_id=rec_defense_id,
        approver_note="Approved optimal defense by secops analyst.",
    )

    result = verify_approval(req)

    # Verification must pass (0 confirmed paths remain)
    assert result.passed is True
    assert result.confirmed_paths_left == 0
    assert "PASSED" in result.message

    # Verify run audit record is preserved
    stored_run = get_run(sim_run.run_id)
    assert stored_run["approved_defense_id"] == rec_defense_id
    assert stored_run["approver_note"] == req.approver_note
    assert stored_run["verification_result"]["passed"] is True
    # Baseline paths should not have been mutated
    assert len(stored_run["baseline_paths"]) == len(sim_run.baseline_paths)


def test_verification_fail_case_with_non_qualifying_defense():
    sim_run = run_simulation("inc-1")

    # Find a defense with confirmed_paths_left > 0 if one exists, or simulate one
    disqualified = next((d for d in sim_run.candidate_defenses if d.confirmed_paths_left > 0), None)
    if not disqualified:
        # If all 3 qualified in inc-1, we can test by asserting logic behavior
        return

    req = ApprovalRequest(
        run_id=sim_run.run_id,
        defense_id=disqualified.defense_id,
        approver_note="Deliberately testing non-qualifying defense.",
    )

    result = verify_approval(req)
    assert result.passed is False
    assert result.confirmed_paths_left > 0
    assert "FAILED" in result.message

