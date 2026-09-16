import type { SearchStatus, SearchMetrics } from "../../hooks/useDealSearch";
import { CheckCircle2, AlertCircle, XCircle } from "lucide-react";

interface SearchProgressProps {
  status: SearchStatus;
  metrics: SearchMetrics;
  error?: string | null;
}

export default function SearchProgress({ status, metrics, error }: SearchProgressProps) {
  if (status === "IDLE") return null;

  const isScanning = ["STARTING", "LOCAL_SEARCH", "EXPANDING_RADIUS", "SCANNING_STORES"].includes(status);
  const isError = status === "ERROR" || status === "CANCELLED";
  const isDone = status === "COMPLETED";

  const statusText = {
    STARTING: "Initializing search…",
    LOCAL_SEARCH: "Checking your local store…",
    EXPANDING_RADIUS: `Expanding search to ${metrics.currentRadiusKm} km…`,
    SCANNING_STORES: "Scanning discovered stores…",
    DEAL_FOUND: "Deals found! Scanning remaining stores…",
    COMPLETED: metrics.dealsFound > 0 ? "Search completed." : "Search completed. No qualifying deals found.",
    CANCELLED: "Search cancelled.",
    ERROR: "Search failed.",
  }[status] || status;

  return (
    <div style={{
      background: "var(--bg-surface)",
      border: "1px solid var(--border)",
      borderRadius: "10px",
      padding: "14px",
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
        paddingBottom: "12px",
        borderBottom: "1px solid var(--border)",
        marginBottom: "12px",
      }}>
        {isScanning && (
          <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "var(--color-brand-green)", display: "inline-block", flexShrink: 0, animation: "pulse 1.5s ease-in-out infinite" }} />
        )}
        {isError && <XCircle className="w-4 h-4 shrink-0" style={{ color: "var(--color-brand-red)" }} />}
        {isDone && <CheckCircle2 className="w-4 h-4 shrink-0" style={{ color: "var(--color-brand-green)" }} />}
        <span style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-primary)" }}>
          {statusText}
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "13px" }}>
        {[
          { label: "Discovered", value: String(metrics.storesDiscovered) },
          { label: "Scanned", value: `${metrics.storesScanned} / ${metrics.storesDiscovered}` },
          { label: "Products", value: String(metrics.productsFound) },
          { label: "Deals", value: String(metrics.dealsFound), highlight: metrics.dealsFound > 0 },
        ].map(({ label, value, highlight }) => (
          <div key={label}>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "2px" }}>{label}</div>
            <div style={{ fontWeight: 600, color: highlight ? "var(--color-brand-green)" : "var(--text-primary)" }}>
              {value}
            </div>
          </div>
        ))}
      </div>

      {error && (
        <div style={{
          marginTop: "10px",
          padding: "8px 10px",
          background: "var(--ring-red)",
          border: "1px solid rgba(220,38,38,0.25)",
          borderRadius: "6px",
          display: "flex",
          gap: "6px",
          alignItems: "flex-start",
        }}>
          <AlertCircle className="w-4 h-4 shrink-0" style={{ color: "var(--color-brand-red)", marginTop: "1px" }} />
          <p style={{ fontSize: "12px", color: "var(--color-brand-red)", margin: 0 }}>{error}</p>
        </div>
      )}

      {isDone && metrics.elapsedTimeMs && (
        <div style={{ marginTop: "8px", fontSize: "11px", color: "var(--text-muted)", textAlign: "right" }}>
          Took {(metrics.elapsedTimeMs / 1000).toFixed(1)}s
        </div>
      )}

      <style>{`@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.4;} }`}</style>
    </div>
  );
}
