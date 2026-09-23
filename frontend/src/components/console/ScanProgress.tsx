
import { useState, useEffect } from "react";
import { useLiveConsole } from "../../store/liveConsoleStore";
import { Bot, Loader2, Clock, Activity, AlertTriangle, CheckCircle2 } from "lucide-react";

export default function ScanProgress({ intervalMinutes, isSearching }: { intervalMinutes?: number, isSearching: boolean }) {
  const { scanState, lastScanTime: lastScan } = useLiveConsole();
  const [timeLeft, setTimeLeft] = useState<number | null>(null);

  useEffect(() => {
    if (!isSearching || scanState !== "COMPLETED" || !lastScan || !intervalMinutes) {
      setTimeLeft(null);
      return;
    }

    const updateTimer = () => {
      const nextScan = new Date(lastScan).getTime() + intervalMinutes * 60000;
      const now = new Date().getTime();
      const diff = Math.max(0, Math.floor((nextScan - now) / 1000));
      setTimeLeft(diff);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [scanState, lastScan, intervalMinutes]);

  const formatCountdown = (seconds: number | null) => {
    if (seconds === null) return "—";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  let phase = "READY";
  let statusText = "Ready to scan";
  let statusDesc = "Configure your targets and start tracking";
  
  if (isSearching) {
    if (["STARTING", "DISCOVERING_STORES", "SCANNING_PRODUCTS", "EVALUATING"].includes(scanState)) {
      phase = "SCANNING";
      switch (scanState) {
        case "STARTING": statusText = "Starting Monitor..."; break;
        case "DISCOVERING_STORES": statusText = "Discovering nearby stores..."; break;
        case "SCANNING_PRODUCTS": statusText = "Scanning products in stores..."; break;
        case "EVALUATING": statusText = "Evaluating deals and thresholds..."; break;
      }
      statusDesc = "Scan in progress...";
    } else if (scanState === "COMPLETED") {
      if (intervalMinutes) {
        phase = "WAITING";
        statusText = "Idle";
        statusDesc = "Waiting for next scan...";
      } else {
        phase = "READY";
        statusText = "Scan Complete";
        statusDesc = "Ready for another scan";
      }
    } else if (scanState === "ERROR") {
      phase = "ERROR";
      statusText = "Scan Error";
      statusDesc = "An error occurred during the scan";
    }
  }

  return (
    <div className="card" style={{
      width: "100%",
      padding: "16px 24px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "24px",
      flexWrap: "wrap",
      minHeight: "88px"
    }}>
      <style>{`
        @keyframes shimmer-indeterminate {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
        @keyframes flow-left {
          0% { transform: translateX(-100%); opacity: 0; }
          40% { transform: translateX(0%); opacity: 1; }
          60% { transform: translateX(0%); opacity: 1; }
          100% { transform: translateX(0%); opacity: 0; }
        }
        @keyframes flow-right {
          0% { transform: translateX(100%); opacity: 0; }
          40% { transform: translateX(0%); opacity: 1; }
          60% { transform: translateX(0%); opacity: 1; }
          100% { transform: translateX(0%); opacity: 0; }
        }
      `}</style>

      {/* Left Area: Icon & Status Text */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px", minWidth: "240px" }}>
        {(phase === "READY" || phase === "COMPLETED") && (
          <div style={{ padding: "10px", background: "rgba(34, 197, 94, 0.1)", borderRadius: "12px", color: "var(--color-brand-green)" }}>
            <Bot className="w-6 h-6" />
          </div>
        )}
        
        {phase === "SCANNING" && (
          <div style={{ padding: "10px", background: "rgba(59, 130, 246, 0.1)", borderRadius: "12px", color: "#3b82f6" }}>
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        )}

        {phase === "WAITING" && (
          <div style={{ padding: "10px", background: "rgba(168, 85, 247, 0.1)", borderRadius: "12px", color: "#a855f7" }}>
            <Activity className="w-6 h-6" />
          </div>
        )}

        {phase === "ERROR" && (
          <div style={{ padding: "10px", background: "rgba(239, 68, 68, 0.1)", borderRadius: "12px", color: "var(--color-brand-red)" }}>
            <AlertTriangle className="w-6 h-6" />
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column" }}>
          <span style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "2px" }}>{statusText}</span>
          <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>{statusDesc}</span>
        </div>
      </div>

      {/* Center Area: Animations */}
      <div style={{ flex: "1 1 auto", display: "flex", justifyContent: "center", alignItems: "center", minWidth: "200px" }}>
        
        {phase === "SCANNING" && (
          <div style={{ position: "relative", height: "6px", width: "100%", maxWidth: "340px", background: "var(--bg-input)", borderRadius: "3px", overflow: "hidden", border: "1px solid var(--border-strong)" }}>
            <div style={{
              position: "absolute", top: 0, left: 0, height: "100%", width: "50%",
              background: "linear-gradient(90deg, transparent, #3b82f6, transparent)",
              animation: "shimmer-indeterminate 1.5s infinite linear"
            }} />
          </div>
        )}

        {phase === "WAITING" && (
          <div style={{ position: "relative", height: "6px", width: "100%", maxWidth: "340px", background: "var(--bg-input)", borderRadius: "3px", overflow: "hidden", border: "1px solid var(--border-strong)" }}>
            <div style={{
              position: "absolute", left: 0, top: 0, bottom: 0, width: "50%",
              background: "linear-gradient(90deg, transparent, #a855f7)",
              animation: "flow-left 2s infinite ease-in-out"
            }} />
            <div style={{
              position: "absolute", right: 0, top: 0, bottom: 0, width: "50%",
              background: "linear-gradient(-90deg, transparent, #a855f7)",
              animation: "flow-right 2s infinite ease-in-out"
            }} />
          </div>
        )}

      </div>

      {/* Right Area: Timers & Stats */}
      <div style={{ minWidth: "180px", display: "flex", justifyContent: "flex-end" }}>
        {phase === "WAITING" && (
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: "11px", textTransform: "uppercase", fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "0.5px" }}>Next scan in</div>
              <div style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)" }}>{formatCountdown(timeLeft)}</div>
            </div>
            <div style={{ padding: "10px", background: "var(--bg-input)", border: "1px solid var(--border-strong)", borderRadius: "12px", color: "var(--text-primary)" }}>
              <Clock className="w-5 h-5" />
            </div>
          </div>
        )}
        
        {phase === "SCANNING" && lastScan && (
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
             <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: "11px", textTransform: "uppercase", fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "0.5px" }}>Started</div>
              <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-primary)" }}>{new Date(lastScan).toLocaleTimeString()}</div>
            </div>
          </div>
        )}

        {phase === "READY" && (
           <div style={{ padding: "10px", background: "var(--bg-input)", border: "1px solid var(--border-strong)", borderRadius: "12px", color: "var(--text-muted)" }}>
             <CheckCircle2 className="w-5 h-5" />
           </div>
        )}
      </div>

    </div>
  );
}
