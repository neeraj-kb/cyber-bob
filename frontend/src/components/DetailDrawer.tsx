import React from 'react';
import { Node, Edge } from '../api';
import {
  X,
  Activity,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
} from 'lucide-react';

interface DetailDrawerProps {
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  onClose: () => void;
}

export const DetailDrawer: React.FC<DetailDrawerProps> = ({
  selectedNode,
  selectedEdge,
  onClose,
}) => {
  if (!selectedNode && !selectedEdge) return null;

  return (
    <div className="absolute top-4 right-4 z-40 w-80 glass-card p-4 text-xs space-y-3 animate-fade-in glow-blue">
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
        <div className="flex items-center gap-1.5 font-bold text-slate-100">
          <Activity className="w-4 h-4 text-blue-400" />
          <span>{selectedNode ? 'Node Telemetry' : 'Link Evidence Inspector'}</span>
        </div>
        <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-white/[0.08] transition">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {selectedNode && (
        <div className="space-y-2.5">
          <div>
            <div className="text-[10px] text-slate-400/70 uppercase font-mono">Entity Label</div>
            <div className="font-semibold text-slate-100 text-sm">{selectedNode.label}</div>
            <div className="text-[11px] font-mono text-slate-400">{selectedNode.id}</div>
          </div>

          <div className="grid grid-cols-2 gap-2 glass-subtle p-2.5 rounded-xl">
            <div>
              <span className="text-[10px] text-slate-400/70">Archetype:</span>
              <div className="font-semibold text-slate-200 uppercase">{selectedNode.type}</div>
            </div>
            <div>
              <span className="text-[10px] text-slate-400/70">Criticality:</span>
              <div className="font-bold text-amber-400">{selectedNode.criticality} / 5</div>
            </div>
            <div>
              <span className="text-[10px] text-slate-400/70">Exposed Entry:</span>
              <div className="font-semibold text-slate-200">{selectedNode.is_entry ? 'Yes' : 'No'}</div>
            </div>
            <div>
              <span className="text-[10px] text-slate-400/70">Critical Target:</span>
              <div className="font-bold text-rose-400">{selectedNode.is_critical ? 'Yes' : 'No'}</div>
            </div>
          </div>
        </div>
      )}

      {selectedEdge && (
        <div className="space-y-2.5">
          <div>
            <div className="text-[10px] text-slate-400/70 uppercase font-mono">Connection Link</div>
            <div className="font-mono font-bold text-slate-100 text-sm">
              {selectedEdge.src} → {selectedEdge.dst}
            </div>
            <div className="text-[11px] text-purple-400 uppercase font-semibold">
              Kind: {selectedEdge.kind}
            </div>
          </div>

          <div className="space-y-2 glass-subtle p-2.5 rounded-xl">
            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400/70">Evidence Status:</span>
              <span
                className={`inline-flex items-center gap-1 font-bold ${
                  selectedEdge.status === 'confirmed'
                    ? 'text-emerald-400'
                    : selectedEdge.status === 'needs_review'
                    ? 'text-amber-400'
                    : 'text-slate-400'
                }`}
              >
                {selectedEdge.status === 'confirmed' && <CheckCircle2 className="w-3.5 h-3.5" />}
                {selectedEdge.status === 'needs_review' && <AlertTriangle className="w-3.5 h-3.5" />}
                {selectedEdge.status === 'unknown' && <HelpCircle className="w-3.5 h-3.5" />}
                <span className="capitalize">{selectedEdge.status.replace('_', ' ')}</span>
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400/70">Confidence Score:</span>
              <span className="font-mono font-bold text-sky-400">
                {Math.round(selectedEdge.confidence * 100)}%
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400/70">Business Weight:</span>
              <span className="font-mono font-bold text-slate-200">
                {selectedEdge.business_weight} / 5
              </span>
            </div>

            <div className="flex items-center justify-between border-t border-white/[0.06] pt-1.5">
              <span className="text-[11px] text-slate-400/70">Last Telemetry:</span>
              <span className="text-[11px] text-slate-300 font-mono">
                {selectedEdge.last_seen ? selectedEdge.last_seen.split('T')[0] : 'Never (Unknown)'}
              </span>
            </div>
          </div>

          {/* Supporting Evidence IDs */}
          <div>
            <span className="text-[10px] text-slate-400/70 uppercase font-mono">Supporting Event Logs:</span>
            {selectedEdge.evidence_ids && selectedEdge.evidence_ids.length > 0 ? (
              <div className="flex flex-wrap gap-1 mt-1">
                {selectedEdge.evidence_ids.map((id) => (
                  <span
                    key={id}
                    className="glass-btn text-sky-300 px-2 py-0.5 rounded-lg font-mono text-[10px]"
                  >
                    {id}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-[11px] text-slate-500 italic mt-0.5">
                No supporting telemetry observed. Link status is unknown.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
