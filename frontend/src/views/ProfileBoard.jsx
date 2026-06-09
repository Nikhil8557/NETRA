// frontend/src/views/ProfileBoard.jsx
import React from 'react';
import { useNetraStore } from '../store';
import LinkExplorer from '../components/LinkExplorer';

export default function ProfileBoard() {
  const { activeProfileId, navigateTo } = useNetraStore();
  const name = activeProfileId === 'KSP-GUID-9901-A' ? 'Ramesh Gowda' : 'Shivaraj B M';

  return (
    <div className="p-6 bg-slate-900 rounded-lg border border-slate-800 space-y-6">
      <div className="flex justify-between items-start border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold">{name} ({activeProfileId})</h2>
        </div>
        <button onClick={() => navigateTo('GENERAL')} className="text-xs text-slate-400 hover:text-slate-100">&larr; Back</button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-950 p-4 rounded border border-slate-800 text-xs space-y-2">
          <div><span className="text-slate-500">Known Alias:</span> Blade Shivaraj</div>
          <div><span className="text-slate-500">Offense:</span> Vehicle Theft / Burglary</div>
          <div><span className="text-slate-500">Contact:</span> +91 9900112233</div>
        </div>
        <div className="md:col-span-2 space-y-2">
          <h4 className="text-[10px] font-bold uppercase text-slate-400">Target Core Network Path</h4>
          <LinkExplorer />
        </div>
      </div>
    </div>
  );
}
