import React from 'react';
import { Incident } from '../api';
import { Play, RotateCcw, Edit3, ShieldAlert, AlertTriangle } from 'lucide-react';

interface IncidentBarProps {
  incidents: Incident[];
  selectedIncidentId: string;
  onSelectIncident: (id: string) => void;
  onRunSimulation: () => void;
  onResetTwin: () => void;
  onToggleTwinEditor: () => void;
  isLoading: boolean;
  baselineConfirmedCount?: number;
  baselineUncertainCount?: number;
}

export const IncidentBar: React.FC<IncidentBarProps> = ({
  incidents,
  selectedIncidentId,
  onSelectIncident,
  onRunSimulation,
  onResetTwin,
  onToggleTwinEditor,
  isLoading,
  baselineConfirmedCount,
  baselineUncertainCount,
}) => {
  return (
    <div className="glass border-b border-white/[0.06] px-5 py-2.5 flex flex-wrap items-center justify-between gap-3">
      {/* Incident Selection */}
      <div className="flex items-center gap-3">
        <label htmlFor="incident-select" className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          <span>Simulated Incident:</span>
        </label>
        <select
          id="incident-select"
          value={selectedIncidentId}
          onChange={(e) => onSelectIncident(e.target.value)}
          className="glass-input rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none font-medium"
        >
          {incidents.map((inc) => (
            <option key={inc.id} value={inc.id} className="bg-slate-900">
              [{inc.id.toUpperCase()}] {inc.title}
            </option>
          ))}
        </select>

        {/* Action button */}
        <button
          onClick={onRunSimulation}
          disabled={isLoading}
          className="flex items-center gap-1.5 glass-btn-primary text-white font-semibold text-xs px-4 py-2 rounded-lg disabled:opacity-50"
        >
          <Play className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : 'fill-white'}`} />
          <span>{isLoading ? 'Simulating...' : 'Run Flight Simulation'}</span>
        </button>
      </div>

      {/* Metrics Banner */}
      {baselineConfirmedCount !== undefined && (
        <div className="hidden md:flex items-center gap-3 glass-subtle px-3 py-1.5 rounded-xl text-xs">
          <div className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse shadow-lg shadow-rose-500/50" />
            <span className="font-semibold">{baselineConfirmedCount}</span>
            <span className="text-slate-400">Confirmed Path{baselineConfirmedCount !== 1 ? 's' : ''}</span>
          </div>
          <span className="text-white/10">|</span>
          <div className="flex items-center gap-1.5 text-amber-400">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span className="font-semibold">{baselineUncertainCount ?? 0}</span>
            <span className="text-slate-400">Uncertain Path{(baselineUncertainCount ?? 0) !== 1 ? 's' : ''}</span>
          </div>
        </div>
      )}

      {/* Utility Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={onToggleTwinEditor}
          className="flex items-center gap-1.5 glass-btn text-slate-200 text-xs px-3 py-1.5 rounded-lg"
          title="Add or edit nodes and edges"
        >
          <Edit3 className="w-3.5 h-3.5 text-slate-400" />
          <span>Twin Editor</span>
        </button>

        <button
          onClick={onResetTwin}
          className="flex items-center gap-1.5 glass-btn text-slate-300 text-xs px-3 py-1.5 rounded-lg"
          title="Reset twin graph to initial seed state"
        >
          <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
          <span>Reset Twin</span>
        </button>
      </div>
    </div>
  );
};
