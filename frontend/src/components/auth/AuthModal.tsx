import React, { useState, useEffect } from "react";
import { useAuthStore } from "../../store/authStore";
import { API_BASE } from "../../lib/api";
import { Lock, Unlock, ShieldAlert, X } from "lucide-react";

export function AuthModal() {
  const { showModal, setShowModal, setupRequired, setLocked, setSetupRequired } = useAuthStore();
  const [pin, setPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (showModal) {
      setPin("");
      setConfirmPin("");
      setError("");
    }
  }, [showModal]);

  if (!showModal) return null;

  const handleSetup = async (disabled: boolean) => {
    try {
      setLoading(true);
      setError("");
      
      const setupPin = disabled ? "disabled" : pin;
      
      const res = await fetch(`${API_BASE}/auth/setup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin: setupPin, confirm_pin: disabled ? "disabled" : confirmPin })
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Setup failed");
      }
      
      setSetupRequired(false);
      setLocked(false);
      setShowModal(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUnlock = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError("");
      
      const res = await fetch(`${API_BASE}/auth/unlock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin })
      });
      
      if (!res.ok) {
        throw new Error("Incorrect PIN");
      }
      
      setLocked(false);
      setShowModal(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 w-full max-w-sm shadow-2xl relative">
        <button 
          onClick={() => setShowModal(false)}
          className="absolute top-4 right-4 text-zinc-500 hover:text-white transition-colors"
        >
          <X size={20} />
        </button>

        {setupRequired ? (
          <div className="space-y-4">
            <div className="flex items-center gap-3 text-emerald-400 mb-6">
              <ShieldAlert size={24} />
              <h2 className="text-xl font-bold text-white">Secure this instance?</h2>
            </div>
            
            <p className="text-zinc-400 text-sm mb-4">
              Local development mode detected. You can secure this instance with a PIN.
            </p>

            <div className="space-y-3">
              <input
                type="password"
                placeholder="Enter PIN (min 4 chars)"
                className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                value={pin}
                onChange={(e) => setPin(e.target.value)}
              />
              <input
                type="password"
                placeholder="Confirm PIN"
                className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                value={confirmPin}
                onChange={(e) => setConfirmPin(e.target.value)}
              />
            </div>
            
            {error && <p className="text-red-400 text-sm">{error}</p>}
            
            <div className="pt-4 flex flex-col gap-3">
              <button
                onClick={() => handleSetup(false)}
                disabled={loading || !pin || pin !== confirmPin}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 px-4 rounded-lg transition-colors disabled:opacity-50"
              >
                Enable PIN Protection
              </button>
              <button
                onClick={() => handleSetup(true)}
                disabled={loading}
                className="w-full bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-medium py-3 px-4 rounded-lg transition-colors"
              >
                Continue Without PIN
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleUnlock} className="space-y-4">
            <div className="flex items-center gap-3 text-emerald-400 mb-6">
              <Lock size={24} />
              <h2 className="text-xl font-bold text-white">Protected Action</h2>
            </div>
            
            <p className="text-zinc-400 text-sm mb-4">
              This action requires owner access. Please enter your PIN to continue.
            </p>

            <input
              type="password"
              placeholder="••••••••"
              autoFocus
              className="w-full bg-black/50 border border-zinc-800 rounded-lg px-4 py-3 text-white text-center tracking-widest text-lg focus:outline-none focus:border-emerald-500 transition-colors"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
            />
            
            {error && <p className="text-red-400 text-sm text-center">{error}</p>}
            
            <button
              type="submit"
              disabled={loading || !pin}
              className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 px-4 rounded-lg transition-colors disabled:opacity-50 mt-4"
            >
              <Unlock size={18} />
              Unlock
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
