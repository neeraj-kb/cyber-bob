# instruction.md — Build the Cybersecurity Flight Simulator

You are a senior full-stack engineer. Build the complete, working product described below. Do not produce a schedule or plan; produce code, run it, and verify it.

## 1. Product summary

**A Cybersecurity Flight Simulator: deterministic core, AI explains.**

A web app where a user loads a (synthetic) organization as a **digital-twin graph**, selects a simulated incident, and sees which attack paths reach critical assets. The app then simulates **three candidate defenses** on cloned copies of the graph, compares outcomes (paths left, business disruption, effort), recommends one in plain language, and lets a **human approve** it. After approval, the app applies it to the twin (simulated only) and **verifies** the updated graph.

Principles (non-negotiable):
1. **Deterministic core.** Graph traversal, scoring, and ranking are transparent rules in Python. No hidden weights.
2. **AI only explains.** An optional LLM (Gemini) writes plain-language rationale from computed results. It never decides, ranks, or changes data. The app must work fully with the LLM disabled.
3. **Human decides.** No automatic remediation. Every action requires explicit approval. Execution is simulated.
4. **Synthetic or authorized data only.**
5. **Missing visibility does not prove safety.** Unknown or unverified links are surfaced as uncertain, never silently treated as safe.

## 2. Tech stack

- Frontend: React + TypeScript, Tailwind CSS, React Flow (interactive graph)
- Backend: Python, FastAPI, NetworkX
- Storage: SQLite (twin state, runs, approvals), JSON/CSV for seed import
- Optional: Gemini API for explanations (env var `GEMINI_API_KEY`; fallback to templated text when absent)

## 3. Repository layout

```
/backend
  app/main.py              # FastAPI app, routes, CORS
  app/models.py            # Pydantic schemas
  app/db.py                # SQLite helpers
  app/graph_builder.py     # JSON/DB -> NetworkX DiGraph
  app/evidence.py          # event association, edge status/confidence/freshness
  app/attack_paths.py      # traversal + path classification
  app/defenses.py          # candidate defense generators + apply functions
  app/simulate.py          # clone, intervene, recompute, compare
  app/ranking.py           # rule-based ranking
  app/explain.py           # templated explanation + optional Gemini
  app/verify.py            # post-approval verification
  data/seed_org.json       # seeded synthetic organization
  data/seed_events.json    # synthetic events/evidence
  tests/                   # pytest
/frontend
  src/                     # React app (see section 8)
README.md
```

## 4. Data model

**Node**
```json
{"id": "web-01", "label": "Web Server", "type": "device|identity|app|data",
 "criticality": 1-5, "is_entry": false, "is_critical": false}
```
- `is_critical` = true for assets that must not be reachable (derive from `criticality >= 4` unless set explicitly).

**Edge**
```json
{"src": "web-01", "dst": "db-01", "kind": "access|trust|dependency",
 "status": "confirmed|needs_review|unknown",
 "confidence": 0.0-1.0, "last_seen": "ISO-8601 timestamp",
 "evidence_ids": ["ev-3"], "business_weight": 1-5}
```
- `business_weight` = how much the business depends on this link (used for disruption).

**Event** (synthetic evidence)
```json
{"id": "ev-3", "timestamp": "...", "asset_id": "web-01", "kind": "login|connection|process|alert",
 "detail": "...", "supports_edge": ["web-01->db-01"]}
```

**Incident**
```json
{"id": "inc-1", "title": "Suspicious login on web-01", "compromised_nodes": ["web-01"]}
```

## 5. Digital-twin construction (evidence pipeline)

Implement in `evidence.py` and `graph_builder.py`:

1. Create organization profile; add devices, identities, apps, data stores.
2. Define access/trust/dependency edges; assign business criticality.
3. Load synthetic events; normalize and associate events to assets and edges.
4. Build the NetworkX `DiGraph`.
5. For each edge decide status by rules (document them in code comments):
   - **confirmed**: has supporting evidence, fresh (within a configurable window, default 7 days), no conflicts.
   - **needs_review**: evidence is stale, incomplete, or conflicting.
   - **unknown**: no evidence either way.
