import { create } from 'zustand';

interface AuthState {
  isLocked: boolean;
  securityEnabled: boolean;
  showModal: boolean;
  setLocked: (locked: boolean) => void;
  setSecurityEnabled: (enabled: boolean) => void;
  setShowModal: (show: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isLocked: false,
  securityEnabled: false,
  showModal: false,
  setLocked: (locked) => set({ isLocked: locked }),
  setSecurityEnabled: (enabled) => set({ securityEnabled: enabled }),
  setShowModal: (show) => set({ showModal: show }),
}));
