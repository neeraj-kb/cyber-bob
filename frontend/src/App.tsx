import React, { useState, useEffect } from 'react';
import {
  api,
  TwinGraph,
  Incident,
  SimulationRun,
  ExplanationResponse,
  DefenseResult,
  VerificationResult,
  Node,
  Edge,
} from './api';
import { GraphCanvas } from './components/GraphCanvas';
import { IncidentBar } from './components/IncidentBar';
import { ComparisonTable } from './components/ComparisonTable';
import { RationalePanel } from './components/RationalePanel';
import { ApprovalModal } from './components/ApprovalModal';
import { TwinEditor } from './components/TwinEditor';
import { DetailDrawer } from './components/DetailDrawer';
import { Legend } from './components/Legend';
import { Plane, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [twin, setTwin] = useState<TwinGraph>({ nodes: [], edges: [] });
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('inc-1');
  const [currentRun, setCurrentRun] = useState<SimulationRun | null>(null);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [selectedPreviewDefenseId, setSelectedPreviewDefenseId] = useState<string | null>(null);

  // Modals & Drawers
  const [isApprovalOpen, setIsApprovalOpen] = useState(false);
  const [approvalTargetDefense, setApprovalTargetDefense] = useState<DefenseResult | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [isTwinEditorOpen, setIsTwinEditorOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null);

  // Loading states
  const [isLoading, setIsLoading] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Initial Data Fetch
  useEffect(() => {
    async function initData() {
      try {
        const [twinData, incidentsData] = await Promise.all([
          api.getTwin(),
          api.getIncidents(),
        ]);
        setTwin(twinData);
        setIncidents(incidentsData);
        if (incidentsData.length > 0) {
          setSelectedIncidentId(incidentsData[0].id);
        }
      } catch (err: any) {
        setErrorMsg('Failed to initialize digital twin from backend.');
      }
    }
    initData();
  }, []);

  // Run Simulation Handler
  const handleRunSimulation = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    setVerificationResult(null);
    setSelectedPreviewDefenseId(null);
    try {
      const run = await api.runSimulation(selectedIncidentId);
      setCurrentRun(run);

      // Auto-trigger explanation
      setIsExplaining(true);
      try {
        const exp = await api.getExplanation(run.run_id);
        setExplanation(exp);
      } catch (e) {
        console.warn('Explanation generation failed', e);
      } finally {
        setIsExplaining(false);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Simulation execution failed');
    } finally {
      setIsLoading(false);
    }
  };

  // Reset Twin Handler
  const handleResetTwin = async () => {
    setIsLoading(true);
    try {
      const resetTwin = await api.resetTwin();
      setTwin(resetTwin);
      setCurrentRun(null);
      setExplanation(null);
      setSelectedPreviewDefenseId(null);
      setVerificationResult(null);
    } catch (err: any) {
      setErrorMsg('Failed to reset digital twin.');
    } finally {
      setIsLoading(false);
    }
  };

  // Twin Editor Handlers
  const handleAddNode = async (node: Node) => {
    await api.addNode(node);
    const updated = await api.getTwin();
    setTwin(updated);
  };

  const handleDeleteNode = async (nodeId: string) => {
    await api.deleteNode(nodeId);
    const updated = await api.getTwin();
    setTwin(updated);
  };

  const handleAddEdge = async (edge: Edge) => {
    await api.addEdge(edge);
    const updated = await api.getTwin();
    setTwin(updated);
  };

  const handleDeleteEdge = async (src: string, dst: string) => {
    await api.deleteEdge(src, dst);
    const updated = await api.getTwin();
    setTwin(updated);
  };

  // Approval Handlers
  const handleOpenApproval = (defense: DefenseResult) => {
    setApprovalTargetDefense(defense);
    setIsApprovalOpen(true);
  };

  const handleConfirmApproval = async (defenseId: string, note: string): Promise<VerificationResult> => {
    if (!currentRun) throw new Error('No active simulation run to approve.');
    const res = await api.approveDefense(currentRun.run_id, defenseId, note);
    setVerificationResult(res.verification);
    setTwin(res.updated_twin);
    // Refresh current run audit
    const updatedRun = await api.getRunAudit(currentRun.run_id);
    setCurrentRun(updatedRun);
    return res.verification;
  };

  const currentIncident = incidents.find((i) => i.id === selectedIncidentId);
  const compromisedNodeIds = currentIncident?.compromised_nodes || [];

  const previewDefense = currentRun?.candidate_defenses.find(
    (d) => d.defense_id === selectedPreviewDefenseId
  ) || null;

  const baselineConfirmedCount = currentRun
    ? currentRun.baseline_paths.filter((p) => p.classification === 'confirmed').length
    : undefined;
  const baselineUncertainCount = currentRun
    ? currentRun.baseline_paths.filter((p) => p.classification === 'uncertain').length
    : undefined;

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#090d16] text-slate-100 font-sans">
      {/* Top Header */}
      <header className="h-13 bg-slate-950 border-b border-slate-800 px-4 flex items-center justify-between z-30 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-blue-600/20 border border-blue-500/40 text-blue-400">
            <Plane className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-2">
              <span>Cybersecurity Flight Simulator</span>
              <span className="text-[10px] bg-blue-950 text-blue-400 border border-blue-800 px-1.5 py-0.2 rounded font-mono">
                v1.0 • DETERMINISTIC CORE
              </span>
            </h1>
            <p className="text-[10px] text-slate-400">
              Deterministic Traversal • Counterfactual Branching • AI Explains • Human Decides
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {verificationResult?.passed && (
            <span className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-800 px-2.5 py-1 rounded-full font-semibold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              Verified Clean Twin
            </span>
          )}
        </div>
      </header>

      {/* Incident Control Bar */}
      <IncidentBar
        incidents={incidents}
        selectedIncidentId={selectedIncidentId}
        onSelectIncident={setSelectedIncidentId}
        onRunSimulation={handleRunSimulation}
        onResetTwin={handleResetTwin}
        onToggleTwinEditor={() => setIsTwinEditorOpen(true)}
        isLoading={isLoading}
        baselineConfirmedCount={baselineConfirmedCount}
        baselineUncertainCount={baselineUncertainCount}
      />

      {/* Error alert if any */}
      {errorMsg && (
        <div className="bg-rose-950/80 border-b border-rose-800 px-4 py-1.5 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Workspace Split View */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Side: React Flow Digital Twin Canvas (60%) */}
        <div className="flex-1 h-full relative">
          <GraphCanvas
            nodes={twin.nodes}
            edges={twin.edges}
            compromisedNodeIds={compromisedNodeIds}
            attackPaths={currentRun?.baseline_paths || []}
            previewDefense={previewDefense}
            onSelectNode={(node) => {
              setSelectedNode(node);
              setSelectedEdge(null);
            }}
            onSelectEdge={(edge) => {
              setSelectedEdge(edge);
              setSelectedNode(null);
            }}
          />

          {/* Floating Link Status Legend (Bottom-Left) */}
          <div className="absolute bottom-4 left-4 z-20">
            <Legend />
          </div>

          {/* Inspector Detail Drawer (Top-Right of canvas) */}
          <DetailDrawer
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            onClose={() => {
              setSelectedNode(null);
              setSelectedEdge(null);
            }}
          />
        </div>

        {/* Right Side: Analysis & Decision Sidebar (40%) */}
        <div className="w-[480px] border-l border-slate-800 bg-slate-950/95 overflow-y-auto p-4 space-y-4 shrink-0 shadow-2xl">
          {/* Comparison Matrix Component */}
          <ComparisonTable
            defenses={currentRun?.candidate_defenses || []}
            recommendedId={currentRun?.recommended_defense_id || null}
            selectedPreviewId={selectedPreviewDefenseId}
            onSelectPreview={(id) => setSelectedPreviewDefenseId(id)}
            onOpenApproval={handleOpenApproval}
          />

          {/* Plain-Language Rationale Component */}
          <RationalePanel
            explanation={explanation}
            isLoading={isExplaining}
            onSelectEvidence={(evId) => {
              const matchingEdge = twin.edges.find((e) => e.evidence_ids.includes(evId));
              if (matchingEdge) setSelectedEdge(matchingEdge);
            }}
          />
        </div>
      </div>

      {/* Human-in-the-Loop Approval Modal */}
      <ApprovalModal
        isOpen={isApprovalOpen}
        onClose={() => setIsApprovalOpen(false)}
        candidateDefenses={currentRun?.candidate_defenses || []}
        initialSelectedDefenseId={approvalTargetDefense?.defense_id || null}
        onConfirmApproval={handleConfirmApproval}
        verificationResult={verificationResult}
      />

      {/* Digital Twin Graph Editor Drawer */}
      <TwinEditor
        isOpen={isTwinEditorOpen}
        onClose={() => setIsTwinEditorOpen(false)}
        nodes={twin.nodes}
        edges={twin.edges}
        onAddNode={handleAddNode}
        onDeleteNode={handleDeleteNode}
        onAddEdge={handleAddEdge}
        onDeleteEdge={handleDeleteEdge}
      />
    </div>
  );
};

export default App;
