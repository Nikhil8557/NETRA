// frontend/src/App.jsx
import React from 'react';
import { useNetraStore } from './store';
import GeneralBoardMap from './components/GeneralBoardMap';
import CaseBoard from './views/CaseBoard';
import ProfileBoard from './views/ProfileBoard';
import VehicleBoard from './views/VehicleBoard';
import './index.css';

export default function App() {
  const { activeBoard, setJWTToken } = useNetraStore();

  const loadTestToken = async (jurisdiction) => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: `OFFICER-${jurisdiction}-99`,
          role: 'STATION_OFFICER',
          jurisdiction: jurisdiction
        })
      });
      const data = await res.json();
      setJWTToken(data.access_token);
      alert(`Token successfully updated: OFFICER-${jurisdiction}-99`);
    } catch (err) {
      console.warn("API offline fallback.", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col">
      <header className="bg-slate-900 border-b border-slate-800 p-4 flex justify-between items-center shadow-lg">
        <div>
          <h1 className="text-lg font-bold text-indigo-400 uppercase tracking-wide">KSP-NETRA Gateway</h1>
          <p className="text-[10px] text-slate-500">Karnataka State Police Network Evaluation & Relationship Analytics</p>
        </div>
        <div className="flex gap-2 items-center bg-slate-950 p-2 rounded border border-slate-800">
          <span className="text-[9px] uppercase font-bold text-slate-400">Select Test Profile:</span>
          <button onClick={() => loadTestToken('MANDYA')} className="bg-slate-800 hover:bg-slate-700 px-2 py-1 text-xs rounded">Mandya PS</button>
          <button onClick={() => loadTestToken('BANGALORE')} className="bg-slate-800 hover:bg-slate-700 px-2 py-1 text-xs rounded">Bangalore City</button>
        </div>
      </header>

      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        {activeBoard === 'GENERAL' && (
          <div className="space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Incident Density Map</h2>
            <GeneralBoardMap />
          </div>
        )}
        {activeBoard === 'CASE' && <CaseBoard />}
        {activeBoard === 'PROFILE' && <ProfileBoard />}
        {activeBoard === 'VEHICLE' && <VehicleBoard />}
      </main>
    </div>
  );
}
