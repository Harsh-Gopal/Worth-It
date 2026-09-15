import { useState } from "react";
import { useAlerts } from "../hooks/useAlerts";
import { Bell, Play, Pause, Trash2, Loader2, Activity } from "lucide-react";

export default function Alerts() {
  const { alerts, isLoading, error, toggleAlert, deleteAlert, runAlert } = useAlerts();
  const [runningAlertId, setRunningAlertId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Loader2 className="w-8 h-8 text-[var(--color-brand-green)] animate-spin" />
      </div>
    );
  }

  if (error) {
    return <div className="text-red-400 p-4 bg-[var(--bg-main)] rounded-xl border border-[var(--color-brand-red)] shadow-lg shadow-[var(--color-brand-red)]/10">Error loading alerts: {error}</div>;
  }

  if (alerts.length === 0) {
    return (
      <div className="p-12 mt-8 text-center surface-panel max-w-2xl mx-auto">
        <div className="w-16 h-16 bg-[var(--bg-main)] rounded-full flex items-center justify-center mx-auto mb-4 border border-[var(--border-color)] shadow-[0_0_15px_var(--ring-color)]">
          <Bell className="w-8 h-8 text-[var(--color-brand-green)]" />
        </div>
        <h2 className="text-xl font-bold text-white tracking-tight mb-2">No Active Subroutines</h2>
        <p className="text-[var(--text-secondary)] max-w-md mx-auto">Create deal alerts from the Radar page to deploy automated background monitoring.</p>
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
    } catch (err) {
      alert("Failed to run alert.");
    } finally {
      setRunningAlertId(null);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-8 flex flex-col gap-8 w-full">
      <div className="flex items-center gap-4 px-4">
        <div className="bg-[var(--ring-color)] p-3 rounded-xl border border-[var(--color-brand-green)] shadow-[0_0_15px_var(--ring-color)]">
          <Bell className="w-7 h-7 text-[var(--color-brand-green)]" />
        </div>
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Active Subroutines</h1>
          <p className="text-[var(--text-secondary)] mt-1 font-mono text-sm uppercase tracking-wider">Automated Background Deal Monitoring</p>
        </div>
      </div>

      <div className="flex flex-col gap-4 px-4">
        {alerts.map((alert: any) => (
          <div key={alert.id} className="surface-panel surface-panel-hover p-6 flex flex-col md:flex-row gap-6 items-start md:items-center justify-between group">
            <div className="flex-1">
              <div className="flex flex-col gap-1.5 mb-3">
                {alert.name && (
                  <h2 className="text-lg font-bold text-[var(--color-brand-green)] mb-1">{alert.name}</h2>
                )}
                
                {alert.product_urls && alert.product_urls.length > 0 && (
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--color-brand-green)] bg-[var(--ring-color)] px-2 py-1 rounded">Wishlist</span>
                    <span className="text-sm text-white">{alert.product_urls.length} Products Monitored</span>
                  </div>
                )}
                
                {alert.categories && alert.categories.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {alert.categories.map((c: string) => (
                      <span key={c} className="text-xs font-bold uppercase tracking-widest text-indigo-400 bg-indigo-500/10 px-2 py-1 rounded border border-indigo-500/20">{c}</span>
                    ))}
                  </div>
                )}
                {alert.keywords && alert.keywords.length > 0 && (
                  <h3 className="text-xl font-bold text-white leading-tight mt-1">
                    {alert.keywords.join(", ")}
                  </h3>
                )}
                {alert.exclude_keywords && alert.exclude_keywords.length > 0 && (
                  <p className="text-xs text-[var(--color-brand-red)] mt-1 font-mono">
                    <span className="opacity-70">EXCLUDE:</span> {alert.exclude_keywords.join(", ")}
                  </p>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-3 text-sm text-[var(--text-secondary)] mt-4">
                {alert.min_discount_pct && (
                  <span className="font-bold text-[var(--color-brand-red)] bg-[var(--color-brand-red)]/10 border border-[var(--color-brand-red)]/30 px-2.5 py-1 rounded-md shadow-[0_0_8px_rgba(255,59,59,0.2)]">
                    🔥 &ge;{alert.min_discount_pct}% OFF
                  </span>
                )}
                <span className="font-medium bg-[var(--bg-main)] border border-[var(--border-color)] px-2.5 py-1 rounded-md text-white font-mono text-xs">RADAR: {alert.radius_km} km</span>
                {alert.require_in_stock && <span className="text-emerald-400 font-medium flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_5px_#34d399]"></div> IN STOCK</span>}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto mt-4 md:mt-0 pt-4 md:pt-0 border-t border-[var(--border-color)] md:border-0 justify-between md:justify-end">
              <button
                onClick={() => handleRunNow(alert.id!)}
                disabled={runningAlertId === alert.id}
                className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[var(--bg-main)] hover:bg-white hover:text-black text-white border border-[var(--border-color)] hover:border-white rounded-xl text-sm font-bold transition-all disabled:opacity-50 min-w-[120px]"
              >
                {runningAlertId === alert.id ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> EXECUTING</>
                ) : (
                  <><Activity className="w-4 h-4" /> DEPLOY NOW</>
                )}
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleAlert(alert.id!, !alert.enabled)}
                  className={`p-2.5 rounded-xl transition-all border ${
                    alert.enabled 
                      ? "bg-[var(--ring-color)] text-[var(--color-brand-green)] border-[var(--color-brand-green)] shadow-[0_0_10px_var(--ring-color)]" 
                      : "bg-[var(--bg-main)] text-[var(--text-secondary)] border-[var(--border-color)] hover:text-white"
                  }`}
                  title={alert.enabled ? "Suspend Subroutine" : "Resume Subroutine"}
                >
                  {alert.enabled ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-0.5" />}
                </button>
                <button
                  onClick={() => deleteAlert(alert.id!)}
                  className="p-2.5 bg-[var(--bg-main)] text-[var(--text-secondary)] hover:text-[var(--color-brand-red)] border border-[var(--border-color)] hover:border-[var(--color-brand-red)] rounded-xl transition-colors"
                  title="Terminate Subroutine"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
