import React, { useMemo } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  Node as FlowNode,
  Edge as FlowEdge,
  MarkerType,
  NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Node, Edge, AttackPath, DefenseResult } from '../api';
import { CustomNode } from './CustomNode';

const nodeTypes: NodeTypes = {
  custom: CustomNode,
};

interface GraphCanvasProps {
  nodes: Node[];
  edges: Edge[];
  compromisedNodeIds: string[];
  attackPaths: AttackPath[];
  previewDefense: DefenseResult | null;
  onSelectNode: (node: Node) => void;
  onSelectEdge: (edge: Edge) => void;
}

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  nodes,
  edges,
  compromisedNodeIds,
  attackPaths,
  previewDefense,
  onSelectNode,
  onSelectEdge,
}) => {
  // Precompute attack path edges
  const activeAttackEdges = useMemo(() => {
    const map = new Map<string, 'confirmed' | 'uncertain'>();
    for (const p of attackPaths) {
      for (const eKey of p.edges) {
        if (!map.has(eKey) || p.classification === 'confirmed') {
          map.set(eKey, p.classification);
        }
      }
    }
    return map;
  }, [attackPaths]);

  // Compute layout positions for nodes
  const flowNodes: FlowNode[] = useMemo(() => {
    const entryNodes = nodes.filter((n) => n.is_entry);
    const criticalNodes = nodes.filter((n) => n.is_critical);
    const middleNodes = nodes.filter((n) => !n.is_entry && !n.is_critical);

    const positions: Record<string, { x: number; y: number }> = {};

    entryNodes.forEach((n, idx) => {
      positions[n.id] = { x: 50, y: 80 + idx * 180 };
    });

    middleNodes.forEach((n, idx) => {
      const col = idx % 2;
      const row = Math.floor(idx / 2);
      positions[n.id] = { x: 380 + col * 260, y: 60 + row * 160 };
    });

    criticalNodes.forEach((n, idx) => {
      positions[n.id] = { x: 960, y: 80 + idx * 170 };
    });

    return nodes.map((n) => {
      const isCompromised = compromisedNodeIds.includes(n.id);
      const isRemoved = previewDefense?.removed_nodes.includes(n.id) || false;

      return {
        id: n.id,
        type: 'custom',
        position: positions[n.id] || { x: 200, y: 200 },
        data: {
          ...n,
          isCompromised,
          isRemoved,
        },
      };
    });
  }, [nodes, compromisedNodeIds, previewDefense]);

  // Convert digital twin edges to React Flow edges with status styling
  const flowEdges: FlowEdge[] = useMemo(() => {
    const removedEdgeKeys = new Set(previewDefense?.removed_edges || []);

    return edges.map((e) => {
      const edgeKey = `${e.src}->${e.dst}`;
      const isRemoved = removedEdgeKeys.has(edgeKey);
      const attackType = activeAttackEdges.get(edgeKey);

      let strokeColor = '#10b981'; // Confirmed green
      let strokeDash = undefined;

      if (e.status === 'needs_review') {
        strokeColor = '#f59e0b'; // Amber dashed
        strokeDash = '5 5';
      } else if (e.status === 'unknown') {
        strokeColor = '#64748b'; // Slate dotted
        strokeDash = '2 4';
      }

      let customClass = '';
      if (attackType === 'confirmed') {
        customClass = 'attack-path-edge';
      } else if (attackType === 'uncertain') {
        customClass = 'attack-path-edge-uncertain';
      }

      if (isRemoved) {
        customClass = 'removed-ghost-edge';
        strokeColor = '#ef4444';
      }

      return {
        id: edgeKey,
        source: e.src,
        target: e.dst,
        animated: attackType !== undefined,
        className: customClass,
        style: {
          stroke: isRemoved ? '#ef4444' : strokeColor,
          strokeWidth: isRemoved ? 1.5 : attackType ? 3.5 : 2,
          strokeDasharray: isRemoved ? '4 4' : strokeDash,
          opacity: isRemoved ? 0.3 : 1,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 14,
          height: 14,
          color: isRemoved ? '#ef4444' : attackType === 'confirmed' ? '#ef4444' : attackType === 'uncertain' ? '#f59e0b' : strokeColor,
        },
        label: isRemoved ? '✂️ SEVERED' : `${e.kind} (wt:${e.business_weight})`,
        labelStyle: {
          fill: isRemoved ? '#ef4444' : '#94a3b8',
          fontSize: 9,
          fontWeight: 600,
          fontFamily: 'monospace',
        },
        labelBgStyle: {
          fill: '#090d16',
          fillOpacity: 0.85,
        },
      };
    });
  }, [edges, activeAttackEdges, previewDefense]);

  return (
    <div className="w-full h-full bg-[#090d16]">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        nodeTypes={nodeTypes}
        fitView
        onNodeClick={(_, node) => {
          const original = nodes.find((n) => n.id === node.id);
          if (original) onSelectNode(original);
        }}
        onEdgeClick={(_, edge) => {
          const original = edges.find((e) => `${e.src}->${e.dst}` === edge.id);
          if (original) onSelectEdge(original);
        }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#1e293b" />
        <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300" />
        <MiniMap
          nodeColor={(n) => {
            const data = n.data as unknown as Node;
            if (data?.is_critical) return '#f59e0b';
            if (data?.is_entry) return '#06b6d4';
            return '#3b82f6';
          }}
          className="!bg-slate-950 !border-slate-800"
        />
      </ReactFlow>
    </div>
  );
};
