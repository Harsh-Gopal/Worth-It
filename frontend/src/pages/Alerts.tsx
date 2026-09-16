import { useState } from "react";
import { useAlerts } from "../hooks/useAlerts";
import { Bell, Play, Pause, Trash2, Loader2, Activity, Bookmark } from "lucide-react";

export default function Alerts() {
  const { alerts, isLoading, error, toggleAlert, deleteAlert, runAlert } = useAlerts();
  const [runningAlertId, setRunningAlertId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "48px" }}>
        <Loader2 className="w-6 h-6 animate-spin" style={{ color: "var(--color-brand-green)" }} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        padding: "12px 16px",
        background: "var(--ring-red)",
        border: "1px solid rgba(220,38,38,0.3)",
        borderRadius: "8px",
        color: "var(--color-brand-red)",
        fontSize: "14px",
      }}>
        Failed to load alerts: {error}
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "64px 16px" }}>
        <div style={{
          width: "52px",
          height: "52px",
          borderRadius: "50%",
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          margin: "0 auto 16px",
        }}>
          <Bell className="w-6 h-6" style={{ color: "var(--color-brand-green)" }} />
        </div>
        <h2 style={{ fontSize: "18px", fontWeight: 600, color: "var(--text-primary)", margin: "0 0 8px" }}>
          No Active Alerts
        </h2>
        <p style={{ fontSize: "14px", color: "var(--text-secondary)", margin: 0, maxWidth: "340px", marginLeft: "auto", marginRight: "auto" }}>
          Run a search and save your criteria as an alert to enable automated background monitoring.
        </p>
      </div>
    );
  }

  const handleRunNow = async (id: string) => {
    setRunningAlertId(id);
    try {
      const events = await runAlert(id);
      if (events.length > 0) {
        alert(`Alert triggered! ${events.length} deals matched and notification sent.`);
      } else {
        alert("Search finished. No new deals found matching the alert criteria.");
      }
    } catch {
      alert("Failed to run alert.");
    } finally {
      setRunningAlertId(null);
    }
  };

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", width: "100%" }}>
      {/* Page header */}
      <div style={{ marginBottom: "24px" }}>
        <h1 style={{
          fontSize: "22px",
          fontWeight: 700,
          color: "var(--text-primary)",
          margin: 0,
          marginBottom: "4px",
        }}>
          My Alerts
        </h1>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)", margin: 0 }}>
          Automated background deal monitoring.
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {alerts.map((alert: any) => (
          <div
            key={alert.id}
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border)",
              borderRadius: "12px",
              padding: "18px 20px",
              display: "flex",
              flexDirection: "column",
              gap: "14px",
            }}
          >
            {/* Alert name & tags */}
            <div>
              {alert.name && (
                <h2 style={{
                  fontSize: "15px",
                  fontWeight: 600,
                  color: "var(--text-primary)",
                  margin: "0 0 8px",
                }}>
                  {alert.name}
                </h2>
              )}

              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", alignItems: "center" }}>
                {alert.product_urls?.length > 0 && (
                  <span style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    fontSize: "11px",
                    fontWeight: 700,
                    color: "var(--color-brand-green)",
                    background: "var(--ring-green)",
                    border: "1px solid rgba(22,163,74,0.25)",
                    borderRadius: "6px",
                    padding: "2px 8px",
                  }}>
                    <Bookmark className="w-3 h-3" /> {alert.product_urls.length} Tracked
                  </span>
                )}

                {alert.categories?.map((c: string) => (
                  <span key={c} style={{
                    fontSize: "11px",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    background: "var(--bg-muted)",
                    border: "1px solid var(--border)",
                    borderRadius: "6px",
                    padding: "2px 8px",
                  }}>
                    {c}
                  </span>
                ))}

                {alert.keywords?.length > 0 && (
                  <span style={{
                    fontSize: "13px",
                    fontWeight: 500,
                    color: "var(--text-primary)",
                  }}>
                    {alert.keywords.join(", ")}
                  </span>
                )}

                {alert.exclude_keywords?.length > 0 && (
                  <span style={{ fontSize: "12px", color: "var(--color-brand-red)" }}>
                    exclude: {alert.exclude_keywords.join(", ")}
                  </span>
                )}
              </div>
            </div>

            {/* Stats row */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", alignItems: "center" }}>
              {alert.min_discount_pct && (
                <span style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "var(--color-brand-red)",
                  background: "var(--ring-red)",
                  border: "1px solid rgba(220,38,38,0.25)",
                  borderRadius: "6px",
                  padding: "3px 8px",
                }}>
                  ≥{alert.min_discount_pct}% off
                </span>
              )}
              <span style={{
                fontSize: "12px",
                fontWeight: 500,
                color: "var(--text-secondary)",
                background: "var(--bg-muted)",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                padding: "3px 8px",
              }}>
                {alert.radius_km} km radius
              </span>
              {alert.enabled ? (
                <span style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "var(--color-brand-green)",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}>
                  <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--color-brand-green)", display: "inline-block" }} />
                  Active
                </span>
              ) : (
                <span style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "var(--text-muted)",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}>
                  <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--text-muted)", display: "inline-block" }} />
                  Paused
                </span>
              )}
            </div>

            {/* Action buttons */}
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              paddingTop: "12px",
              borderTop: "1px solid var(--border)",
              justifyContent: "flex-end",
              flexWrap: "wrap",
            }}>
              <button
                onClick={() => handleRunNow(alert.id!)}
                disabled={runningAlertId === alert.id}
                className="btn-secondary"
                style={{ fontSize: "12px", padding: "6px 14px" }}
              >
                {runningAlertId === alert.id ? (
                  <><Loader2 className="w-3 h-3 animate-spin" /> Running…</>
                ) : (
                  <><Activity className="w-3 h-3" /> Run Now</>
                )}
              </button>

              <button
                onClick={() => toggleAlert(alert.id!, !alert.enabled)}
                title={alert.enabled ? "Pause alert" : "Resume alert"}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "32px",
                  height: "32px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: alert.enabled ? "var(--ring-green)" : "var(--bg-muted)",
                  color: alert.enabled ? "var(--color-brand-green)" : "var(--text-muted)",
                  cursor: "pointer",
                  transition: "all 0.15s",
                }}
              >
                {alert.enabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>

              <button
                onClick={() => deleteAlert(alert.id!)}
                title="Delete alert"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "32px",
                  height: "32px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "var(--bg-muted)",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                  transition: "all 0.15s",
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLElement).style.color = "var(--color-brand-red)";
                  (e.currentTarget as HTMLElement).style.borderColor = "var(--color-brand-red)";
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.color = "var(--text-muted)";
                  (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
                }}
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
