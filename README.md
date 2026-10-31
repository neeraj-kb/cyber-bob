# Cybersecurity Flight Simulator

A high-assurance web application that models an organization's digital twin as a directed graph, simulates cyber incidents to identify critical asset exposure, generates candidate defense interventions on cloned counterfactual graphs, ranks defenses using deterministic transparent rules, provides plain-language explanations (via deterministic template or optional Gemini), and requires explicit human approval before applying simulated remediation to the twin.

---

## 1. Core Principles

1. **Deterministic Core**: Graph traversal, attack path classification, disruption metrics, and defense rankings are 100% computed using explicit Python algorithms. No hidden weights or opaque heuristics.
2. **AI Only Explains**: An optional LLM (Gemini 2.5) explains computed facts in plain language. It never decides, ranks, scores, or mutates data. The app works fully offline with no LLM key using built-in deterministic templates.
3. **Human Decides**: Remediation is never automated. Every action requires explicit operator approval and is permanently audited. Execution updates the digital twin only (safe simulation).
4. **Synthetic Data Only**: Operates strictly on authorized synthetic enterprise digital twins.
5. **Missing Visibility Does Not Prove Safety**: Links with stale, conflicting, or missing evidence are surfaced as **uncertain**, never silently assumed safe.

---

## 2. Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, `@xyflow/react` (React Flow), Lucide Icons
- **Backend**: Python 3.14+, FastAPI, Pydantic v2, NetworkX, Uvicorn, SQLite
- **AI Explanation (Optional)**: Google Gemini API (`google-genai` SDK) with anti-hallucination fact boundary validation; deterministic template fallback when API key is unset.

---

## 3. Quickstart & How to Run

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run FastAPI backend server (listening on http://127.0.0.1:8000)
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite development server (listening on http://localhost:5173)
npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

## 4. Deploying to Vercel

The repository is pre-configured with full-stack monorepo settings for Vercel:
- **Frontend**: Built automatically from `frontend/` into `frontend/dist`.
- **Backend API**: Exposed as a Python Serverless Function via [`api/index.py`](file:///c:/Users/Neeraj/OneDrive/Desktop/Kodikon_6.0/api/index.py) routing all `/api/*` traffic to FastAPI.
- **Serverless SQLite**: Uses system `/tmp` on serverless execution with automatic seed loading.

### Option A: Deploy via GitHub (Recommended)
1. Push your repository to GitHub:
   ```bash
   git add .
   git commit -m "Configure full-stack deployment for Vercel"
   git push origin main
   ```
2. Go to [vercel.com](https://vercel.com) $\rightarrow$ **Add New Project** $\rightarrow$ Import your GitHub repository.
3. Keep default settings (Vercel automatically detects [`vercel.json`](file:///c:/Users/Neeraj/OneDrive/Desktop/Kodikon_6.0/vercel.json)).
4. (Optional) In Project Settings $\rightarrow$ Environment Variables, set `GEMINI_API_KEY` if you wish to enable Gemini 2.5 explanations.
5. Click **Deploy**.

### Option B: Deploy via Vercel CLI
```bash
npm install -g vercel
vercel
```

---

## 5. Running the Automated Test Suite

From the root repository directory:
```bash
pytest -v
```
All 24 unit and integration tests validate:
- Edge status and confidence scoring formulas (`test_evidence.py`)
- Attack path discovery and confirmed vs uncertain path classification (`test_attack_paths.py`)
- Baseline graph immutability during counterfactual branching (`test_counterfactuals.py`)
- Business disruption and orphaned node penalties (`test_disruption.py`)
- Deterministic ranking, qualification gates, and tie-breaking (`test_ranking.py`)
- Verification pass/fail criteria and residual uncertainty reporting (`test_verify.py`)
- Fact-bounded explanation templates, Gemini prompt generation, and anti-hallucination validation (`test_explain.py`)
- All FastAPI REST endpoints (`test_api.py`)

---

## 5. Seed Dataset & The Trade-off Demonstration

The seed dataset (`backend/data/seed_org.json`) models a 10-node hybrid enterprise infrastructure:
- **Perimeter**: `web-01` (entry device), `vpn-gw` (entry device)
- **Identities**: `admin-user` (DevOps admin), `svc-deployer` (CI/CD service account)
- **Apps**: `app-srv-01` (Customer Portal Backend), `auth-srv` (SSO Provider)
- **Infrastructure**: `jump-host` (Internal bastion jump host)
- **Crown Jewels**: `cust-db-01` (criticality: 5), `fin-ledger-01` (criticality: 5), `backup-vault` (criticality: 4)

### The Trade-off Demonstration in Incident `inc-1` (`web-01` compromised):
- **Candidate 1: Block Link `web-01 -> app-srv-01`** (Segment trust link):
  - Incurs low business disruption (`4`) and moderate effort (`3`).
  - Successfully eliminates the confirmed path to `cust-db-01`.
  - **Trade-off**: Leaves an uncertain path open through `jump-host` (stale telemetry) to `fin-ledger-01`!
- **Candidate 2: Isolate Host `web-01`**:
  - Drops all edges incident to `web-01`.
  - Incurs higher business disruption (`8`), effort (`2`).
  - Completely eliminates **both** confirmed and uncertain paths.
  - **Trade-off**: High operational disruption, but provides absolute containment.
- **Candidate 3: Revoke Identity Credentials `svc-deployer`**:
  - Incurs disruption (`3`), effort (`1`).
  - Fails to break the confirmed path to `cust-db-01` (disqualified from ranking with documented reason).

This clearly demonstrates the non-negotiable principle: **Missing visibility does not prove safety.**

---

## 6. Documented Assumptions

1. **Evidence Decay**: Evaluated relative to an anchor timestamp or current UTC. Half-life decay constant is configured in `app/config.py` as $\tau = 14$ days, with a freshness cutoff window of 7 days.
2. **Critical Assets**: Assets with `criticality >= 4` are designated as crown-jewel critical targets that must not be reachable by attackers.
3. **Disruption Calculation**: Additive business disruption comprises the sum of business weights ($1-5$) of all severed edges plus the criticality ratings ($1-5$) of any non-entry nodes whose in-degree becomes 0 (upstream traffic cut off).
4. **Offline Capability**: When `GEMINI_API_KEY` is not present in the environment, the system seamlessly uses deterministic string templating with zero loss of functionality.

---

## 7. Known Gaps & Out of Scope

As specified in `instruction.md`:
- Live data collectors or agent daemons on real operating systems are out of scope.
- Automatic or unsupervised remediation without human approval is explicitly prohibited.
- Competing benign-vs-suspicious hypothesis engines are out of scope.
- Multi-tenant enterprise tenant isolation is out of scope.

