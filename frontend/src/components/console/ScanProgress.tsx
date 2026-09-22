import React, { useEffect, useState } from "react";
import { useLiveConsole } from "../../store/liveConsoleStore";

export default function ScanProgress() {
  const { scanState, lastScanTime: lastScan } = useLiveConsole();

  // Derive progress percentage and labels from scanState
  let progress = 0;
  let statusText = "Idle";
  let showAnimation = false;

  switch (scanState) {
    case "STARTING":
      progress = 10;
      statusText = "Starting Monitor...";
      showAnimation = true;
      break;
    case "DISCOVERING_STORES":
      progress = 30;
      statusText = "Discovering nearby stores...";
      showAnimation = true;
      break;
    case "SCANNING_PRODUCTS":
      progress = 60;
      statusText = "Scanning products in stores...";
      showAnimation = true;
      break;
    case "EVALUATING":
      progress = 85;
      statusText = "Evaluating deals and thresholds...";
      showAnimation = true;
      break;
    case "COMPLETED":
      progress = 100;
      statusText = "Scan Completed";
      showAnimation = false;
      break;
    case "ERROR":
      progress = 100;
      statusText = "Scan Error";
      showAnimation = false;
      break;
    case "IDLE":
    default:
      progress = 0;
      statusText = "Waiting...";
      showAnimation = false;
      break;
  }

  const formatTime = (isoString: string | null) => {
    if (!isoString) return "—";
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  return (
    <div style={{
      width: "100%",
      background: "#161b22",
      border: "1px solid #30363d",
      borderRadius: "12px",
      padding: "20px",
      fontFamily: "ui-sans-serif, system-ui, sans-serif",
      color: "var(--text-primary)"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div>
          <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "4px" }}>
            Current Scan
          </div>
          <div style={{ fontSize: "16px", fontWeight: 500, color: "var(--color-brand-green)" }}>
            {statusText}
          </div>
        </div>
      </div>

      <div style={{ position: "relative", height: "6px", background: "#30363d", borderRadius: "3px", overflow: "hidden", marginBottom: "16px" }}>
        <div style={{
          position: "absolute",
          top: 0,
          left: 0,
          height: "100%",
          width: `${progress}%`,
          background: scanState === "ERROR" ? "var(--color-brand-red)" : "var(--color-brand-green)",
          transition: "width 0.4s ease",
        }} />
        {showAnimation && (
          <div style={{
            position: "absolute",
            top: 0,
            left: 0,
            height: "100%",
            width: "100%",
            background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)",
            animation: "shimmer 1.5s infinite",
          }} />
        )}
      </div>
      
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", color: "var(--text-secondary)" }}>
        <div>
          Started: <span style={{ color: "var(--text-primary)" }}>{formatTime(lastScan)}</span>
        </div>
        <div>
          Status: <span style={{ color: scanState === "ERROR" ? "var(--color-brand-red)" : (scanState === "COMPLETED" ? "var(--color-brand-green)" : "var(--text-primary)") }}>{scanState}</span>
        </div>
      </div>
    </div>
  );
}
