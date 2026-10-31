import React, { useState } from 'react';
import { DefenseResult } from '../api';
import {
  ShieldCheck,
  ShieldX,
  Award,
  ChevronDown,
  ChevronUp,
  Eye,
} from 'lucide-react';

interface ComparisonTableProps {
  defenses: DefenseResult[];
  recommendedId: string | null;
  selectedPreviewId: string | null;
  onSelectPreview: (defenseId: string | null) => void;
  onOpenApproval: (defense: DefenseResult) => void;
}

export const ComparisonTable: React.FC<ComparisonTableProps> = ({
  defenses,
  recommendedId,
  selectedPreviewId,
  onSelectPreview,
  onOpenApproval,
}) => {
  const [expandedBreakdownId, setExpandedBreakdownId] = useState<string | null>(null);

  if (!defenses || defenses.length === 0) {
    return (
      <div className="p-4 text-center text-slate-400 text-xs bg-slate-900/50 rounded-xl border border-slate-800">
        Run simulation to generate candidate defenses and comparison matrix.
      </div>
    );
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Award className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-slate-100">Candidate Defenses (Simulated Counterfactuals)</h3>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">3 Options Evaluated</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
              <th className="py-2 px-2">Rank</th>
              <th className="py-2 px-2">Candidate Action</th>
              <th className="py-2 px-2 text-center">Confirmed Left</th>
              <th className="py-2 px-2 text-center">Uncertain Left</th>
              <th className="py-2 px-2 text-center">Disruption</th>
              <th className="py-2 px-2 text-center">Effort</th>
              <th className="py-2 px-2 text-center">Meets Target</th>
              <th className="py-2 px-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-medium">
            {defenses.map((d) => {
              const isRecommended = d.defense_id === recommendedId;
              const isPreviewing = d.defense_id === selectedPreviewId;
              const isExpanded = d.defense_id === expandedBreakdownId;

              return (
                <React.Fragment key={d.defense_id}>
                  <tr
                    className={`transition-colors ${
                      isRecommended
                        ? 'bg-blue-950/30 hover:bg-blue-950/50'
                        : isPreviewing
                        ? 'bg-slate-800/40 hover:bg-slate-800/60'
                        : 'hover:bg-slate-800/30'
                    }`}
                  >
                    {/* Rank */}
                    <td className="py-2.5 px-2">
                      {d.rank ? (
                        <span
                          className={`inline-flex items-center justify-center w-6 h-6 rounded-full font-bold text-xs ${
                            d.rank === 1
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                              : 'bg-slate-800 text-slate-300 border border-slate-700'
                          }`}
                        >
                          #{d.rank}
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px] italic">DQ</span>
                      )}
                    </td>

                    {/* Candidate Name & Rationale snippet */}
                    <td className="py-2.5 px-2">
                      <div className="font-semibold text-slate-200">{d.name}</div>
                      <div className="text-[10px] text-slate-400 truncate max-w-xs" title={d.ranking_reason}>
                        {d.ranking_reason}
                      </div>
                    </td>

                    {/* Confirmed Paths Left */}
                    <td className="py-2.5 px-2 text-center font-mono">
                      <span
                        className={`px-2 py-0.5 rounded font-bold ${
                          d.confirmed_paths_left === 0
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : 'bg-rose-950 text-rose-300 border border-rose-800'
                        }`}
                      >
                        {d.confirmed_paths_left}
                      </span>
                    </td>

                    {/* Uncertain Paths Left */}
                    <td className="py-2.5 px-2 text-center font-mono">
                      <span
                        className={`px-2 py-0.5 rounded ${
                          d.uncertain_paths_left === 0
                            ? 'bg-slate-950 text-slate-400'
                            : 'bg-amber-950 text-amber-300 border border-amber-800'
                        }`}
                      >
                        {d.uncertain_paths_left}
                      </span>
                    </td>

                    {/* Disruption with breakdown toggle */}
                    <td className="py-2.5 px-2 text-center">
                      <button
                        onClick={() => setExpandedBreakdownId(isExpanded ? null : d.defense_id)}
                        className="inline-flex items-center gap-1 font-mono font-bold text-slate-200 hover:text-blue-400"
                        title="Click to view disruption breakdown"
                      >
                        <span>{d.disruption}</span>
                        {isExpanded ? (
                          <ChevronUp className="w-3 h-3 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-3 h-3 text-slate-400" />
                        )}
                      </button>
                    </td>

                    {/* Effort */}
                    <td className="py-2.5 px-2 text-center font-mono text-slate-300">
                      {d.effort}/5
                    </td>

                    {/* Meets Target */}
                    <td className="py-2.5 px-2 text-center">
                      {d.meets_target ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                          <ShieldCheck className="w-4 h-4 text-emerald-400" />
                          <span>Pass</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-400">
                          <ShieldX className="w-4 h-4 text-rose-400" />
                          <span>Fail</span>
                        </span>
                      )}
                    </td>

                    {/* Action buttons */}
                    <td className="py-2.5 px-2 text-right space-x-1.5 whitespace-nowrap">
                      {/* Preview toggle */}
                      <button
                        onClick={() => onSelectPreview(isPreviewing ? null : d.defense_id)}
                        className={`text-[11px] px-2.5 py-1 rounded border transition ${
                          isPreviewing
                            ? 'bg-sky-600 border-sky-500 text-white font-semibold'
                            : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                        }`}
                        title="Preview counterfactual impact on graph canvas"
                      >
                        <span className="flex items-center gap-1">
                          <Eye className="w-3 h-3" />
                          <span>{isPreviewing ? 'Hide Diff' : 'Preview'}</span>
                        </span>
                      </button>

                      {/* Approve button */}
                      <button
                        onClick={() => onOpenApproval(d)}
                        className="text-[11px] px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow transition"
                      >
                        Approve
                      </button>
                    </td>
                  </tr>

                  {/* Disruption Breakdown Accordion */}
                  {isExpanded && (
                    <tr className="bg-slate-950/70 border-b border-slate-800">
                      <td colSpan={8} className="p-3 text-[11px]">
                        <div className="space-y-1.5 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 font-mono">
                          <div className="font-semibold text-slate-300">Disruption Breakdown Formula:</div>
                          <div className="text-slate-400">
                            Total Disruption = Sum(Severed Edge Weights) + Sum(Orphaned Node Criticality)
                          </div>
                          <div className="grid grid-cols-2 gap-3 pt-1">
                            <div>
                              <span className="text-sky-300 font-semibold">Severed Edges:</span>
                              {Object.keys(d.disruption_breakdown.removed_edge_weights).length > 0 ? (
                                <ul className="list-disc list-inside text-slate-400 mt-0.5">
                                  {Object.entries(d.disruption_breakdown.removed_edge_weights).map(([k, w]) => (
                                    <li key={k}>
                                      {k} (weight: {w})
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="text-slate-500">None</p>
                              )}
                            </div>
                            <div>
                              <span className="text-amber-300 font-semibold">Orphaned Nodes Cut Off:</span>
                              {Object.keys(d.disruption_breakdown.orphaned_nodes_penalty).length > 0 ? (
                                <ul className="list-disc list-inside text-slate-400 mt-0.5">
                                  {Object.entries(d.disruption_breakdown.orphaned_nodes_penalty).map(([n, c]) => (
                                    <li key={n}>
                                      Node {n} (criticality: {c})
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="text-slate-500">None</p>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
