import { create } from 'zustand';

interface AuthState {
  isLocked: boolean;
  securityEnabled: boolean;
  showModal: boolean;
  pendingAction: (() => void) | null;
  setLocked: (locked: boolean) => void;
  setSecurityEnabled: (enabled: boolean) => void;
  setShowModal: (show: boolean) => void;
  requestAuth: (action: () => void) => void;
  executePendingAction: () => void;
  clearPendingAction: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  isLocked: false,
  securityEnabled: false,
  showModal: false,
  pendingAction: null,
  setLocked: (locked) => set({ isLocked: locked }),
  setSecurityEnabled: (enabled) => set({ securityEnabled: enabled }),
  setShowModal: (show) => set({ showModal: show }),
  requestAuth: (action) => {
    if (get().securityEnabled && get().isLocked) {
      set({ pendingAction: action, showModal: true });
    } else {
      action();
    }
  },
  executePendingAction: () => {
    const action = get().pendingAction;
    if (action) {
      action();
      set({ pendingAction: null });
    }
  },
  clearPendingAction: () => set({ pendingAction: null }),
}));
