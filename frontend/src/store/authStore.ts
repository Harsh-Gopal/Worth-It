import { create } from 'zustand';

interface AuthState {
  isLocked: boolean;
  setupRequired: boolean;
  showModal: boolean;
  setLocked: (locked: boolean) => void;
  setSetupRequired: (required: boolean) => void;
  setShowModal: (show: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isLocked: false,
  setupRequired: false,
  showModal: false,
  setLocked: (locked) => set({ isLocked: locked }),
  setSetupRequired: (required) => set({ setupRequired: required }),
  setShowModal: (show) => set({ showModal: show }),
}));