6. Update `confidence` and `freshness` accordingly (e.g., confidence derived from evidence count and age; formula documented and unit-tested).
7. Publish the twin (persist to SQLite) and mark ready for simulation.

Edge-status legend must be shown in the UI:
- Confirmed link: supported by available evidence
- Needs-review link: incomplete, conflicting, or stale evidence
- Unknown link: insufficient information

## 6. Simulation engine (`attack_paths.py`, `simulate.py`)

**Baseline attack paths**
- Sources: the incident's `compromised_nodes` (plus any `is_entry` nodes if requested).
- Targets: all nodes with `is_critical`.
- Use `nx.all_simple_paths` with a cutoff (default 8) to enumerate paths.
- Classify each path:
  - **confirmed** if every edge on the path is `confirmed`
  - **uncertain** if it crosses any `needs_review` or `unknown` edge
- Return per path: node list, edge list, classification, target, the uncertain edges involved.
- Count critical assets reachable via confirmed paths and via uncertain paths separately.

**Counterfactuals**
- For each candidate defense: `G2 = G.copy()`, apply the intervention to `G2` only, recompute paths on `G2`. Never mutate the baseline graph.
- Output per defense: `confirmed_paths_left`, `uncertain_paths_left`, `critical_assets_reachable`, `disruption`, `effort`, `meets_target`, `removed_edges`, `removed_nodes`.

**Candidate defenses (exactly three, generated from the incident and graph)**
1. **Isolate host**: remove all edges incident to a chosen compromised or pivot node.
2. **Revoke identity/credential**: remove the access edges of a chosen identity node.
3. **Segment or block link**: remove one or more chosen trust edges on the attack paths (pick the edge appearing in the most confirmed paths).

Generate choices deterministically (e.g., node/edge with the highest path-coverage; ties broken by id). Each defense has a fixed `effort` score (1-5) defined in a config dict.

**Disruption**
- `disruption = sum(business_weight of removed edges) + sum(criticality of removed nodes' dependents cut off)`.
- Keep the formula simple, documented, and exposed in the API response (`disruption_breakdown`).

## 7. Decision engine (`ranking.py`)

Ranking rule, no hidden weights:
1. **Target:** a defense qualifies if it leaves **zero confirmed attack paths** to any critical asset.
2. **Rank** qualifying defenses by lowest `disruption`, then lowest `effort`, then defense id (stable tie-break).
3. **Flag** any defense whose remaining paths include uncertain ones; show them for human review.
4. **Human decides** and may choose any option, including a non-recommended or broader one.

If no defense qualifies: return `meets_target=false`, show remaining paths, and recommend adding controls or expert review (do not fake a recommendation).

Return the full ranking table with the reason each defense was ranked or disqualified.

## 8. API (FastAPI)

- `GET  /api/twin` — current graph (nodes, edges with status/confidence/last_seen)
- `PUT  /api/twin` — replace/edit synthetic org (nodes, edges); re-run evidence pipeline
- `POST /api/twin/node`, `POST /api/twin/edge`, `DELETE ...` — editable graph operations
- `GET  /api/incidents` — list simulated incidents
- `POST /api/simulate` `{incident_id}` — baseline paths + three counterfactuals + ranking
- `POST /api/explain` `{run_id}` — plain-language explanation (templated, or Gemini if configured)
- `POST /api/approve` `{run_id, defense_id, approver_note}` — records human approval, applies defense to the twin (simulated), returns updated graph
- `POST /api/verify` `{run_id}` — re-runs traversal on updated graph and returns pass/fail with remaining paths
- `GET  /api/runs/{id}` — stored run for audit

All responses are Pydantic-typed. Enable CORS for the dev frontend. Persist runs and approvals in SQLite.

## 9. Explanations (`explain.py`)

