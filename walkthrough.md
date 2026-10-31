# Cybersecurity Flight Simulator: Architecture & Implementation Walkthrough

The **Cybersecurity Flight Simulator** is a full-stack digital-twin platform designed to model security incidents, evaluate attack trajectories, simulate candidate interventions on cloned counterfactual graphs, and rank defenses deterministically.

This document serves as the architectural specification and implementation guide for building, operating, and verifying the platform as outlined in [instruction.md](file:///c:/Users/Neeraj/OneDrive/Desktop/Kodikon_6.0/instruction.md).

---

## 1. Core Philosophy & Non-Negotiable Principles

```
  ┌───────────────────────────────────────────────────────────┐
  │                 DETERMINISTIC CORE                        │
  │  • Graph Traversal (NetworkX DiGraph)                     │
  │  • Evidence & Confidence Rules                            │
  │  • Counterfactual Branching (G2 = G.copy())               │
  │  • Mathematical Disruption Scoring                        │
  │  • Multi-Tier Objective Ranking Rules                     │
  └─────────────────────────────┬─────────────────────────────┘
                                │ Structured Facts Object
                                ▼
  ┌───────────────────────────────────────────────────────────┐
  │                 AI EXPLANATION LAYER                      │
  │  • Explains computed facts only in plain language         │
  │  • Never decides, ranks, scores, or mutates data          │
  │  • Optional Gemini 2.5 API with strict validator          │
  │  • Fully functional offline via deterministic templates   │
  └─────────────────────────────┬─────────────────────────────┘
                                │ Recommended Options
                                ▼
  ┌───────────────────────────────────────────────────────────┐
  │                  HUMAN DECISION LAYER                     │
  │  • Human approves all state-changing interventions        │
  │  • Discretion to choose any candidate defense             │
  │  • Simulated execution on digital twin only               │
  │  • Post-approval automated verification                   │
  └───────────────────────────────────────────────────────────┘
```

1. **Deterministic Core**: Graph traversal, attack path classification, disruption metrics, and defense rankings are 100% computed using explicit Python algorithms. No hidden weights, fuzzy heuristics, or neural decision-making.
2. **AI Only Explains**: An optional Large Language Model (Gemini) generates human-readable narratives strictly derived from a structured facts object. The app functions completely without the LLM via built-in templating.
3. **Human Decides**: Remediation is never automated. Every defense requires explicit human approval with audit notes.
4. **Synthetic and Safe**: Operations run solely against digital twins; no real-world infrastructure is touched.
5. **Missing Visibility != Safety**: Missing or stale evidence is never assumed safe. Attack paths crossing unverified or stale links are surfaced as **uncertain** and require explicit operator triage.

---

## 2. System Architecture & Component Layout

The repository is structured into two cleanly separated subsystems:

```
Kodikon_6.0/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py             # Global constants, effort weights, thresholds
│   │   ├── models.py             # Pydantic v2 schemas for all API & twin entities
│   │   ├── db.py                 # SQLite persistence for twin, runs & approvals
│   │   ├── graph_builder.py      # NetworkX DiGraph builder & SQLite synchronization
│   │   ├── evidence.py           # Synthetic event parser, freshness & confidence math
│   │   ├── attack_paths.py       # Traversal engine & path classification (confirmed/uncertain)
│   │   ├── defenses.py           # 3 deterministic candidate defense generators & disruption scoring
│   │   ├── simulate.py           # Counterfactual graph cloner & evaluator
│   │   ├── ranking.py            # Transparent rule-based ranking engine
│   │   ├── explain.py            # Dual-mode explanation (Template + Gemini LLM)
│   │   ├── verify.py             # Post-approval verification engine
│   │   └── main.py               # FastAPI application, CORS & REST endpoints
│   ├── data/
│   │   ├── seed_org.json         # 8-12 node synthetic enterprise twin
│   │   └── seed_events.json      # Synthetic security and telemetry events
│   ├── tests/
│   │   ├── test_evidence.py
│   │   ├── test_attack_paths.py
│   │   ├── test_counterfactuals.py
│   │   ├── test_disruption.py
│   │   ├── test_ranking.py
│   │   ├── test_verify.py
│   │   ├── test_explain.py
│   │   └── test_api.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api.ts                # Strongly-typed API client matching backend models
│   │   ├── App.tsx               # Primary dashboard layout & view coordinator
│   │   ├── components/
│   │   │   ├── GraphCanvas.tsx   # React Flow interactive twin visualizer
│   │   │   ├── CustomNode.tsx    # Node types (device, identity, app, data) & badges
│   │   │   ├── Legend.tsx        # Edge status and node type legend
│   │   │   ├── IncidentBar.tsx   # Incident selector & flight simulator trigger
│   │   │   ├── ComparisonTable.tsx# 3 Defenses metrics, disruption & ranks
│   │   │   ├── DefenseDiffView.tsx# Before/After counterfactual graph diff viewer
│   │   │   ├── RationalePanel.tsx# Plain-language explanation & residual warning
│   │   │   ├── ApprovalModal.tsx # Human approval flow & post-verification display
│   │   │   ├── TwinEditor.tsx    # Manual Node/Edge CRUD drawer
│   │   │   └── DetailDrawer.tsx  # Node/Edge telemetry & evidence inspector
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── instruction.md
├── task.md
├── walkthrough.md
└── README.md
```

---

## 3. Data Model & Evidence Pipeline

### 3.1 Data Entities

- **Node**: Represents an entity within the enterprise environment.
  - `id`: Unique string (e.g., `web-01`).
  - `label`: Human-readable label (e.g., `Public Web Server`).
  - `type`: `device`, `identity`, `app`, or `data`.
  - `criticality`: Integer `1-5`.
  - `is_entry`: Boolean flag indicating if reachable directly from external networks.
  - `is_critical`: Boolean flag indicating crown-jewel assets (derived as `criticality >= 4` by default).

- **Edge**: Directed relationship connecting two nodes.
  - `src`, `dst`: Source and target node IDs.
  - `kind`: `access` (identities -> resources), `trust` (lateral networks), `dependency` (apps -> data).
  - `status`: `confirmed`, `needs_review`, or `unknown`.
  - `confidence`: Float `0.0 - 1.0`.
  - `last_seen`: ISO-8601 timestamp of most recent supporting telemetry.
  - `evidence_ids`: Array of supporting event IDs.
  - `business_weight`: Integer `1-5` reflecting the operational reliance on this link.

- **Event**: Synthetic log or telemetry record.
  - `id`: Unique ID (e.g., `ev-101`).
  - `timestamp`: Event creation time.
  - `asset_id`: Source asset logging the event.
  - `kind`: `login`, `connection`, `process`, or `alert`.
  - `detail`: Diagnostic log message.
  - `supports_edge`: List of edge keys (e.g., `["web-01->db-01"]`).

### 3.2 Evidence & Status Classification Rules

Edge status is computed deterministically in `app/evidence.py` using explicit rules:

1. **`confirmed`**:
   - At least 1 supporting event exists in `seed_events.json`.
   - The most recent event is fresh: `now - last_seen <= FRESHNESS_WINDOW_DAYS` (default 7 days).
   - No conflicting alerts or revocation events exist for this link.
2. **`needs_review`**:
   - Evidence is stale (`> 7 days old`), or
   - Conflicting events detected (e.g., failed authentication alerts or policy mismatch), or
   - Telemetry indicates partial/unverified access.
3. **`unknown`**:
   - Zero supporting telemetry events associated with the link.
   - Represents an unmonitored or assumed connection.

### 3.3 Confidence Scoring Algorithm
$$\text{confidence} = \min\left(1.0, 0.4 \times \log_2(1 + N_{\text{events}}) \times \exp\left(-\frac{\Delta t}{\tau}\right)\right)$$
- $N_{\text{events}}$: Number of supporting events.
- $\Delta t$: Days elapsed since `last_seen`.
- $\tau$: Half-life decay constant (14 days).
- If status is `unknown`, confidence is capped at `0.05`.

---

## 4. Simulation Engine: Counterfactuals & Defense Generation

### 4.1 Baseline Attack Path Discovery
1. Identify **Compromised Nodes**: Loaded from selected incident (e.g., `web-01`).
2. Identify **Critical Targets**: All nodes where `is_critical == True`.
3. Enumerate simple directed paths using `nx.all_simple_paths(G, source, target, cutoff=8)`.
4. Classify each path:
   - **Confirmed Path**: Every single edge along the path has status `confirmed`.
   - **Uncertain Path**: The path traverses one or more edges marked `needs_review` or `unknown`.

### 4.2 Candidate Defense Generation
The engine deterministically generates **exactly three** candidate defenses tailored to the incident:

1. **Defense 1: Host Isolation (`isolate_host`)**
   - Targets the compromised host or immediate downstream pivot.
   - Action: Drops all incoming and outgoing edges connected to that node.
   - Effort Score: Fixed at `2` (medium-low effort via EDR agent/host firewall).
2. **Defense 2: Credential / Identity Revocation (`revoke_identity`)**
   - Targets the active identity or service account traversed by attack paths.
   - Action: Drops all `access` edges originating from or pointing to that identity.
   - Effort Score: Fixed at `1` (low effort via IdP session kill / password reset).
3. **Defense 3: Network Segmentation / Link Block (`block_link`)**
   - Targets the specific network trust link traversed by the highest number of confirmed paths.
   - Action: Drops the identified critical edge(s).
   - Effort Score: Fixed at `3` (moderate effort requiring firewall or security group modification).

### 4.3 Counterfactual Graph Cloning & Immutability
To guarantee safety and transparency:
- The baseline digital twin graph $G$ is **never mutated** during simulation.
- For each candidate defense $i \in \{1, 2, 3\}$, the engine instantiates an isolated clone:
  $$G_i = G.\text{copy}()$$
- The intervention is applied exclusively to $G_i$, and attack paths are re-evaluated from scratch.

### 4.4 Disruption Scoring Formula
$$\text{Disruption} = \sum_{e \in E_{\text{removed}}} \text{business\_weight}(e) + \sum_{v \in V_{\text{orphaned}}} \text{criticality}(v)$$
Where:
- $E_{\text{removed}}$: Edges severed by the defense.
- $V_{\text{orphaned}}$: Nodes that lose all connectivity to core operational infrastructure as a result.
- The API explicitly returns `disruption_breakdown` with individual edge weights and orphan penalties for full auditability.

---

## 5. Deterministic Decision Engine & Ranking Rules

Candidate defenses are evaluated against strict mathematical criteria without subjective weights:

```
                   ┌──────────────────────────────────────┐
                   │    All Candidate Defenses (1, 2, 3)   │
                   └──────────────────┬───────────────────┘
                                      │
                                      ▼
               [ Zero Confirmed Attack Paths to Critical Assets? ]
                                      │
                   ┌──────────────────┴──────────────────┐
                   │ YES                                 │ NO
                   ▼                                     ▼
           QUALIFIES FOR RANKING                 DISQUALIFIED
                                                 (meets_target = false)
                   │
                   ▼
       SORT BY:
       1. Lowest Disruption (primary)
       2. Lowest Effort (secondary)
       3. Defense ID (stable tie-breaker)
                   │
                   ▼
       FLAG UNCERTAIN PATHS
       (Alert operator if uncertain paths remain)
```

1. **Gate Condition (`meets_target`)**:
   - A defense qualifies if and only if:
     $$\text{confirmed\_paths\_left} == 0$$
   - If a defense leaves even 1 confirmed attack path to any critical asset, it is disqualified with a documented reason.
2. **Ranking Order**:
   - Sort qualifying defenses ascending by `disruption`.
   - On ties, sort ascending by `effort`.
   - On remaining ties, sort lexicographically by `defense_id` for deterministic stability.
3. **Residual Uncertainty Flag**:
   - Even if `confirmed_paths_left == 0`, if `uncertain_paths_left > 0`, the defense is flagged with a prominent operational review warning.
4. **No-Qualifier Fallback**:
   - If no candidate defense eliminates all confirmed paths, the engine sets `meets_target = false` on all options and recommends immediate manual escalation and compensating controls. It never fabricates an unearned recommendation.

---

## 6. Plain-Language Explanations Engine

### 6.1 Structured Facts Payload
Before generating explanations, the backend extracts an immutable, structured facts object:
```json
{
  "incident_id": "inc-1",
  "incident_title": "Suspicious login on web-01",
  "baseline_confirmed_paths": 2,
  "baseline_uncertain_paths": 1,
  "critical_assets_at_risk": ["cust-db-01", "fin-ledger-01"],
  "recommended_defense": {
    "defense_id": "def-segment-link",
    "name": "Block Trust Link web-01 -> app-srv-02",
    "disruption": 3,
    "effort": 3,
    "confirmed_paths_left": 0,
    "uncertain_paths_left": 1
  },
  "candidate_defenses": [...],
  "flagged_uncertain_edges": [
    {
      "edge": "jump-host->fin-ledger-01",
      "status": "needs_review",
      "reason": "telemetry stale (>12 days)"
    }
  ],
  "evidence_cited": ["ev-101", "ev-104"]
}
```

### 6.2 Deterministic Template (Default)
Generates structured narrative using deterministic Python string interpolation:
- Identifies the top-ranked defense and why it succeeded (0 confirmed paths, lowest disruption).
- Explains why competing options were ranked lower or disqualified.
- Highlights flagged uncertain edges and explicitly issues the warning:
  > *"Missing visibility does not prove safety. Link jump-host -> fin-ledger-01 has stale telemetry and must be manually inspected."*

### 6.3 Gemini 2.5 LLM Integration & Anti-Hallucination Guardrail
- When `GEMINI_API_KEY` is provided:
  - The structured facts JSON is transmitted to the Gemini API (`google-genai` SDK).
  - System prompt restricts Gemini:
    - *Must only cite facts and numbers present in the facts JSON.*
    - *Must never invent defenses, change disruption numbers, or alter ranking.*
    - *Must cite evidence IDs.*
    - *Must include the missing visibility safety warning.*
  - **Output Validation**:
    - The backend inspects the generated text. If any defense ID, node ID, or number not present in the facts payload is detected, the response is discarded, and the system seamlessly falls back to the deterministic template.

---

## 7. Human Decision & Post-Approval Verification

1. **Operator Choice**:
   - The security analyst inspects the comparison table and rationale.
   - The analyst can select **any** option (including higher-disruption or non-recommended ones if organizational context dictates).
2. **Approval Record**:
   - The analyst submits an `ApprovalRequest` containing `run_id`, `defense_id`, and `approver_note`.
   - The action is timestamped and persisted to SQLite.
3. **Simulated Twin Mutation**:
   - The chosen defense is applied to the digital twin stored in SQLite.
4. **Automated Verification**:
   - The verification engine (`app/verify.py`) re-runs path traversal on the newly updated twin.
   - **Verification Passed**: If confirmed paths to critical assets equal `0`.
   - **Verification Failed**: If any confirmed attack path persists.
   - Any residual uncertain paths are logged and displayed on the verification card.

---

## 8. Synthetic Seed Dataset & Trade-off Demonstration

The included `seed_org.json` models an 11-node realistic hybrid corporate infrastructure:

```
[Internet]
    │
    ▼
[web-01] (Compromised in inc-1)
    │
    ├── (confirmed, wt: 3) ──────────────► [app-srv-02]
    │                                           │
    │                                (confirmed, wt: 4)
    │                                           │
    │                                           ▼
    │                                     [cust-db-01] ★ CRITICAL
    │
    └── (needs_review / stale, wt: 2) ───► [jump-host]
                                                │
                                         (unknown, wt: 1)
                                                │
                                                ▼
                                         [fin-ledger-01] ★ CRITICAL
```

### The Trade-off Demonstration:
- **Defense A (Revoke App Credential)**:
  - Disruption: `2`, Effort: `1`.
  - Cuts confirmed path to `cust-db-01`.
  - **Trade-off**: Leaves an uncertain path through `jump-host` to `fin-ledger-01` open!
- **Defense B (Isolate web-01)**:
  - Disruption: `6`, Effort: `2`.
  - Severely cuts all paths, eliminating both confirmed and uncertain paths.
  - **Trade-off**: High disruption; knocks offline benign corporate customer services.
- **Defense C (Segment Trust Link web-01 -> app-srv-02)**:
  - Disruption: `3`, Effort: `3`.
  - Minimally invasive for confirmed path; requires operator to decide how to handle the stale `jump-host` connection.

This scenario vividly exhibits the non-negotiable principle: **Missing visibility does not prove safety.**

---

## 9. API Specification

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/twin` | Retrieve current twin nodes and edges with confidence, freshness, and status |
| `PUT` | `/api/twin` | Replace twin graph and trigger evidence pipeline recalculation |
| `POST` | `/api/twin/node` | Add or update a node in the digital twin |
| `DELETE` | `/api/twin/node/{id}` | Remove a node and its incident edges |
| `POST` | `/api/twin/edge` | Add or update an edge in the digital twin |
| `DELETE` | `/api/twin/edge` | Remove an edge |
| `GET` | `/api/incidents` | List available simulated incidents (`inc-1`, `inc-2`) |
| `POST` | `/api/simulate` | Execute attack path traversal, 3 counterfactuals, and ranking |
| `POST` | `/api/explain` | Generate plain-language rationale (templated or Gemini) |
| `POST` | `/api/approve` | Human approval: updates simulated twin and creates audit log |
| `POST` | `/api/verify` | Post-approval verification: validates zero confirmed paths remain |
| `GET` | `/api/runs/{id}` | Audit retrieval of historical simulation runs and approvals |

---

## 10. Frontend User Journey

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🛡️ CYBERSECURITY FLIGHT SIMULATOR                 [Twin Editor] [Docs] [Dark]│
├─────────────────────────────────────────────────────────────────────────────┤
│ Incident Selector: [ Inc-1: Suspicious login on web-01 ▼ ]  [ ▶ Run Simulation]│
├──────────────────────────────────────┬──────────────────────────────────────┤
│ 🗺️ DIGITAL TWIN (React Flow Canvas)  │ 📊 CANDIDATE DEFENSES COMPARISON     │
│                                      │                                      │
│ • Custom Nodes: Devices, Identities, │ #1 [Block Link web-01->app-srv-02]   │
│   Apps, Data Stores                  │    Paths: 0 confirmed | 1 uncertain  │
│ • Edges:                             │    Disruption: 3 | Effort: 3         │
│   - Solid Green: Confirmed           │    Status: ✅ Meets Target (Rank 1)   │
│   - Dashed Amber: Needs Review       │                                      │
│   - Dotted Grey: Unknown             │ #2 [Revoke Service Identity]         │
│ • Attack Paths highlighted in Red    │    Paths: 0 confirmed | 1 uncertain  │
│ • Toggle: [Baseline] vs [Post-Def]   │    Disruption: 4 | Effort: 1 (Rank 2)│
│                                      │                                      │
│                                      │ #3 [Isolate Host web-01]             │
│                                      │    Paths: 0 confirmed | 0 uncertain  │
│                                      │    Disruption: 8 | Effort: 2 (Rank 3)│
├──────────────────────────────────────┼──────────────────────────────────────┤
│ 🔍 EVIDENCE & NODE DETAILS           │ 📝 PLAIN-LANGUAGE EXPLANATION        │
│ Node: web-01 (Criticality 3)         │ "Recommendation: Block trust link    │
│ Supporting events: ev-101, ev-103    │ between web-01 and app-srv-02..."    │
│ Confidence: 0.94 | Freshness: 1d ago │ ⚠️ Residual Uncertainty Alert:       │
│ Status: Confirmed Link               │ Link jump-host -> fin-ledger-01 is   │
│                                      │ unverified. Safety cannot be assumed.│
│                                      │ [ Human Approval & Simulate Action ] │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 11. Verification & Testing Strategy

Pytest unit and integration tests validate every phase of the deterministic engine:
1. `test_evidence.py`: Validates `confirmed`, `needs_review`, and `unknown` status transitions, confidence decay, and edge evidence mapping.
2. `test_attack_paths.py`: Checks path traversal with cutoff limits, target reachability, and verified vs uncertain path labeling.
3. `test_counterfactuals.py`: Asserts that baseline graph nodes and edges are strictly immutable when running counterfactuals.
4. `test_disruption.py`: Tests additive business disruption and orphan node penalties.
5. `test_ranking.py`: Tests disqualification of defenses that fail to break confirmed paths, tie-breaking by disruption then effort, and empty-qualifier reporting.
6. `test_verify.py`: Confirms post-approval verification logic, pass/fail thresholds, and pre-approval snapshot immutability.
7. `test_explain.py`: Tests the deterministic template output, facts serialization, and fallback behavior when Gemini API is unconfigured or returns invalid data.
8. `test_api.py`: Tests all FastAPI endpoints end-to-end using `httpx`.

