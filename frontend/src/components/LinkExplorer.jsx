// frontend/src/components/LinkExplorer.jsx
import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import { useNetraStore } from '../store';

export default function LinkExplorer() {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const navigateTo = useNetraStore((state) => state.navigateTo);

  useEffect(() => {
    if (!containerRef.current) return;
    try {
      const cy = cytoscape({
        container: containerRef.current,
        elements: [
          { data: { id: 's1', label: 'Ramesh Gowda', type: 'Suspect' } },
          { data: { id: 's2', label: 'Shivaraj B M', type: 'Suspect' } },
          { data: { id: 'v1', label: 'KA-01-HE-4321', type: 'Vehicle' } },
          { data: { id: 'v2', label: 'KA-42-M-8888', type: 'Vehicle' } },
          { data: { source: 's1', target: 'v1', label: 'HAS_VEHICLE' } },
          { data: { source: 's2', target: 'v2', label: 'DRIVES' } },
          { data: { source: 's1', target: 's2', label: 'CO_ACCUSED' } }
        ],
        style: [
          { selector: 'node', style: { 'background-color': '#1e293b', 'label': 'data(label)', 'color': '#f8fafc', 'font-size': '12px', 'text-valign': 'center', 'text-halign': 'center', 'width': '80px', 'height': '80px', 'border-width': '2px', 'border-color': '#4f46e5' } },
          { selector: 'node[type="Vehicle"]', style: { 'background-color': '#14532d', 'border-color': '#22c55e', 'shape': 'rectangle', 'width': '100px', 'height': '40px' } },
          { selector: 'edge', style: { 'width': 2, 'line-color': '#64748b', 'target-arrow-color': '#64748b', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'label': 'data(label)', 'font-size': '9px', 'color': '#94a3b8', 'text-background-opacity': 1, 'text-background-color': '#0f172a', 'text-background-padding': '3px' } }
        ],
        layout: { name: 'cose', padding: 30 }
      });
      cyRef.current = cy;
      cy.on('dblclick', 'node', (evt) => {
        const node = evt.target;
        if (node.data('type') === 'Suspect') {
          navigateTo('PROFILE', node.data('id') === 's1' ? 'KSP-GUID-9901-A' : 'KSP-GUID-2234-B');
        }
      });
    } catch (err) {
      console.error(err);
    }
    return () => { if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null; } };
  }, [navigateTo]);

  return <div ref={containerRef} className="w-full h-full min-h-[300px] relative bg-slate-950 rounded border border-slate-800" />;
}
