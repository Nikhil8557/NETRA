// frontend/src/views/CaseBoard.jsx
import React, { useState, useEffect } from 'react';
import { useNetraStore } from '../store';
import api from '../api';
import BreakGlassModal from '../components/BreakGlassModal';

export default function CaseBoard() {
  const { activeCaseId, navigateTo } = useNetraStore();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchCase = async (id) => {
    setLoading(true);
    try {
      const res = await api.get(`/case/${id}`);
      setData(res.data);
    } catch (err) {
      console.warn(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (activeCaseId) fetchCase(activeCaseId); }, [activeCaseId]);

  if (loading) return <div className="p-6 text-slate-400 animate-pulse">Loading case records...</div>;

  return (
    <div className="p-6 bg-slate-900 rounded-lg border border-slate-800 space-y-6">
      <div className="flex justify-between items-start border-b border-slate-800 pb-4">
        <div>
          <span className="text-xs bg-indigo-950 text-indigo-400 px-2.5 py-1 rounded font-bold">{data?.jurisdiction}</span>
          <h2 className="text-xl font-bold mt-2">{activeCaseId} : {data?.title}</h2>
        </div>
        <button onClick={() => navigateTo('GENERAL')} className="text-xs text-slate-400 hover:text-slate-100">&larr; Back</button>
      </div>
      <div className="space-y-4">
        <div className="bg-slate-950 p-4 rounded border border-slate-800">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase">Case Summary</h4>
          <p className="mt-2 text-sm">{data?.summary}</p>
        </div>
        <div className="bg-slate-950 p-4 rounded border border-slate-800">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase">Classified Investigation Notes</h4>
          <p className="mt-2 text-xs text-amber-300 font-mono">{data?.sensitive_notes}</p>
        </div>
        <div>
          <h4 className="text-[10px] font-bold text-slate-400 uppercase">Linked Subjects</h4>
          <div className="flex gap-2 mt-2">
            {data?.suspects?.map((sus) => (
              <button key={sus} onClick={() => navigateTo('PROFILE', sus)} className="bg-slate-950 p-2 border border-slate-800 text-xs text-indigo-400 rounded">👤 {sus}</button>
            ))}
          </div>
        </div>
      </div>
      <BreakGlassModal onOverrideExecuted={fetchCase} />
    </div>
  );
}
