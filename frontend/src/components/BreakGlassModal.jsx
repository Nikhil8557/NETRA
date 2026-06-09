// frontend/src/components/BreakGlassModal.jsx
import React, { useState } from 'react';
import { useNetraStore } from '../store';

export default function BreakGlassModal({ onOverrideExecuted }) {
  const { isBreakGlassOpen, pendingOverrideRequest, closeBreakGlass, registerEmergencyOverride } = useNetraStore();
  const [reason, setReason] = useState('');
  const [activeFir, setActiveFir] = useState('');
  const [validationError, setValidationError] = useState('');

  if (!isBreakGlassOpen || !pendingOverrideRequest) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!reason.trim() || !activeFir.trim()) {
      setValidationError("Justification and FIR parameters are required.");
      return;
    }
    registerEmergencyOverride(pendingOverrideRequest.id, reason, activeFir);
    closeBreakGlass();
    if (onOverrideExecuted) onOverrideExecuted(pendingOverrideRequest.id);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border-2 border-red-600 rounded-lg max-w-md w-full overflow-hidden shadow-2xl">
        <div className="bg-red-950/40 p-4 border-b border-red-500">
          <h3 className="font-bold text-red-500 text-sm uppercase">Emergency Override Audit Warning</h3>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-xs text-slate-300 leading-relaxed">
            Target <strong>{pendingOverrideRequest.id}</strong> lies inside restricted jurisdiction <strong>{pendingOverrideRequest.targetJurisdiction}</strong>. This bypass action will be saved permanently.
          </p>
          {validationError && <div className="text-red-400 text-xs">{validationError}</div>}
          <div className="space-y-1">
            <label className="block text-[10px] font-bold text-slate-400 uppercase">Override Justification</label>
            <textarea className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-xs text-slate-200 focus:outline-none" value={reason} onChange={(e) => setReason(e.target.value)} />
          </div>
          <div className="space-y-1">
            <label className="block text-[10px] font-bold text-slate-400 uppercase">Active Investigation FIR Number</label>
            <input type="text" className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-xs text-slate-200 focus:outline-none" value={activeFir} onChange={(e) => setActiveFir(e.target.value)} />
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <button type="button" className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200" onClick={closeBreakGlass}>Cancel</button>
            <button type="submit" className="px-4 py-1.5 text-xs bg-red-600 hover:bg-red-700 font-bold text-white rounded">Proceed</button>
          </div>
        </form>
      </div>
    </div>
  );
}
