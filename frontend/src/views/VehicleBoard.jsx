// frontend/src/views/VehicleBoard.jsx
import React from 'react';
import { useNetraStore } from '../store';

export default function VehicleBoard() {
  const { activeVehiclePlate, navigateTo } = useNetraStore();

  return (
    <div className="p-6 bg-slate-900 rounded-lg border border-slate-800 space-y-6">
      <div className="flex justify-between items-start border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold">{activeVehiclePlate}</h2>
        <button onClick={() => navigateTo('GENERAL')} className="text-xs text-slate-400 hover:text-slate-100">&larr; Back</button>
      </div>
      <div className="bg-slate-950 p-4 rounded border border-slate-800 space-y-2 text-xs">
        <div className="text-red-400 font-bold uppercase mb-2">🚨 ACTIVE BLACKLIST STATUS flag set</div>
        <div>Owner: Shivaraj B M</div>
        <div>Type: Yamaha RX100</div>
        <button onClick={() => navigateTo('CASE', 'CASE-101')} className="mt-4 text-indigo-400 underline block">Open Connected Case Archive: CASE-101</button>
      </div>
    </div>
  );
}
