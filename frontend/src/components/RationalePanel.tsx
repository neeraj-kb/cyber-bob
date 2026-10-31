import React from 'react';
import { ExplanationResponse } from '../api';
import {
  Sparkles,
  Bot,
  AlertTriangle,
  FileText,
  ExternalLink,
} from 'lucide-react';

interface RationalePanelProps {
  explanation: ExplanationResponse | null;
  isLoading: boolean;
  onSelectEvidence?: (evidenceId: string) => void;
}

export const RationalePanel: React.FC<RationalePanelProps> = ({
  explanation,
  isLoading,
  onSelectEvidence,
}) => {
  if (isLoading) {
    return (
      <div className="glass-card p-5 text-xs space-y-2 text-center text-slate-400 animate-fade-in">
        <div className="inline-block animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full mb-1" />
        <p>Synthesizing plain-language rationale from computed facts...</p>
      </div>
    );
  }

  if (!explanation) {
    return (
      <div className="glass-card p-5 text-xs text-slate-400 text-center animate-fade-in">
        Run simulation to generate plain-language explanation and trade-off rationale.
      </div>
    );
  }

  const isGemini = explanation.mode === 'gemini';

  return (
    <div className="glass-card p-4 space-y-3 text-xs animate-fade-in">
      {/* Header with Mode Badge */}
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
        <div className="flex items-center gap-2">
          {isGemini ? (
            <Sparkles className="w-4 h-4 text-purple-400" />
          ) : (
            <FileText className="w-4 h-4 text-blue-400" />
          )}
          <h3 className="text-sm font-semibold text-slate-100">Plain-Language Decision Rationale</h3>
        </div>

        <span
          className={`inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border backdrop-blur-sm ${
            isGemini
              ? 'bg-purple-500/10 text-purple-300 border-purple-500/20'
              : 'bg-blue-500/10 text-blue-300 border-blue-500/20'
          }`}
        >
          {isGemini ? <Bot className="w-3 h-3 text-purple-400" /> : <FileText className="w-3 h-3 text-blue-400" />}
          <span>{isGemini ? 'Gemini 2.5 Explanation' : 'Deterministic Template'}</span>
        </span>
      </div>

      {/* Summary */}
      <div className="glass-subtle p-3 rounded-xl text-slate-300 leading-relaxed">
        {explanation.summary}
      </div>

      {/* Rationale Content */}
      <div className="space-y-1.5 text-slate-300 whitespace-pre-wrap leading-relaxed">
        {explanation.rationale}
      </div>

      {/* Missing Visibility / Uncertainty Warning */}
      <div className="bg-amber-500/[0.06] backdrop-blur-md border border-amber-500/20 rounded-xl p-3 text-amber-200 space-y-1">
        <div className="flex items-center gap-1.5 font-bold text-amber-400">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span>Core Safety Principle</span>
        </div>
        <p className="text-[11px] leading-relaxed text-amber-100/80">
          {explanation.uncertainty_warning}
        </p>
      </div>

      {/* Supporting Evidence Citations */}
      {explanation.evidence_cited && explanation.evidence_cited.length > 0 && (
        <div className="border-t border-white/[0.06] pt-2 flex items-center gap-2 flex-wrap">
          <span className="text-[11px] text-slate-400/80 font-mono">Evidence Cited:</span>
          {explanation.evidence_cited.map((evId) => (
            <button
              key={evId}
              onClick={() => onSelectEvidence && onSelectEvidence(evId)}
              className="inline-flex items-center gap-1 glass-btn text-sky-300 text-[11px] font-mono px-2 py-0.5 rounded-lg transition"
            >
              <span>{evId}</span>
              <ExternalLink className="w-2.5 h-2.5 text-slate-400" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
