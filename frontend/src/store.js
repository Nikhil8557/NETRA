// frontend/src/store.js
import { create } from 'zustand';

export const useNetraStore = create((set) => ({
  activeBoard: 'GENERAL',
  activeCaseId: null,
  activeProfileId: null,
  activeVehiclePlate: null,
  userToken: localStorage.getItem('ksp_netra_token') || null,
  activeOverrides: {},
  isBreakGlassOpen: false,
  pendingOverrideRequest: null,

  navigateTo: (board, id = null) => {
    const updates = { activeBoard: board };
    if (board === 'CASE') updates.activeCaseId = id;
    if (board === 'PROFILE') updates.activeProfileId = id;
    if (board === 'VEHICLE') updates.activeVehiclePlate = id;
    set(updates);
  },

  setJWTToken: (token) => {
    if (token) localStorage.setItem('ksp_netra_token', token);
    else localStorage.removeItem('ksp_netra_token');
    set({ userToken: token });
  },

  registerEmergencyOverride: (id, reason, activeFir) => {
    set((state) => ({
      activeOverrides: { ...state.activeOverrides, [id]: { reason, activeFir } }
    }));
  },

  openBreakGlass: (type, id, targetJurisdiction) => {
    set({ isBreakGlassOpen: true, pendingOverrideRequest: { type, id, targetJurisdiction } });
  },

  closeBreakGlass: () => {
    set({ isBreakGlassOpen: false, pendingOverrideRequest: null });
  }
}));
