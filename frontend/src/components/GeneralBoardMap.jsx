// frontend/src/components/GeneralBoardMap.jsx
import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { registerCorrectionProtocol } from '@india-boundary-corrector/maplibre-protocol';
import { useNetraStore } from '../store';
import 'maplibre-gl/dist/maplibre-gl.css';

export default function GeneralBoardMap() {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const navigateTo = useNetraStore((state) => state.navigateTo);
  const [errorStatus, setErrorStatus] = useState(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;
    try {
      registerCorrectionProtocol(maplibregl);
    } catch (err) {
      console.warn("India boundary corrector protocol registry skipped.", err);
    }

    try {
      const map = new maplibregl.Map({
        container: mapContainerRef.current,
        style: {
          version: 8,
          sources: {
            'corrected-osm': {
              type: 'raster',
              tiles: ['ibc://a.tile.openstreetmap.org/{z}/{x}/{y}.png'],
              tileSize: 256,
              attribution: 'OpenStreetMap | Corrected Boundaries via IBC protocol'
            }
          },
          layers: [{ id: 'base-layer', type: 'raster', source: 'corrected-osm' }]
        },
        center: [75.7139, 15.3173],
        zoom: 6.5
      });
      mapRef.current = map;

      // Coordinate references represent dynamic geographical boundaries inside Karnataka
      const mockIncidents = [
        { id: 'CASE-101', coords: [77.0452, 12.5843], title: 'Mandya Transit Theft', jurisdiction: 'MANDYA' },
        { id: 'CASE-202', coords: [77.5946, 12.9716], title: 'Bangalore Cyber Extortion', jurisdiction: 'BANGALORE' }
      ];

      mockIncidents.forEach((inc) => {
        const popup = new maplibregl.Popup({ offset: 25 }).setHTML(`
          <div class="p-2 text-slate-900">
            <h4 class="font-bold text-sm">${inc.title}</h4>
            <p class="text-xs text-slate-500">Jurisdiction: ${inc.jurisdiction}</p>
            <button id="btn-${inc.id}" class="mt-2 text-xs bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-1 px-2 rounded w-full">Analyze Incident File</button>
          </div>
        `);
        popup.on('open', () => {
          document.getElementById(`btn-${inc.id}`)?.addEventListener('click', () => { navigateTo('CASE', inc.id); });
        });
        new maplibregl.Marker().setLngLat(inc.coords).setPopup(popup).addTo(map);
      });
    } catch (err) {
      setErrorStatus("Failed to render map. Confirm system WebGL settings.");
    }
    return () => { if (mapRef.current) { mapRef.current.remove(); mapRef.current = null; } };
  }, [navigateTo]);

  return (
    <div className="relative w-full h-full rounded-lg border border-slate-700 overflow-hidden bg-slate-900 min-h-[400px]">
      {errorStatus ? <div className="flex items-center justify-center h-full text-slate-400">{errorStatus}</div> : <div ref={mapContainerRef} className="w-full h-full absolute inset-0" />}
    </div>
  );
}
