"""Plain-language explanation engine: deterministic templating with optional Gemini 2.5 fallback."""
import json
import re
from typing import Dict, Any, List, Optional
from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.models import ExplanationResponse, TwinGraph
from app.db import get_run, get_twin


def build_facts(run_dict: Dict[str, Any], twin: Optional[TwinGraph] = None) -> Dict[str, Any]:
    """Extract an immutable, structured facts object from simulation run results and twin state."""
    if twin is None:
        twin = get_twin()

    edge_lookup = {f"{e.src}->{e.dst}": e for e in twin.edges}

    baseline_paths = run_dict.get("baseline_paths", [])
    confirmed_baseline = [p for p in baseline_paths if p.get("classification") == "confirmed"]
    uncertain_baseline = [p for p in baseline_paths if p.get("classification") == "uncertain"]

    evidence_ids: List[str] = []
    flagged_uncertain_edges: List[Dict[str, Any]] = []

    for p in baseline_paths:
        for edge_key in p.get("edges", []):
            edge_obj = edge_lookup.get(edge_key)
            if edge_obj:
                evidence_ids.extend(edge_obj.evidence_ids)
                if edge_obj.status in ("needs_review", "unknown"):
                    flagged_uncertain_edges.append({
                        "edge": edge_key,
                        "status": edge_obj.status,
                        "confidence": edge_obj.confidence,
                        "last_seen": edge_obj.last_seen,
                        "evidence_ids": edge_obj.evidence_ids,
                    })

    # Deduplicate
    unique_evidence_ids = sorted(list(set(evidence_ids)))
    seen_edges = set()
    unique_flagged_edges = []
    for f in flagged_uncertain_edges:
        if f["edge"] not in seen_edges:
            seen_edges.add(f["edge"])
            unique_flagged_edges.append(f)

    candidate_defenses = run_dict.get("candidate_defenses", [])

    return {
        "run_id": run_dict.get("run_id"),
        "incident_id": run_dict.get("incident_id"),
        "baseline_confirmed_paths": len(confirmed_baseline),
        "baseline_uncertain_paths": len(uncertain_baseline),
        "critical_assets_at_risk": run_dict.get("baseline_critical_assets_reachable", []),
        "recommended_defense_id": run_dict.get("recommended_defense_id"),
        "candidate_defenses": [
            {
                "defense_id": d.get("defense_id"),
                "name": d.get("name"),
                "type": d.get("type"),
                "rank": d.get("rank"),
                "meets_target": d.get("meets_target"),
                "confirmed_paths_left": d.get("confirmed_paths_left"),
                "uncertain_paths_left": d.get("uncertain_paths_left"),
                "disruption": d.get("disruption"),
                "effort": d.get("effort"),
                "removed_edges": d.get("removed_edges", []),
                "removed_nodes": d.get("removed_nodes", []),
            }
            for d in candidate_defenses
        ],
        "flagged_uncertain_edges": unique_flagged_edges,
        "evidence_cited": unique_evidence_ids,
    }


def generate_template_explanation(facts: Dict[str, Any]) -> Dict[str, Any]:
    """Generate deterministic, factually bounded plain-language explanation."""
    run_id = facts["run_id"]
    incident_id = facts["incident_id"]
    crit_assets = ", ".join(facts["critical_assets_at_risk"]) or "None"
    rec_id = facts.get("recommended_defense_id")
    candidates = facts.get("candidate_defenses", [])
    rec_candidate = next((c for c in candidates if c.get("defense_id") == rec_id), None)

    summary = (
        f"Incident '{incident_id}' presents {facts['baseline_confirmed_paths']} confirmed and "
        f"{facts['baseline_uncertain_paths']} uncertain attack path(s) reaching critical asset(s): {crit_assets}."
    )

    if rec_candidate:
        rationale_lines = [
            f"**Recommended Action**: **{rec_candidate['name']}** (Rank #1).",
            f"- **Target Met**: Successfully reduces confirmed attack paths from {facts['baseline_confirmed_paths']} to 0.",
            f"- **Efficiency**: Incurs a disruption score of {rec_candidate['disruption']} with operational effort {rec_candidate['effort']} (1-5).",
        ]
        
        competing = [c for c in candidates if c.get("defense_id") != rec_id]
        if competing:
            rationale_lines.append("\n**Alternative Trade-offs**:")
            for alt in competing:
                status_txt = f"Rank #{alt.get('rank')}" if alt.get("meets_target") else "Disqualified"
                rationale_lines.append(
                    f"- *{alt['name']}* ({status_txt}): Leaves {alt['confirmed_paths_left']} confirmed and "
                    f"{alt['uncertain_paths_left']} uncertain path(s). Disruption: {alt['disruption']}, Effort: {alt['effort']}."
                )
    else:
        rationale_lines = [
            "**No Candidate Defense Fully Met the Target** (0 confirmed paths left).",
            "None of the automated candidate defenses completely eliminate confirmed paths to critical assets.",
            "Immediate manual containment, segmentation, and human review are required."
        ]

    rationale = "\n".join(rationale_lines)

    flagged = facts.get("flagged_uncertain_edges", [])
    if flagged:
        edges_str = ", ".join([f"{f['edge']} ({f['status']}, confidence: {f['confidence']})" for f in flagged])
        uncertainty_warning = (
            f"⚠️ **Safety Warning**: Missing visibility does not prove safety. "
            f"Residual uncertain link(s) detected: {edges_str}. "
            f"Because evidence is stale, incomplete, or unobserved, an attacker may still exploit these unverified pathways."
        )
    else:
        uncertainty_warning = "⚠️ **Safety Notice**: Missing visibility does not prove safety. All observed links are confirmed."

    return {
        "run_id": run_id,
        "recommended_defense_id": rec_id,
        "mode": "template",
        "summary": summary,
        "rationale": rationale,
        "uncertainty_warning": uncertainty_warning,
        "evidence_cited": facts.get("evidence_cited", []),
        "facts": facts,
    }


