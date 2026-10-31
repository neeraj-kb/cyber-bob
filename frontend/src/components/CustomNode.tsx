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

const typeColors: Record<NodeType, { border: string; bg: string; badge: string; glow: string }> = {
  device: {
    border: 'border-sky-500/30 hover:border-sky-400/50',
    bg: 'bg-white/[0.04] backdrop-blur-xl',
    badge: 'bg-sky-500/10 text-sky-300 border-sky-500/20',
    glow: 'hover:shadow-sky-500/10',
  },
  identity: {
    border: 'border-purple-500/30 hover:border-purple-400/50',
    bg: 'bg-white/[0.04] backdrop-blur-xl',
    badge: 'bg-purple-500/10 text-purple-300 border-purple-500/20',
    glow: 'hover:shadow-purple-500/10',
  },
  app: {
    border: 'border-emerald-500/30 hover:border-emerald-400/50',
    bg: 'bg-white/[0.04] backdrop-blur-xl',
    badge: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
    glow: 'hover:shadow-emerald-500/10',
  },
  data: {
    border: 'border-amber-500/30 hover:border-amber-400/50',
    bg: 'bg-white/[0.04] backdrop-blur-xl',
    badge: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
    glow: 'hover:shadow-amber-500/10',
  },
};

export const CustomNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as unknown as CustomNodeData;
  const { id, label, type, criticality, is_entry, is_critical, isCompromised, isRemoved } = nodeData;
  const theme = typeColors[type] || typeColors.device;

  return (
    <div
      className={`relative min-w-[200px] max-w-[240px] rounded-2xl border p-3 shadow-lg transition-all duration-300 ${
        theme.bg
      } ${theme.glow} hover:shadow-2xl ${
        isRemoved
          ? 'opacity-40 border-red-500/40 bg-red-500/[0.03] grayscale'
          : isCompromised
          ? 'border-red-500/60 shadow-red-500/20 animate-pulse glow-rose'
          : selected
          ? 'border-blue-400/60 ring-2 ring-blue-500/30 glow-blue'
          : theme.border
      }`}
    >
      <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-slate-400/60 !border-0" />
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-slate-400/60 !border-0" />

      {/* Top badges */}
      <div className="flex items-center justify-between gap-1 mb-2">
        <div className="flex items-center gap-1.5">
          <span className="p-1 rounded-lg bg-white/[0.06] border border-white/[0.08]">
            {typeIcons[type]}
          </span>
          <span className={`text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-md border backdrop-blur-sm ${theme.badge}`}>
            {type}
          </span>
        </div>

        {/* Criticality Rating */}
        <div className="flex items-center gap-1 bg-white/[0.04] backdrop-blur-sm px-1.5 py-0.5 rounded-lg border border-white/[0.08]">
          <span className="text-[10px] text-slate-400/70 font-mono">Crit:</span>
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
        <div className="text-[10px] font-mono text-slate-400/60 truncate">{id}</div>
      </div>

      {/* Flags / Status Badges */}
      <div className="mt-2.5 flex flex-wrap gap-1">
        {is_entry && (
          <span className="inline-flex items-center gap-0.5 text-[9px] font-medium bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 px-1.5 py-0.5 rounded-md backdrop-blur-sm">
            <Globe className="w-2.5 h-2.5" />
            Entry
          </span>
        )}

        {is_critical && (
          <span className="inline-flex items-center gap-0.5 text-[9px] font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20 px-1.5 py-0.5 rounded-md backdrop-blur-sm">
            <Crown className="w-2.5 h-2.5 text-amber-400" />
            Critical Target
          </span>
        )}

        {isCompromised && (
          <span className="inline-flex items-center gap-0.5 text-[9px] font-bold bg-red-500/10 text-red-300 border border-red-500/20 px-1.5 py-0.5 rounded-md animate-bounce backdrop-blur-sm">
            <Flame className="w-2.5 h-2.5 text-red-400" />
            Compromised
          </span>
        )}

        {isRemoved && (
          <span className="inline-flex items-center gap-0.5 text-[9px] font-bold bg-red-500/[0.06] text-red-400 border border-red-500/20 px-1.5 py-0.5 rounded-md backdrop-blur-sm">
            <Ban className="w-2.5 h-2.5 text-red-400" />
            Isolated / Severed
          </span>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-slate-400/60 !border-0" />
      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-slate-400/60 !border-0" />
    </div>
  );
};
