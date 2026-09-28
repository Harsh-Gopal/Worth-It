import React, { useState } from "react";
import { Shield, ShieldAlert, Loader2 } from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { API_BASE } from "../../lib/api";

export default function SecuritySettings() {
  const { securityEnabled, setSecurityEnabled, requestAuth } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [pin, setPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");

  const handleEnableSecurity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pin || pin.length < 4) {
      setError("PIN must be at least 4 characters.");
      return;
    }
    if (pin !== confirmPin) {
      setError("PINs do not match.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const res = await fetch(`${API_BASE}/auth/setup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin, confirm_pin: confirmPin })
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Setup failed");
      }
      
      setSecurityEnabled(true);
      setIsConfiguring(false);
      setPin("");
      setConfirmPin("");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDisableSecurity = () => {
    requestAuth(async () => {
      if (!confirm("Are you sure you want to disable PIN protection? Your settings will no longer be protected.")) {
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        const res = await fetch(`${API_BASE}/auth/setup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pin: "disabled", confirm_pin: "disabled" })
        });
        
        if (!res.ok) {
          throw new Error("Failed to disable security");
        }
        
        setSecurityEnabled(false);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    });
  };

  return (
    <div className="card">
      <div style={{
        padding: "18px 20px",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "38px",
            height: "38px",
            borderRadius: "10px",
            background: securityEnabled ? "rgba(22,163,74,0.08)" : "rgba(100,116,139,0.08)",
            border: `1px solid ${securityEnabled ? "rgba(22,163,74,0.2)" : "rgba(100,116,139,0.2)"}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            {securityEnabled ? (
              <Shield className="w-5 h-5" style={{ color: "var(--color-brand-green)" }} />
            ) : (
              <ShieldAlert className="w-5 h-5" style={{ color: "var(--text-muted)" }} />
            )}
          </div>
          <div>
            <h2 style={{
              fontSize: "14.5px",
              fontWeight: 700,
              color: "var(--text-primary)",
              margin: "0 0 3px 0",
              letterSpacing: "-0.01em",
            }}>
              Security
            </h2>
            <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
              Optional protection for sensitive settings.
            </p>
          </div>
        </div>
      </div>

      <div style={{ padding: "20px" }}>
        {securityEnabled ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "12px 14px",
              background: "var(--ring-green)",
              border: "1px solid rgba(22,163,74,0.25)",
              borderRadius: "8px",
            }}>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-brand-green)" }}>
                Security status: Enabled
              </div>
              <button
                onClick={handleDisableSecurity}
                disabled={loading}
                className="btn-secondary"
                style={{ fontSize: "12px", padding: "6px 12px" }}
              >
                {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : "Disable Protection"}
              </button>
            </div>
            {error && <p style={{ fontSize: "13px", color: "var(--color-brand-red)", margin: 0 }}>{error}</p>}
          </div>
        ) : isConfiguring ? (
          <form onSubmit={handleEnableSecurity} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <p style={{ fontSize: "13px", color: "var(--text-primary)", margin: "0 0 8px 0" }}>
              Protect Telegram and other sensitive configuration with a PIN.
            </p>
            
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "6px" }}>PIN</label>
                <input
                  type="password"
                  placeholder="••••"
                  value={pin}
                  onChange={e => setPin(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--bg-input)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    color: "var(--text-primary)",
                    fontSize: "14px",
                    padding: "9px 12px",
                    outline: "none",
                  }}
                  autoFocus
                  required
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "6px" }}>Confirm PIN</label>
                <input
                  type="password"
                  placeholder="••••"
                  value={confirmPin}
                  onChange={e => setConfirmPin(e.target.value)}
                  style={{
                    width: "100%",
                    background: "var(--bg-input)",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    color: "var(--text-primary)",
                    fontSize: "14px",
                    padding: "9px 12px",
                    outline: "none",
                  }}
                  required
                />
              </div>
            </div>

            {error && <p style={{ fontSize: "13px", color: "var(--color-brand-red)", margin: 0 }}>{error}</p>}

            <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
              <button type="submit" disabled={loading} className="btn-primary" style={{ flex: 1 }}>
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Enable Security"}
              </button>
              <button type="button" onClick={() => setIsConfiguring(false)} className="btn-secondary" style={{ flex: 1 }}>
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-secondary)" }}>
              Security status: Disabled
            </div>
            <button
              onClick={() => setIsConfiguring(true)}
              className="btn-primary"
              style={{ fontSize: "12px", padding: "6px 12px" }}
            >
              Enable PIN Protection
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