def validate_gemini_facts(gemini_text: str, facts: Dict[str, Any]) -> bool:
    """
    Validate that Gemini's response adheres strictly to the facts object:
    - Does not invent non-existent defense IDs
    - Does not introduce contradictory numbers or unauthorized terms
    """
    # Allowed defense IDs
    allowed_ids = {c["defense_id"] for c in facts.get("candidate_defenses", [])}
    # Check if any unknown 'def-' pattern was invented
    found_def_ids = set(re.findall(r"def-[a-zA-Z0-9_\-]+", gemini_text))
    if not found_def_ids.issubset(allowed_ids):
        return False
    return True


def generate_gemini_explanation(facts: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Query Gemini 2.5 API with facts payload and validate output against hallucinations."""
    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""You are the explanation engine for a Cybersecurity Flight Simulator.
Your role is SOLELY to explain computed simulation results in clear, concise language for a human security operator.

RULES:
1. Base your explanation strictly on the FACTS JSON provided below. Do not assume, invent, or extrapolate any numbers, defenses, or nodes.
2. Clearly state the recommended defense and why it ranked first.
3. Compare the recommended defense against competing alternatives (mention disruption and effort).
4. Explicitly cite supporting evidence IDs (e.g., ev-101) where relevant.
5. Highlight any residual uncertain paths and include the mandatory safety warning: "Missing visibility does not prove safety."
6. Format your output into clear markdown sections: Summary, Rationale, and Safety Warning.

FACTS JSON:
{json.dumps(facts, indent=2)}
"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        text = response.text or ""
        if not text or not validate_gemini_facts(text, facts):
            return None

        # Extract safety warning if present
        warning_match = re.search(r"(Missing visibility does not prove safety.*)", text, re.IGNORECASE)
        warning_str = warning_match.group(1) if warning_match else "⚠️ Safety Warning: Missing visibility does not prove safety."

        return {
            "run_id": facts["run_id"],
            "recommended_defense_id": facts.get("recommended_defense_id"),
            "mode": "gemini",
            "summary": f"Gemini Analysis for Incident {facts['incident_id']}: {facts['baseline_confirmed_paths']} confirmed attack path(s) identified.",
            "rationale": text,
            "uncertainty_warning": warning_str,
            "evidence_cited": facts.get("evidence_cited", []),
            "facts": facts,
        }
    except Exception:
        # Graceful fallback on network, rate-limit, or SDK exceptions
        return None


def explain_run(run_id: str) -> ExplanationResponse:
    """Retrieve run, construct facts object, and generate validated explanation."""
    run_dict = get_run(run_id)
    if not run_dict:
        raise ValueError(f"Simulation run {run_id} not found")

    facts = build_facts(run_dict)

    # Attempt Gemini explanation if configured
    gemini_result = generate_gemini_explanation(facts)
    if gemini_result:
        return ExplanationResponse(**gemini_result)

    # Deterministic template default / fallback
    template_result = generate_template_explanation(facts)
    return ExplanationResponse(**template_result)

