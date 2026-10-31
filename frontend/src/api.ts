export type NodeType = 'device' | 'identity' | 'app' | 'data';
export type EdgeKind = 'access' | 'trust' | 'dependency';
export type EdgeStatus = 'confirmed' | 'needs_review' | 'unknown';
export type PathClassification = 'confirmed' | 'uncertain';
export type DefenseType = 'isolate_host' | 'revoke_identity' | 'block_link';

export interface Node {
  id: string;
  label: string;
  type: NodeType;
  criticality: number;
  is_entry: boolean;
  is_critical: boolean;
}

export interface Edge {
  src: string;
  dst: string;
  kind: EdgeKind;
  status: EdgeStatus;
  confidence: number;
  last_seen: string | null;
  evidence_ids: string[];
  business_weight: number;
}

export interface Incident {
  id: string;
  title: string;
  compromised_nodes: string[];
}

export interface AttackPath {
  nodes: string[];
  edges: string[];
  classification: PathClassification;
  target: string;
  uncertain_edges: string[];
}

export interface DisruptionBreakdown {
  removed_edge_weights: Record<string, number>;
  orphaned_nodes_penalty: Record<string, number>;
  total_disruption: number;
}

export interface DefenseResult {
  defense_id: string;
  name: string;
  type: DefenseType;
  target_id: string;
  removed_nodes: string[];
  removed_edges: string[];
  confirmed_paths_left: number;
  uncertain_paths_left: number;
  critical_assets_reachable: string[];
  disruption: number;
  disruption_breakdown: DisruptionBreakdown;
  effort: number;
  meets_target: boolean;
  rank: number | null;
  ranking_reason: string;
}

export interface TwinGraph {
  nodes: Node[];
  edges: Edge[];
}

export interface SimulationRun {
  run_id: string;
  incident_id: string;
  timestamp: string;
  baseline_paths: AttackPath[];
  baseline_critical_assets_reachable: string[];
  candidate_defenses: DefenseResult[];
  recommended_defense_id: string | null;
  approved_defense_id?: string | null;
  approver_note?: string | null;
}

export interface ExplanationResponse {
  run_id: string;
  recommended_defense_id: string | null;
  mode: 'template' | 'gemini';
  summary: string;
  rationale: string;
  uncertainty_warning: string;
  evidence_cited: string[];
  facts: Record<string, any>;
}

export interface VerificationResult {
  run_id: string;
  defense_id: string;
  passed: boolean;
  confirmed_paths_left: number;
  uncertain_paths_left: number;
  remaining_critical_assets: string[];
  residual_uncertain_paths: AttackPath[];
  message: string;
}

const API_BASE = '/api';

export const api = {
  async getTwin(): Promise<TwinGraph> {
    const res = await fetch(`${API_BASE}/twin`);
    if (!res.ok) throw new Error('Failed to fetch digital twin');
    return res.json();
  },

  async replaceTwin(twin: TwinGraph): Promise<TwinGraph> {
    const res = await fetch(`${API_BASE}/twin`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(twin),
    });
    if (!res.ok) throw new Error('Failed to update twin');
    return res.json();
  },

  async resetTwin(): Promise<TwinGraph> {
    const res = await fetch(`${API_BASE}/twin/reset`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reset twin');
    return res.json();
  },

  async addNode(node: Node): Promise<Node> {
    const res = await fetch(`${API_BASE}/twin/node`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(node),
    });
    if (!res.ok) throw new Error('Failed to add node');
    return res.json();
  },

  async deleteNode(nodeId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/twin/node/${nodeId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete node');
  },

  async addEdge(edge: Edge): Promise<Edge> {
    const res = await fetch(`${API_BASE}/twin/edge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(edge),
    });
    if (!res.ok) throw new Error('Failed to add edge');
    return res.json();
  },

  async deleteEdge(src: string, dst: string): Promise<void> {
    const res = await fetch(`${API_BASE}/twin/edge?src=${src}&dst=${dst}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete edge');
  },

  async getIncidents(): Promise<Incident[]> {
    const res = await fetch(`${API_BASE}/incidents`);
    if (!res.ok) throw new Error('Failed to list incidents');
    return res.json();
  },

  async runSimulation(incidentId: string): Promise<SimulationRun> {
    const res = await fetch(`${API_BASE}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ incident_id: incidentId }),
    });
    if (!res.ok) throw new Error('Failed to run simulation');
    return res.json();
  },

  async getExplanation(runId: string): Promise<ExplanationResponse> {
    const res = await fetch(`${API_BASE}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ run_id: runId }),
    });
    if (!res.ok) throw new Error('Failed to generate explanation');
    return res.json();
  },

  async approveDefense(runId: string, defenseId: string, note: string): Promise<{
    status: string;
    run_id: string;
    defense_id: string;
    verification: VerificationResult;
    updated_twin: TwinGraph;
  }> {
    const res = await fetch(`${API_BASE}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        run_id: runId,
        defense_id: defenseId,
        approver_note: note,
      }),
    });
    if (!res.ok) throw new Error('Failed to approve defense');
    return res.json();
  },

  async verifyRun(runId: string): Promise<VerificationResult> {
    const res = await fetch(`${API_BASE}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ run_id: runId }),
    });
    if (!res.ok) throw new Error('Failed to verify run');
    return res.json();
  },

  async getRunAudit(runId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/runs/${runId}`);
    if (!res.ok) throw new Error('Failed to fetch run audit');
    return res.json();
  },
};

