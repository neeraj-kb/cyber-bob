import React from 'react';
import { Info, CheckCircle2, AlertTriangle, HelpCircle } from 'lucide-react';

export const Legend: React.FC = () => {
  return (
    <div className="bg-slate-900/90 backdrop-blur border border-slate-800 rounded-xl p-3 shadow-xl text-xs space-y-2.5 max-w-sm">
      <div className="flex items-center gap-1.5 font-semibold text-slate-200 border-b border-slate-800 pb-1.5">
        <Info className="w-3.5 h-3.5 text-blue-400" />
        <span>Evidence & Link Status Legend</span>
      </div>

      <div className="space-y-1.5">
        {/* Confirmed Link */}
        <div className="flex items-start gap-2">
          <div className="flex items-center h-4 mt-0.5">
            <div className="w-6 h-0.5 bg-emerald-500 rounded" />
          </div>
          <div>
            <div className="flex items-center gap-1 text-emerald-400 font-medium">
              <CheckCircle2 className="w-3 h-3" />
              <span>Confirmed Link</span>
            </div>
            <p className="text-[11px] text-slate-400">Supported by fresh, verifiable evidence (within 7d)</p>
          </div>
        </div>

        {/* Needs-Review Link */}
        <div className="flex items-start gap-2">
          <div className="flex items-center h-4 mt-0.5">
            <div className="w-6 h-0.5 border-t-2 border-dashed border-amber-500" />
          </div>
          <div>
            <div className="flex items-center gap-1 text-amber-400 font-medium">
              <AlertTriangle className="w-3 h-3" />
              <span>Needs-Review Link</span>
            </div>
            <p className="text-[11px] text-slate-400">Incomplete, conflicting, or stale telemetry (&gt;7d)</p>
          </div>
        </div>

        {/* Unknown Link */}
        <div className="flex items-start gap-2">
          <div className="flex items-center h-4 mt-0.5">
            <div className="w-6 h-0.5 border-t-2 border-dotted border-slate-500" />
          </div>
          <div>
            <div className="flex items-center gap-1 text-slate-400 font-medium">
              <HelpCircle className="w-3 h-3" />
              <span>Unknown Link</span>
            </div>
            <p className="text-[11px] text-slate-400">Insufficient telemetry; zero supporting records</p>
          </div>
        </div>

        {/* Attack Trajectory Indicators */}
        <div className="border-t border-slate-800/80 pt-1.5 flex items-center justify-between text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500 animate-pulse" />
            <span className="text-red-400 font-semibold">Active Attack Path</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500" />
            <span className="text-amber-400">Uncertain Path</span>
          </div>
        </div>
      </div>
    </div>
  );
};
