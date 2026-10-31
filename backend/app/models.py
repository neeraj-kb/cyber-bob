"""Pydantic models and schemas for Cybersecurity Flight Simulator."""
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, model_validator
from app.config import CRITICALITY_THRESHOLD

NodeType = Literal["device", "identity", "app", "data"]
EdgeKind = Literal["access", "trust", "dependency"]
EdgeStatus = Literal["confirmed", "needs_review", "unknown"]
EventKind = Literal["login", "connection", "process", "alert"]
DefenseType = Literal["isolate_host", "revoke_identity", "block_link"]
PathClassification = Literal["confirmed", "uncertain"]


class Node(BaseModel):
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Human-readable node label")
    type: NodeType = Field(..., description="Entity archetype")
    criticality: int = Field(default=1, ge=1, le=5, description="Business criticality (1-5)")
    is_entry: bool = Field(default=False, description="Whether node is externally exposed")
    is_critical: bool = Field(default=False, description="Crown jewel asset that must not be reached")

    @model_validator(mode="before")
    @classmethod
    def set_is_critical_default(cls, data: Any) -> Any:
        if isinstance(data, dict):
            crit = data.get("criticality", 1)
            if "is_critical" not in data or data["is_critical"] is None:
                data["is_critical"] = crit >= CRITICALITY_THRESHOLD
            elif crit >= CRITICALITY_THRESHOLD and not data.get("is_critical"):
                # Ensure critical assets threshold is respected unless explicitly overridden
                pass
        return data


class Edge(BaseModel):
    src: str = Field(..., description="Source node ID")
    dst: str = Field(..., description="Destination node ID")
    kind: EdgeKind = Field(..., description="Relationship kind")
    status: EdgeStatus = Field(default="unknown", description="Evidence status")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    last_seen: Optional[str] = Field(default=None, description="ISO-8601 timestamp of last telemetry")
    evidence_ids: List[str] = Field(default_factory=list, description="IDs of supporting events")
    business_weight: int = Field(default=1, ge=1, le=5, description="Business dependency weight (1-5)")

    @property
    def key(self) -> str:
        return f"{self.src}->{self.dst}"


class Event(BaseModel):
    id: str = Field(..., description="Unique event identifier")
    timestamp: str = Field(..., description="ISO-8601 event timestamp")
    asset_id: str = Field(..., description="Associated asset ID")
    kind: EventKind = Field(..., description="Event telemetry kind")
    detail: str = Field(..., description="Diagnostic event payload")
    supports_edge: List[str] = Field(default_factory=list, description="Edges supported by this event (src->dst)")


class Incident(BaseModel):
    id: str = Field(..., description="Unique incident identifier")
    title: str = Field(..., description="Incident title or alert name")
    compromised_nodes: List[str] = Field(..., description="Initially compromised nodes")


class AttackPath(BaseModel):
    nodes: List[str] = Field(..., description="Sequence of node IDs in traversal order")
    edges: List[str] = Field(..., description="Sequence of edge keys (src->dst)")
    classification: PathClassification = Field(..., description="Path certainty")
    target: str = Field(..., description="Critical asset reached")
    uncertain_edges: List[str] = Field(default_factory=list, description="Uncertain or unverified edges traversed")


class DisruptionBreakdown(BaseModel):
    removed_edge_weights: Dict[str, int] = Field(default_factory=dict, description="Weight of each severed edge")
    orphaned_nodes_penalty: Dict[str, int] = Field(default_factory=dict, description="Criticality penalty for cut-off nodes")
    total_disruption: int = Field(default=0, description="Sum of severed weights and cut-off penalties")


class DefenseResult(BaseModel):
    defense_id: str = Field(..., description="Unique candidate defense identifier")
    name: str = Field(..., description="Human-readable defense action name")
    type: DefenseType = Field(..., description="Intervention archetype")
    target_id: str = Field(..., description="Target node ID or edge key")
    removed_nodes: List[str] = Field(default_factory=list, description="Nodes removed or completely isolated")
    removed_edges: List[str] = Field(default_factory=list, description="Edges severed by intervention")
    confirmed_paths_left: int = Field(..., description="Count of remaining confirmed attack paths")
    uncertain_paths_left: int = Field(..., description="Count of remaining uncertain attack paths")
    critical_assets_reachable: List[str] = Field(default_factory=list, description="Critical asset IDs still reachable")
    disruption: int = Field(..., description="Total business disruption score")
    disruption_breakdown: DisruptionBreakdown = Field(..., description="Detailed breakdown of disruption")
    effort: int = Field(..., ge=1, le=5, description="Fixed operational effort score")
    meets_target: bool = Field(..., description="Whether defense leaves zero confirmed paths to critical assets")
    rank: Optional[int] = Field(default=None, description="Objective rank (1 = best recommendation)")
    ranking_reason: str = Field(default="", description="Deterministic explanation of rank or disqualification")


class TwinGraph(BaseModel):
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)


class SimulationRequest(BaseModel):
    incident_id: str = Field(..., description="Simulated incident identifier")


class SimulationRun(BaseModel):
    run_id: str = Field(..., description="Unique run identifier")
    incident_id: str = Field(..., description="Incident identifier")
    timestamp: str = Field(..., description="Simulation timestamp")
    baseline_paths: List[AttackPath] = Field(default_factory=list)
    baseline_critical_assets_reachable: List[str] = Field(default_factory=list)
    candidate_defenses: List[DefenseResult] = Field(default_factory=list)
    recommended_defense_id: Optional[str] = None
    approved_defense_id: Optional[str] = None
    approver_note: Optional[str] = None


class ExplainRequest(BaseModel):
    run_id: str = Field(..., description="Simulation run ID")


class ExplanationResponse(BaseModel):
    run_id: str
    recommended_defense_id: Optional[str]
    mode: Literal["template", "gemini"]
    summary: str
    rationale: str
    uncertainty_warning: str
    evidence_cited: List[str]
    facts: Dict[str, Any]


class ApprovalRequest(BaseModel):
    run_id: str = Field(..., description="Simulation run identifier")
    defense_id: str = Field(..., description="Chosen candidate defense ID")
    approver_note: str = Field(default="", description="Operator approval justification note")


class VerificationResult(BaseModel):
    run_id: str
    defense_id: str
    passed: bool
    confirmed_paths_left: int
    uncertain_paths_left: int
    remaining_critical_assets: List[str]
    residual_uncertain_paths: List[AttackPath]
    message: str

