# Task Roadmap: Cybersecurity Flight Simulator

This document tracks all tasks, milestones, implementation status, and verification steps for the **Cybersecurity Flight Simulator** based on [instruction.md](file:///c:/Users/Neeraj/OneDrive/Desktop/Kodikon_6.0/instruction.md).

---

## Progress Overview

- [x] **Phase 1: Project Setup & Core Configuration**
- [x] **Phase 2: Data Models, Seeds & Database Storage**
- [x] **Phase 3: Digital Twin & Evidence Processing Pipeline**
- [x] **Phase 4: Attack Path Traversal & Path Classification Engine**
- [x] **Phase 5: Candidate Defenses Generator & Counterfactual Simulation**
- [x] **Phase 6: Deterministic Ranking Decision Engine**
- [x] **Phase 7: Plain-Language Explanations Engine (Dual-Mode: Template + Gemini)**
- [x] **Phase 8: Post-Approval Verification Engine**
- [x] **Phase 9: FastAPI REST API & Endpoints**
- [x] **Phase 10: Backend Unit & Integration Test Suite**
- [x] **Phase 11: Frontend Application Setup (React + Vite + TypeScript + Tailwind)**
- [x] **Phase 12: Interactive Frontend Components & React Flow Visualizer**
- [x] **Phase 13: End-to-End System Testing & Documentation**

---

## Detailed Task Breakdown

### Phase 1: Project Setup & Core Configuration
- [x] Create repository structure:
  - `/backend/app`
  - `/backend/data`
  - `/backend/tests`
  - `/frontend`
- [x] Create `/backend/app/config.py`:
  - Centralize all scoring constants, weights, freshness windows, and default limits:
    - `FRESHNESS_WINDOW_DAYS` (7 days)
    - `DEFAULT_PATH_CUTOFF` (8)
    - `EFFORT_SCORES`: fixed effort mapping (`isolate_host`: 2, `revoke_identity`: 1, `block_link`: 3)
    - `CRITICALITY_THRESHOLD` (criticality >= 4)
    - `GEMINI_MODEL` (`gemini-2.5-flash`)
- [x] Setup Python environment dependencies in `/backend/requirements.txt`:
  - `fastapi`, `uvicorn[standard]`, `pydantic`, `networkx`, `google-genai`, `pytest`, `httpx`

### Phase 2: Data Models, Seeds & Database Storage
- [x] Implement `/backend/app/models.py` with Pydantic v2 schemas:
  - `Node`, `Edge`, `Event`, `Incident`, `AttackPath`, `DefenseResult`, `DisruptionBreakdown`, `SimulationRun`, `ApprovalRequest`, `VerificationResult`.
- [x] Implement `/backend/app/db.py`:
  - SQLite persistence for twin state (`twin_nodes`, `twin_edges`), `events`, `incidents`, `runs`, and approvals.
- [x] Create synthetic seed datasets in `/backend/data/`:
  - `seed_org.json`: 10-node realistic hybrid enterprise environment demonstrating trade-off.
  - `seed_events.json`: Confirmed, stale, conflicting, and missing telemetry events.

### Phase 3: Digital Twin & Evidence Processing Pipeline
- [x] Implement `/backend/app/evidence.py`:
  - Rule-based edge status classification: `confirmed`, `needs_review`, `unknown`.
  - Mathematical confidence scoring formula with exponential decay over time.
- [x] Implement `/backend/app/graph_builder.py`:
  - Converting SQLite/JSON nodes & edges into a NetworkX `DiGraph` and back.

### Phase 4: Attack Path Traversal Engine
- [x] Implement `/backend/app/attack_paths.py`:
  - Simple path enumeration with cutoff limit from sources to critical targets.
  - Path classification: confirmed vs uncertain.
  - Reachable critical asset set and counts.

### Phase 5: Candidate Defenses Generator & Counterfactual Simulation
- [x] Implement `/backend/app/defenses.py`:
  - 3 deterministic candidate defense generators: `isolate_host`, `revoke_identity`, `block_link`.
  - Disruption calculation: edge weights + orphaned node penalties.
- [x] Implement `/backend/app/simulate.py`:
  - Counterfactual simulation: `G2 = G.copy()`.
  - Immutable baseline graph verification.

### Phase 6: Deterministic Ranking Decision Engine
- [x] Implement `/backend/app/ranking.py`:
  - Gate: 0 confirmed paths to critical assets.
  - Sorting: lowest disruption -> lowest effort -> stable tie-breaker ID.
  - Flagging residual uncertain paths.

### Phase 7: Explanations Engine (Dual-Mode: Template + Gemini)
- [x] Implement `/backend/app/explain.py`:
  - Structured `Facts` payload.
  - Deterministic template generator citing facts, ranking rationale, trade-offs, and residual risks.
  - Gemini 2.5 integration with strict fact-boundary anti-hallucination validation and seamless offline fallback.

### Phase 8: Post-Approval Verification Engine
- [x] Implement `/backend/app/verify.py`:
  - Apply approved defense to digital twin in SQLite.
  - Re-run path traversal on updated twin.
  - Pass criteria: confirmed paths == 0.
  - Verify baseline snapshot immutability.

### Phase 9: FastAPI REST Endpoints & API Server
- [x] Implement `/backend/app/main.py`:
  - `GET /api/twin`, `PUT /api/twin`, `POST /api/twin/reset`
  - `POST /api/twin/node`, `DELETE /api/twin/node/{id}`
  - `POST /api/twin/edge`, `DELETE /api/twin/edge`
  - `GET /api/incidents`
  - `POST /api/simulate`
  - `POST /api/explain`
  - `POST /api/approve`
  - `POST /api/verify`
  - `GET /api/runs/{id}`

### Phase 10: Backend Unit & Integration Test Suite
- [x] 24/24 tests passing:
  - `test_evidence.py`
  - `test_attack_paths.py`
  - `test_counterfactuals.py`
  - `test_disruption.py`
  - `test_ranking.py`
  - `test_verify.py`
  - `test_explain.py`
  - `test_api.py`

### Phase 11: Frontend Application Setup
- [x] Vite + React 18 + TypeScript + Tailwind CSS setup in `/frontend`.
- [x] Typed API client in `/frontend/src/api.ts`.

### Phase 12: Interactive Frontend Components & React Flow Visualizer
- [x] Interactive Graph Canvas (`@xyflow/react`) with custom nodes, status-styled edges, and pulsing attack path animations.
- [x] Status legend for confirmed, needs-review, and unknown links.
- [x] Incident bar with flight simulator trigger and reset.
- [x] Candidate defenses comparison table with rank, metrics, and disruption breakdown accordion.
- [x] Before / After counterfactual diff viewer (previewing severed links and isolated hosts).
- [x] Plain-language rationale panel with residual uncertainty warning banner.
- [x] Human-in-the-loop approval modal and automated verification result card.
- [x] Digital twin node/edge editor drawer.
- [x] Node and link telemetry detail inspector.

### Phase 13: End-to-End System Testing & Documentation
- [x] Automated backend tests verified (100% pass).
- [x] Frontend TypeScript type-checking and Vite production build verified (`npm run build`).
- [x] Complete [README.md](file:///c:/Users/Neeraj/OneDrive/Desktop/Kodikon_6.0/README.md) with startup instructions, scenario walkthrough, and documented assumptions.
