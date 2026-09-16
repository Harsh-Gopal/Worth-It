import { Loader2, CheckCircle2, AlertCircle, MapPin, Store, PackageSearch, Target } from "lucide-react";

interface SearchProgressProps {
  status: string;
  metrics: any;
  error: string | null;
}

export default function SearchProgress({ status, metrics, error }: SearchProgressProps) {
  if (status === "IDLE") return null;

  const isComplete = status === "COMPLETED";
  const hasError = !!error;

  const statCard = (icon: React.ReactNode, label: string, value: string, green = false) => (
    <div style={{
      background: "var(--bg-muted)",
      border: green ? "1px solid rgba(22,163,74,0.25)" : "1px solid var(--border)",
      borderRadius: "8px",
      padding: "12px",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
        <span style={{ color: green ? "var(--color-brand-green)" : "var(--text-muted)" }}>{icon}</span>
        <span style={{ fontSize: "10px", fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          {label}
        </span>
      </div>
      <p style={{ fontSize: "20px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>{value}</p>
    </div>
  );

  return (
    <div style={{
      background: "var(--bg-surface)",
      border: "1px solid var(--border)",
      borderRadius: "12px",
      padding: "16px",
    }}>
      <h3 style={{
        fontSize: "13px",
        fontWeight: 600,
        color: "var(--text-primary)",
        margin: "0 0 12px",
        display: "flex",
        alignItems: "center",
        gap: "6px",
      }}>
        {!isComplete && !hasError && <Loader2 className="w-4 h-4 animate-spin" style={{ color: "var(--color-brand-green)" }} />}
        {isComplete && <CheckCircle2 className="w-4 h-4" style={{ color: "var(--color-brand-green)" }} />}
        {hasError && <AlertCircle className="w-4 h-4" style={{ color: "var(--color-brand-red)" }} />}
        Search Progress
      </h3>

      {error ? (
        <div style={{
          padding: "10px 12px",
          background: "var(--ring-red)",
          border: "1px solid rgba(220,38,38,0.25)",
          borderRadius: "8px",
          display: "flex",
          gap: "8px",
          alignItems: "flex-start",
        }}>
          <AlertCircle className="w-4 h-4 shrink-0" style={{ color: "var(--color-brand-red)", marginTop: "1px" }} />
          <p style={{ fontSize: "13px", color: "var(--color-brand-red)", margin: 0 }}>{error}</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
          {statCard(<MapPin className="w-3 h-3" />, "Radius", metrics.currentRadiusKm ? `${metrics.currentRadiusKm.toFixed(1)} km` : "—")}
          {statCard(<Store className="w-3 h-3" />, "Stores", `${metrics.storesScanned}/${metrics.storesDiscovered}`)}
          {statCard(<PackageSearch className="w-3 h-3" />, "Products", String(metrics.productsFound || 0))}
          {statCard(<Target className="w-3 h-3" />, "Deals", String(metrics.dealsFound || 0), true)}
        </div>
      )}

      {!isComplete && !hasError && (
        <div style={{
          marginTop: "12px",
          paddingTop: "12px",
          borderTop: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}>
          <span style={{
            width: "6px",
            height: "6px",
            borderRadius: "50%",
            background: "var(--color-brand-green)",
            animation: "pulse 1.5s ease-in-out infinite",
            flexShrink: 0,
          }} />
          <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
            {status === "STARTING" && "Initializing scan…"}
            {status === "LOCAL_SEARCH" && "Checking local store…"}
            {status === "EXPANDING_RADIUS" && `Expanding sweep to ${metrics.currentRadiusKm} km…`}
            {status === "SCANNING_STORES" && "Scanning stores for inventory…"}
          </span>
        </div>
      )}

      <style>{`@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.4;} }`}</style>
    </div>
  );
}
