import React, { useState } from 'react';
import { Node, Edge, NodeType, EdgeKind, EdgeStatus } from '../api';
import { Plus, Trash2, X, Network } from 'lucide-react';

interface TwinEditorProps {
  isOpen: boolean;
  onClose: () => void;
  nodes: Node[];
  edges: Edge[];
  onAddNode: (node: Node) => Promise<void>;
  onDeleteNode: (nodeId: string) => Promise<void>;
  onAddEdge: (edge: Edge) => Promise<void>;
  onDeleteEdge: (src: string, dst: string) => Promise<void>;
}

export const TwinEditor: React.FC<TwinEditorProps> = ({
  isOpen,
  onClose,
  nodes,
  edges,
  onAddNode,
  onDeleteNode,
  onAddEdge,
  onDeleteEdge,
}) => {
  const [activeTab, setActiveTab] = useState<'nodes' | 'edges'>('nodes');

  // New Node Form State
  const [newNodeId, setNewNodeId] = useState('');
  const [newNodeLabel, setNewNodeLabel] = useState('');
  const [newNodeType, setNewNodeType] = useState<NodeType>('device');
  const [newNodeCrit, setNewNodeCrit] = useState(3);
  const [newNodeIsEntry, setNewNodeIsEntry] = useState(false);
  const [newNodeIsCritical, setNewNodeIsCritical] = useState(false);

  // New Edge Form State
  const [newEdgeSrc, setNewEdgeSrc] = useState(nodes[0]?.id || '');
  const [newEdgeDst, setNewEdgeDst] = useState(nodes[1]?.id || '');
  const [newEdgeKind, setNewEdgeKind] = useState<EdgeKind>('access');
  const [newEdgeStatus, setNewEdgeStatus] = useState<EdgeStatus>('confirmed');
  const [newEdgeWeight, setNewEdgeWeight] = useState(3);

  if (!isOpen) return null;

  const handleCreateNode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNodeId || !newNodeLabel) return;
    await onAddNode({
      id: newNodeId.trim().toLowerCase(),
      label: newNodeLabel.trim(),
      type: newNodeType,
      criticality: newNodeCrit,
      is_entry: newNodeIsEntry,
      is_critical: newNodeIsCritical || newNodeCrit >= 4,
    });
    setNewNodeId('');
    setNewNodeLabel('');
  };

  const handleCreateEdge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEdgeSrc || !newEdgeDst || newEdgeSrc === newEdgeDst) return;
    await onAddEdge({
      src: newEdgeSrc,
      dst: newEdgeDst,
      kind: newEdgeKind,
      status: newEdgeStatus,
      confidence: newEdgeStatus === 'confirmed' ? 0.9 : newEdgeStatus === 'needs_review' ? 0.45 : 0.05,
      last_seen: new Date().toISOString(),
      evidence_ids: [],
      business_weight: newEdgeWeight,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center gap-2">
            <Network className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold text-slate-100 text-sm">Digital Twin Graph Editor</h3>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab switch */}
        <div className="flex border-b border-slate-800 px-4 pt-2 bg-slate-950/50 text-xs">
          <button
            onClick={() => setActiveTab('nodes')}
            className={`pb-2 px-3 font-semibold border-b-2 transition ${
              activeTab === 'nodes'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Nodes ({nodes.length})
          </button>
          <button
            onClick={() => setActiveTab('edges')}
            className={`pb-2 px-3 font-semibold border-b-2 transition ${
              activeTab === 'edges'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Edges ({edges.length})
          </button>
        </div>

        {/* Body */}
        <div className="p-4 overflow-y-auto space-y-4 text-xs">
          {activeTab === 'nodes' ? (
            <div className="space-y-4">
              {/* Add Node Form */}
              <form onSubmit={handleCreateNode} className="bg-slate-950/70 p-3 rounded-xl border border-slate-800 space-y-2.5">
                <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                  <Plus className="w-3.5 h-3.5 text-blue-400" />
                  <span>Add New Twin Node</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="ID (e.g., auth-srv-02)"
                    value={newNodeId}
                    onChange={(e) => setNewNodeId(e.target.value)}
                    required
                    className="bg-slate-900 border border-slate-700 rounded p-1.5 text-slate-100"
                  />
                  <input
                    type="text"
                    placeholder="Label (e.g., Auth Server)"
                    value={newNodeLabel}
                    onChange={(e) => setNewNodeLabel(e.target.value)}
                    required
                    className="bg-slate-900 border border-slate-700 rounded p-1.5 text-slate-100"
                  />
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="text-[10px] text-slate-400">Type:</label>
                    <select
                      value={newNodeType}
                      onChange={(e) => setNewNodeType(e.target.value as NodeType)}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-slate-100"
                    >
                      <option value="device">Device</option>
                      <option value="identity">Identity</option>
                      <option value="app">App</option>
                      <option value="data">Data</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400">Criticality (1-5):</label>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      value={newNodeCrit}
                      onChange={(e) => setNewNodeCrit(Number(e.target.value))}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-slate-100"
                    />
                  </div>
                  <div className="flex items-center gap-3 pt-4">
                    <label className="flex items-center gap-1 text-[11px] text-slate-300">
                      <input
                        type="checkbox"
                        checked={newNodeIsEntry}
                        onChange={(e) => setNewNodeIsEntry(e.target.checked)}
                      />
                      Entry
                    </label>
                    <label className="flex items-center gap-1 text-[11px] text-slate-300">
                      <input
                        type="checkbox"
                        checked={newNodeIsCritical}
                        onChange={(e) => setNewNodeIsCritical(e.target.checked)}
                      />
                      Critical
                    </label>
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded font-semibold text-xs"
                >
                  Add Node
                </button>
              </form>

              {/* Node List */}
              <div className="divide-y divide-slate-800">
                {nodes.map((n) => (
                  <div key={n.id} className="py-2 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-slate-200">{n.label}</span>{' '}
                      <span className="text-[11px] font-mono text-slate-400">({n.id})</span>
                      <div className="text-[10px] text-slate-400 space-x-1.5 mt-0.5">
                        <span className="uppercase text-sky-400">{n.type}</span>
                        <span>•</span>
                        <span>Crit: {n.criticality}</span>
                        {n.is_entry && <span>• <strong className="text-cyan-400">Entry</strong></span>}
                        {n.is_critical && <span>• <strong className="text-amber-400">Critical</strong></span>}
                      </div>
                    </div>
                    <button
                      onClick={() => onDeleteNode(n.id)}
                      className="p-1 text-slate-400 hover:text-rose-400 transition"
                      title="Delete node"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Add Edge Form */}
              <form onSubmit={handleCreateEdge} className="bg-slate-950/70 p-3 rounded-xl border border-slate-800 space-y-2.5">
                <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                  <Plus className="w-3.5 h-3.5 text-blue-400" />
                  <span>Add New Link (Edge)</span>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-slate-400">Source Node:</label>
                    <select
                      value={newEdgeSrc}
                      onChange={(e) => setNewEdgeSrc(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-slate-100"
                    >
                      {nodes.map((n) => (
                        <option key={n.id} value={n.id}>
                          {n.label} ({n.id})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400">Target Node:</label>
                    <select
                      value={newEdgeDst}
                      onChange={(e) => setNewEdgeDst(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-slate-100"
                    >
                      {nodes.map((n) => (
                        <option key={n.id} value={n.id}>
                          {n.label} ({n.id})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="text-[10px] text-slate-400">Kind:</label>
                    <select
                      value={newEdgeKind}
                      onChange={(e) => setNewEdgeKind(e.target.value as EdgeKind)}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-slate-100"
                    >
                      <option value="access">Access</option>
                      <option value="trust">Trust</option>
                      <option value="dependency">Dependency</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400">Status:</label>
                    <select
                      value={newEdgeStatus}
                      onChange={(e) => setNewEdgeStatus(e.target.value as EdgeStatus)}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-slate-100"
                    >
                      <option value="confirmed">Confirmed</option>
                      <option value="needs_review">Needs Review</option>
                      <option value="unknown">Unknown</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400">Business Weight (1-5):</label>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      value={newEdgeWeight}
                      onChange={(e) => setNewEdgeWeight(Number(e.target.value))}
                      className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-slate-100"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded font-semibold text-xs"
                >
                  Add Edge
                </button>
              </form>

              {/* Edge List */}
              <div className="divide-y divide-slate-800">
                {edges.map((e) => (
                  <div key={`${e.src}->${e.dst}`} className="py-2 flex items-center justify-between">
                    <div>
                      <span className="font-mono font-semibold text-slate-200">
                        {e.src} → {e.dst}
                      </span>
                      <div className="text-[10px] text-slate-400 space-x-1.5 mt-0.5">
                        <span className="uppercase text-purple-400">{e.kind}</span>
                        <span>•</span>
                        <span
                          className={
                            e.status === 'confirmed'
                              ? 'text-emerald-400'
                              : e.status === 'needs_review'
                              ? 'text-amber-400'
                              : 'text-slate-400'
                          }
                        >
                          {e.status}
                        </span>
                        <span>•</span>
                        <span>Weight: {e.business_weight}</span>
                        <span>•</span>
                        <span>Conf: {Math.round(e.confidence * 100)}%</span>
                      </div>
                    </div>
                    <button
                      onClick={() => onDeleteEdge(e.src, e.dst)}
                      className="p-1 text-slate-400 hover:text-rose-400 transition"
                      title="Delete edge"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
