import React, { useState } from 'react';
import { DefenseResult, VerificationResult } from '../api';
import {
  ShieldAlert,
  AlertTriangle,
  X,
  CheckCircle2,
  FileCheck,
} from 'lucide-react';

interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  candidateDefenses: DefenseResult[];
  initialSelectedDefenseId: string | null;
  onConfirmApproval: (defenseId: string, note: string) => Promise<VerificationResult>;
  verificationResult: VerificationResult | null;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({
  isOpen,
  onClose,
  candidateDefenses,
  initialSelectedDefenseId,
  onConfirmApproval,
  verificationResult,
}) => {
  const [selectedDefenseId, setSelectedDefenseId] = useState<string>(
    initialSelectedDefenseId || (candidateDefenses[0]?.defense_id ?? '')
  );
  const [note, setNote] = useState<string>('Approved intervention after risk and disruption review.');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDefenseId) return;
    setIsSubmitting(true);
    try {
      await onConfirmApproval(selectedDefenseId, note);
    } finally {
      setIsSubmitting(false);
    }
  };


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/90">
          <div className="flex items-center gap-2">
            <FileCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="font-semibold text-slate-100 text-sm">
              Human-in-the-Loop Remediation Approval
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition p-1 rounded-lg hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs">
          {verificationResult ? (
            /* Post-Approval Verification Banner */
            <div className="space-y-4 animate-fade-in">
              <div
                className={`p-4 rounded-xl border ${
                  verificationResult.passed
                    ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-200'
                    : 'bg-rose-950/40 border-rose-500/50 text-rose-200'
                }`}
              >
                <div className="flex items-center gap-2 font-bold text-sm mb-1">
                  {verificationResult.passed ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <ShieldAlert className="w-5 h-5 text-rose-400" />
                  )}
                  <span>
                    {verificationResult.passed ? 'Automated Verification Passed' : 'Verification Failed'}
                  </span>
                </div>
                <p className="text-xs leading-relaxed text-slate-300">
                  {verificationResult.message}
                </p>
              </div>

              {/* Residual Status Checklist */}
              <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 space-y-2">
                <div className="font-semibold text-slate-200 border-b border-slate-800 pb-1">
                  Verification Metrics:
                </div>
                <div className="grid grid-cols-2 gap-2 text-slate-300">
                  <div>
                    Confirmed Paths Left: <span className="font-bold font-mono text-emerald-400">{verificationResult.confirmed_paths_left}</span>
                  </div>
                  <div>
                    Uncertain Paths Left: <span className="font-bold font-mono text-amber-400">{verificationResult.uncertain_paths_left}</span>
                  </div>
                </div>

                {verificationResult.uncertain_paths_left > 0 && (
                  <div className="mt-2 text-amber-300 flex items-start gap-1.5 text-[11px] bg-amber-950/30 p-2 rounded border border-amber-900/60">
                    <AlertTriangle className="w-3.5 h-3.5 mt-0.5 text-amber-400 shrink-0" />
                    <span>
                      Residual uncertain paths remain active. As visibility is missing, safe operation cannot be proven until telemetry is refreshed.
                    </span>
                  </div>
                )}
              </div>

              <div className="flex justify-end pt-2">
                <button
                  onClick={onClose}
                  className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-4 py-2 rounded-lg text-xs"
                >
                  Done (View Updated Twin)
                </button>
              </div>
            </div>
          ) : (
            /* Approval Form */
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="text-slate-300 leading-relaxed">
                As part of non-negotiable principle #3 (<strong>Human decides</strong>), please review and explicitly approve an intervention to apply to the digital twin.
              </div>

              {/* Radio list for candidates */}
              <div className="space-y-2">
                <label className="font-semibold text-slate-200 block">
                  Select Intervention to Apply:
                </label>
                {candidateDefenses.map((d) => (
                  <label
                    key={d.defense_id}
                    className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition ${
                      selectedDefenseId === d.defense_id
                        ? 'bg-blue-950/40 border-blue-500 ring-1 ring-blue-500'
                        : 'bg-slate-950/50 border-slate-800 hover:bg-slate-800/40'
                    }`}
                  >
                    <input
                      type="radio"
                      name="defense-select"
                      value={d.defense_id}
                      checked={selectedDefenseId === d.defense_id}
                      onChange={() => setSelectedDefenseId(d.defense_id)}
                      className="mt-1 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-100">{d.name}</span>
                        {d.rank && (
                          <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-amber-300 border border-slate-700">
                            Rank #{d.rank}
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        Confirmed left: {d.confirmed_paths_left} | Uncertain left: {d.uncertain_paths_left} | Disruption: {d.disruption} | Effort: {d.effort}/5
                      </div>
                    </div>
                  </label>
                ))}
              </div>

              {/* Approver Note */}
              <div className="space-y-1.5">
                <label className="font-semibold text-slate-200 block">
                  Approver Justification Note:
                </label>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  rows={3}
                  required
                  placeholder="Record business context or reason for selecting this remediation..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Action buttons */}
              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-md transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Simulating Intervention...' : 'Approve & Apply to Twin'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
