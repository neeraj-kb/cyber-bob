"""Unit tests for explanation templating, Gemini integration fallback, and anti-hallucination validation."""
from app.explain import (
    generate_template_explanation,
    validate_gemini_facts,
    explain_run,
)
from app.simulate import run_simulation
from app.db import init_db, load_seed_data


def test_deterministic_template_explanation():
    facts = {
        "run_id": "run-test-1",
        "incident_id": "inc-1",
        "baseline_confirmed_paths": 2,
        "baseline_uncertain_paths": 1,
        "critical_assets_at_risk": ["cust-db-01"],
        "recommended_defense_id": "def-block-web_01_to_app_srv_01",
        "candidate_defenses": [
            {
                "defense_id": "def-block-web_01_to_app_srv_01",
                "name": "Block Network Link: web-01->app-srv-01",
                "rank": 1,
                "meets_target": True,
                "confirmed_paths_left": 0,
                "uncertain_paths_left": 1,
                "disruption": 4,
                "effort": 3,
            },
            {
                "defense_id": "def-isolate-web-01",
                "name": "Isolate Host: web-01",
                "rank": 2,
                "meets_target": True,
                "confirmed_paths_left": 0,
                "uncertain_paths_left": 0,
                "disruption": 8,
                "effort": 2,
            }
        ],
        "flagged_uncertain_edges": [
            {
                "edge": "web-01->jump-host",
                "status": "needs_review",
                "confidence": 0.45,
                "last_seen": "2026-10-10",
                "evidence_ids": ["ev-104"],
            }
        ],
        "evidence_cited": ["ev-101", "ev-104"],
    }

    result = generate_template_explanation(facts)

    assert result["mode"] == "template"
    assert "Recommended Action" in result["rationale"]
    assert "Block Network Link: web-01->app-srv-01" in result["rationale"]
    assert "Missing visibility does not prove safety" in result["uncertainty_warning"]
    assert "web-01->jump-host" in result["uncertainty_warning"]


def test_validate_gemini_facts_rejects_hallucinated_defenses():
    facts = {
        "candidate_defenses": [
            {"defense_id": "def-isolate-web-01"},
            {"defense_id": "def-block-link"},
        ]
    }

    # Text referencing valid defense
    valid_text = "I recommend applying def-isolate-web-01 because it meets the target."
    assert validate_gemini_facts(valid_text, facts) is True

    # Text introducing an unmentioned defense ID
    hallucinated_text = "I recommend applying def-fake-remediation-999 to solve the breach."
    assert validate_gemini_facts(hallucinated_text, facts) is False


def test_explain_run_falls_back_cleanly_without_gemini_key(monkeypatch):
    init_db()
    load_seed_data(force=True)
    sim_run = run_simulation("inc-1")

    # Ensure GEMINI_API_KEY is empty
    monkeypatch.setenv("GEMINI_API_KEY", "")

    response = explain_run(sim_run.run_id)
    assert response.mode == "template"
    assert response.recommended_defense_id is not None
    assert "Missing visibility does not prove safety" in response.uncertainty_warning