- Build a structured facts object from computed results (paths, counts, disruption, effort, flagged uncertain edges, evidence ids, confidence and freshness labels).
- Default: deterministic template that turns the facts into plain language.
- If `GEMINI_API_KEY` is set: send only the facts object, ask for a short plain-language rationale, and instruct the model to use only provided facts and cite evidence ids. Validate that the response does not name defenses or numbers not in the facts; otherwise fall back to the template.
- The explanation must mention: recommended action, why it was ranked first, residual uncertain paths needing human review, and that missing visibility does not prove safety.

## 10. Verification (`verify.py`)

After approval:
- Apply the defense to the twin; recompute baseline paths on the updated graph.
- Pass only if zero confirmed paths remain to critical assets.
- Report any uncertain paths still present; they remain flagged for human review.
- Assert and test that the pre-approval baseline stored for the run is unchanged.

## 11. Frontend

Single-page app, accessible dashboard, dark theme. Components:

1. **Graph view (React Flow):** nodes by type (device, identity, app, data) with criticality indicator; edges styled by status (confirmed = solid green, needs_review = dashed amber, unknown = dotted grey); attack paths highlightable; click node/edge for details (evidence, confidence, freshness).
2. **Twin editor:** add/edit/delete nodes and edges, set criticality and edge status inputs.
3. **Incident selector:** choose a simulated incident and run the simulation.
4. **Before/after view:** baseline graph vs graph after a selected defense (removed elements visibly marked).
5. **Comparison table:** the three defenses with confirmed paths left, uncertain paths left, disruption, effort, meets-target, rank.
6. **Recommendation panel:** plain-language explanation, evidence links, uncertain-path warning.
7. **Approval flow:** the human picks any option, adds a note, approves; then shows the verification result.
8. Legend for link statuses, keyboard-accessible controls, sufficient contrast, ARIA labels on interactive elements.

Use a typed API client (`src/api.ts`) mirroring backend schemas.

## 12. Seed data

Create a small, realistic synthetic organization (8-12 nodes) in `seed_org.json` that demonstrates:
- At least one confirmed attack path and one uncertain path (through a stale or unknown edge) to a critical asset.
- A trade-off: the cheapest defense leaves an uncertain path, while a broader defense is more disruptive but cleaner.
- Mixed edge statuses and varied freshness.

Include at least two incidents. All data is clearly synthetic.

## 13. Safety and privacy constraints

- Only synthetic or explicitly authorized data.
- No automatic remediation, no real network or system changes. "Execution" updates the twin only.
- Every state-changing action requires an explicit approval request and is logged.
- No secrets in the repo; read keys from environment variables.

## 14. Quality bar and acceptance criteria

Write pytest tests for:
- Edge status/confidence classification
- Path enumeration and confirmed vs uncertain classification
- Counterfactuals do not mutate the baseline graph
- Disruption calculation
- Ranking (qualification, tie-breaks, no-qualifier case)
- Verification pass and fail cases
- Explanation fallback when the LLM is unavailable or returns invalid content

The product is done when:
- [ ] `pip install -r requirements.txt && uvicorn app.main:app` starts the backend; `npm install && npm run dev` starts the frontend; the README documents both.
- [ ] Seeded org loads, graph renders, statuses and legend are visible.
- [ ] Running a simulation shows baseline paths and three defenses with comparison table.
- [ ] Ranking follows the rule exactly and flags uncertain paths.
- [ ] User can pick any option, approve, and see the verified updated graph.
- [ ] The app works end to end with no LLM key.
- [ ] All tests pass.

## 15. Working method for the agent

1. Read this file fully; list assumptions in the README rather than asking questions, unless something is contradictory.
2. Build backend core first (graph, paths, defenses, ranking, verify) with tests, then the API, then the frontend, then explanations.
3. Run the tests and the app yourself; fix failures before reporting.
4. Keep code typed, small, and documented; put every scoring constant in one config module.
5. Finish with a short summary: how to run, what was built, assumptions made, known gaps.

## 16. Out of scope (do not build unless asked)

- Live data collectors or real endpoint agents
- Automatic response or remediation
- Competing benign-vs-suspicious hypothesis engine
- Multi-organization or multi-tenant support
