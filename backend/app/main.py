"""FastAPI main application with CORS, route handlers, and Pydantic schemas."""
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    TwinGraph,
    Node,
    Edge,
    Incident,
    SimulationRequest,
    SimulationRun,
    ExplainRequest,
    ExplanationResponse,
    ApprovalRequest,
    VerificationResult,
)
from app.db import (
    init_db,
    load_seed_data,
    get_twin,
    save_twin,
    save_node,
    delete_node,
    save_edge,
    delete_edge,
    get_incidents,
    get_incident,
    get_events,
    get_run,
)
from app.evidence import process_all_evidence
from app.simulate import run_simulation
from app.explain import explain_run
from app.verify import verify_approval


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    init_db()
    load_seed_data()
    yield


app = FastAPI(
    title="Cybersecurity Flight Simulator API",
    description="Deterministic digital-twin simulation and AI explanation backend.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> Dict[str, str]:
    return {"status": "healthy", "service": "Cybersecurity Flight Simulator"}


@app.get("/api/twin", response_model=TwinGraph)
def get_digital_twin() -> TwinGraph:
    """Retrieve current digital-twin graph with node metadata and edge evidence statuses."""
    return get_twin()


@app.put("/api/twin", response_model=TwinGraph)
def replace_digital_twin(twin_data: TwinGraph) -> TwinGraph:
    """Replace synthetic organization nodes & edges, and re-run evidence pipeline."""
    events = get_events()
    updated_twin = process_all_evidence(twin_data, events)
    save_twin(updated_twin)
    return updated_twin


@app.post("/api/twin/reset", response_model=TwinGraph)
def reset_digital_twin() -> TwinGraph:
    """Reset the digital twin back to baseline seed organization data."""
    load_seed_data(force=True)
    return get_twin()


@app.post("/api/twin/node", response_model=Node)
def add_or_update_node(node: Node) -> Node:
    """Create or update a single node in the digital twin."""
    save_node(node)
    return node


@app.delete("/api/twin/node/{node_id}")
def remove_node(node_id: str) -> Dict[str, str]:
    """Delete a node and its incident edges from the digital twin."""
    delete_node(node_id)
    return {"status": "deleted", "node_id": node_id}


@app.post("/api/twin/edge", response_model=Edge)
def add_or_update_edge(edge: Edge) -> Edge:
    """Create or update a single edge and recalculate its evidence."""
    events = get_events()
    current_twin = get_twin()
    # Check if edge already exists
    filtered_edges = [e for e in current_twin.edges if not (e.src == edge.src and e.dst == edge.dst)]
    filtered_edges.append(edge)
    updated_twin = process_all_evidence(TwinGraph(nodes=current_twin.nodes, edges=filtered_edges), events)
    save_twin(updated_twin)
    # Find and return the updated edge
    for e in updated_twin.edges:
        if e.src == edge.src and e.dst == edge.dst:
            return e
    return edge


@app.delete("/api/twin/edge")
def remove_edge(src: str, dst: str) -> Dict[str, str]:
    """Delete a single edge from the digital twin."""
    delete_edge(src, dst)
    return {"status": "deleted", "edge": f"{src}->{dst}"}


@app.get("/api/incidents", response_model=List[Incident])
def list_incidents() -> List[Incident]:
    """List available simulated security incidents."""
    return get_incidents()


@app.post("/api/simulate", response_model=SimulationRun)
def simulate_flight(request: SimulationRequest) -> SimulationRun:
    """
    Run baseline attack path discovery, clone counterfactual graphs,
    simulate three candidate defenses, and rank them deterministically.
    """
    incident = get_incident(request.incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{request.incident_id}' not found.",
        )
    return run_simulation(request.incident_id)


@app.post("/api/explain", response_model=ExplanationResponse)
def explain_simulation(request: ExplainRequest) -> ExplanationResponse:
    """
    Generate plain-language rationale for the given run.
    Uses Gemini API if configured; falls back gracefully to deterministic templates.
    """
    try:
        return explain_run(request.run_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post("/api/approve", response_model=Dict[str, Any])
def approve_defense(request: ApprovalRequest) -> Dict[str, Any]:
    """
    Record human approval, execute simulated intervention on the digital twin,
    and return the updated graph alongside the approval record.
    """
    try:
        verification = verify_approval(request)
        updated_twin = get_twin()
        return {
            "status": "approved",
            "run_id": request.run_id,
            "defense_id": request.defense_id,
            "verification": verification.model_dump(),
            "updated_twin": updated_twin.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post("/api/verify", response_model=VerificationResult)
def verify_simulation(request: ExplainRequest) -> VerificationResult:
    """
    Re-run path traversal on the updated twin for this run and verify pass/fail criteria.
    """
    run_dict = get_run(request.run_id)
    if not run_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{request.run_id}' not found")
    
    approved_defense_id = run_dict.get("approved_defense_id")
    if not approved_defense_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run has not been approved yet. Call /api/approve first."
        )

    # Re-run verification
    approval_req = ApprovalRequest(
        run_id=request.run_id,
        defense_id=approved_defense_id,
        approver_note=run_dict.get("approver_note", ""),
    )
    return verify_approval(approval_req)


@app.get("/api/runs/{run_id}")
def get_run_audit(run_id: str) -> Dict[str, Any]:
    """Retrieve full audit record for a simulation run including baseline, rankings, and approval."""
    run_dict = get_run(run_id)
    if not run_dict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found")
    return run_dict

