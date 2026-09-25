import { useState, useEffect } from "react";
import { useLiveConsole } from "../../store/liveConsoleStore";
import { Bot, Loader2, Clock, Activity, AlertTriangle, CheckCircle2 } from "lucide-react";

export default function ScanProgress({
  intervalMinutes,
  isSearching,
}: {
  intervalMinutes?: number;
  isSearching: boolean;
}) {
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
      setTimeLeft(Math.max(0, Math.floor((nextScan - now) / 1000)));
    };
    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [scanState, lastScan, intervalMinutes, isSearching]);

  const formatCountdown = (s: number | null) => {
    if (s === null) return "—";
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  let phase = "READY";
  let statusText = "Ready to scan";
  let statusDesc = "Configure your targets and start tracking";

  if (isSearching) {
    if (["STARTING", "DISCOVERING_STORES", "SCANNING_PRODUCTS", "EVALUATING"].includes(scanState)) {
      phase = "SCANNING";
      switch (scanState) {
        case "STARTING":           statusText = "Starting Monitor…";             break;
        case "DISCOVERING_STORES": statusText = "Discovering nearby stores…";    break;
        case "SCANNING_PRODUCTS":  statusText = "Scanning products in stores…";  break;
        case "EVALUATING":         statusText = "Evaluating deals…";             break;
      }
      statusDesc = "Scan in progress";
    } else if (scanState === "COMPLETED") {
      if (intervalMinutes) {
        phase = "WAITING";
        statusText = "Waiting";
        statusDesc = "Next scan queued";
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

  const phaseConfig: Record<string, { iconBg: string; iconColor: string; icon: any; borderColor: string }> = {
    READY:    { iconBg: "rgba(22,163,74,0.1)",  iconColor: "var(--color-brand-green)", icon: Bot,           borderColor: "var(--border)" },
    SCANNING: { iconBg: "rgba(59,130,246,0.1)",  iconColor: "#3b82f6",                 icon: Loader2,       borderColor: "rgba(59,130,246,0.25)" },
    WAITING:  { iconBg: "rgba(168,85,247,0.1)",  iconColor: "#a855f7",                 icon: Activity,      borderColor: "rgba(168,85,247,0.25)" },
    ERROR:    { iconBg: "rgba(220,38,38,0.1)",   iconColor: "var(--color-brand-red)",  icon: AlertTriangle, borderColor: "rgba(220,38,38,0.25)" },
  };

  const cfg = phaseConfig[phase];
  const PhaseIcon = cfg.icon;

  return (
    <div
      className="card"
      style={{
        padding: "16px 20px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "16px",
        flexWrap: "wrap",
        borderColor: cfg.borderColor,
        transition: "border-color 0.3s ease",
      }}
    >
      <style>{`
        @keyframes shimmer-scan {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
        @keyframes pulse-waiting {
          0%, 100% { opacity: 0.5; }
          50%       { opacity: 1; }
        }
      `}</style>

      {/* Left: icon + status text */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px", minWidth: "220px" }}>
        <div style={{
          width: "40px",
          height: "40px",
          borderRadius: "10px",
          background: cfg.iconBg,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: cfg.iconColor,
          flexShrink: 0,
        }}>
          <PhaseIcon className={`w-5 h-5${phase === "SCANNING" ? " animate-spin" : ""}`} />
        </div>
        <div>
          <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.3 }}>
            {statusText}
          </div>
          <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
            {statusDesc}
          </div>
        </div>
      </div>

      {/* Center: progress bar */}
      <div style={{ flex: "1 1 auto", display: "flex", alignItems: "center", justifyContent: "center", minWidth: "140px" }}>
        {phase === "SCANNING" && (
          <div style={{
            position: "relative",
            height: "4px",
            width: "100%",
            maxWidth: "280px",
            background: "var(--bg-input)",
            borderRadius: "2px",
            overflow: "hidden",
          }}>
            <div style={{
              position: "absolute",
              top: 0,
              left: 0,
              height: "100%",
              width: "40%",
              background: "linear-gradient(90deg, transparent, #3b82f6, transparent)",
              animation: "shimmer-scan 1.4s infinite linear",
            }} />
          </div>
        )}
        {phase === "WAITING" && (
          <div style={{
            position: "relative",
            height: "4px",
            width: "100%",
            maxWidth: "280px",
            background: "var(--bg-input)",
            borderRadius: "2px",
            overflow: "hidden",
          }}>
            <div style={{
              position: "absolute",
              left: 0,
              top: 0,
              height: "100%",
              width: "100%",
              background: "linear-gradient(90deg, transparent, #a855f7, transparent)",
              animation: "pulse-waiting 2s ease-in-out infinite",
            }} />
          </div>
        )}
      </div>

      {/* Right: countdown / clock */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px", justifyContent: "flex-end", minWidth: "120px" }}>
        {phase === "WAITING" && (
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: "10.5px", textTransform: "uppercase", fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.07em" }}>
                Next in
              </div>
              <div style={{ fontSize: "17px", fontWeight: 800, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums", letterSpacing: "-0.03em" }}>
                {formatCountdown(timeLeft)}
              </div>
            </div>
            <div style={{
              width: "36px", height: "36px", borderRadius: "9px",
              background: "var(--bg-input)", border: "1px solid var(--border-strong)",
              display: "flex", alignItems: "center", justifyContent: "center",
              color: "#a855f7",
            }}>
              <Clock className="w-4 h-4" />
            </div>
          </div>
        )}
        {phase === "SCANNING" && lastScan && (
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "10.5px", textTransform: "uppercase", fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.07em" }}>
              Started
            </div>
            <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
              {new Date(lastScan).toLocaleTimeString()}
            </div>
          </div>
        )}
        {phase === "READY" && (
          <div style={{
            width: "36px", height: "36px", borderRadius: "9px",
            background: "var(--bg-input)", border: "1px solid var(--border)",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "var(--text-muted)",
          }}>
            <CheckCircle2 className="w-4 h-4" />
          </div>
        )}
      </div>
    </div>
  );
}
