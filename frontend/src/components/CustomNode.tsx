import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import {
  Server,
  User,
  AppWindow,
  Database,
  Flame,
  Globe,
  Crown,
  Ban,
} from 'lucide-react';
import { NodeType } from '../api';

export interface CustomNodeData {
  id: string;
  label: string;
  type: NodeType;
  criticality: number;
  is_entry: boolean;
  is_critical: boolean;
  isCompromised?: boolean;
  isRemoved?: boolean;
}

const typeIcons: Record<NodeType, React.ReactNode> = {
  device: <Server className="w-4 h-4 text-sky-400" />,
  identity: <User className="w-4 h-4 text-purple-400" />,
  app: <AppWindow className="w-4 h-4 text-emerald-400" />,
  data: <Database className="w-4 h-4 text-amber-400" />,
};

const typeColors: Record<NodeType, { border: string; bg: string; badge: string }> = {
  device: {
    border: 'border-sky-500/40 hover:border-sky-400',
    bg: 'bg-slate-900/90',
    badge: 'bg-sky-950 text-sky-300 border-sky-800',
  },
  identity: {
    border: 'border-purple-500/40 hover:border-purple-400',
    bg: 'bg-slate-900/90',
    badge: 'bg-purple-950 text-purple-300 border-purple-800',
  },
  app: {
    border: 'border-emerald-500/40 hover:border-emerald-400',
    bg: 'bg-slate-900/90',
    badge: 'bg-emerald-950 text-emerald-300 border-emerald-800',
  },
  data: {
    border: 'border-amber-500/40 hover:border-amber-400',
    bg: 'bg-slate-900/90',
    badge: 'bg-amber-950 text-amber-300 border-amber-800',
  },
};

export const CustomNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as unknown as CustomNodeData;
  const { id, label, type, criticality, is_entry, is_critical, isCompromised, isRemoved } = nodeData;
  const theme = typeColors[type] || typeColors.device;

  return (
    <div
      className={`relative min-w-[200px] max-w-[240px] rounded-xl border p-3 shadow-lg transition-all duration-200 ${
        theme.bg
      } ${
        isRemoved
          ? 'opacity-40 border-red-500/60 bg-red-950/20 grayscale'
          : isCompromised
          ? 'border-red-500 shadow-red-500/20 animate-pulse'
          : selected
          ? 'border-blue-400 ring-2 ring-blue-500/40'
          : theme.border
      }`}
    >
      <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-slate-400" />
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-slate-400" />

      {/* Top badges */}
      <div className="flex items-center justify-between gap-1 mb-2">
        <div className="flex items-center gap-1.5">
          <span className="p-1 rounded-md bg-slate-800/80 border border-slate-700/60">
            {typeIcons[type]}
          </span>
          <span className={`text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded border ${theme.badge}`}>
            {type}
          </span>
        </div>

        {/* Criticality Rating */}
        <div className="flex items-center gap-1 bg-slate-950/60 px-1.5 py-0.5 rounded border border-slate-800">
          <span className="text-[10px] text-slate-400 font-mono">Crit:</span>
          <span
            className={`text-[11px] font-bold font-mono ${
              criticality >= 4 ? 'text-rose-400' : criticality === 3 ? 'text-amber-400' : 'text-sky-300'
            }`}
          >
            {criticality}/5
          </span>
        </div>
      </div>

      {/* Label and ID */}
      <div className="space-y-0.5">
        <h4 className="text-xs font-semibold text-slate-100 truncate" title={label}>
          {label}
        </h4>
        <div className="text-[10px] font-mono text-slate-400 truncate">{id}</div>
      </div>

      {/* Flags / Status Badges */}
      <div className="mt-2.5 flex flex-wrap gap-1">
        {is_entry && (
          <span className="inline-flex items-center gap-0.5 text-[9px] font-medium bg-cyan-950 text-cyan-300 border border-cyan-800 px-1.5 py-0.5 rounded">
            <Globe className="w-2.5 h-2.5" />
            Entry
          </span>
        )}

        {is_critical && (
          <span className="inline-flex items-center gap-0.5 text-[9px] font-medium bg-amber-950 text-amber-300 border border-amber-800 px-1.5 py-0.5 rounded">
            <Crown className="w-2.5 h-2.5 text-amber-400" />
            Critical Target
          </span>
        )}

        {isCompromised && (
          <span className="inline-flex items-center gap-0.5 text-[9px] font-bold bg-red-950 text-red-300 border border-red-800 px-1.5 py-0.5 rounded animate-bounce">
            <Flame className="w-2.5 h-2.5 text-red-400" />
            Compromised
          </span>
        )}

        {isRemoved && (
          <span className="inline-flex items-center gap-0.5 text-[9px] font-bold bg-slate-900 text-red-400 border border-red-700 px-1.5 py-0.5 rounded">
            <Ban className="w-2.5 h-2.5 text-red-400" />
            Isolated / Severed
          </span>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-slate-400" />
      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-slate-400" />
    </div>
  );
};
