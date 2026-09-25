import { useState, useEffect, useRef } from "react";
import { Terminal, Filter, Trash2 } from "lucide-react";
import { useLiveConsole } from "../../store/liveConsoleStore";

interface LiveConsoleProps {
  streamUrl?: string;
  alertId?: string;
}

export default function LiveConsole({ streamUrl, alertId }: LiveConsoleProps) {
  const { logs, connect, clearLogs } = useLiveConsole();
  const [filter, setFilter] = useState<string>("ALL");
  const [isAutoScroll, setIsAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const url = streamUrl || (alertId ? `/api/alerts/${alertId}/stream` : null);
    if (!url) return;
    connect(url);
    // Do NOT disconnect on unmount so the console survives navigation
  }, [alertId, streamUrl, connect]);

  useEffect(() => {
    if (isAutoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isAutoScroll]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const t = e.currentTarget;
    setIsAutoScroll(t.scrollHeight - t.scrollTop <= t.clientHeight + 10);
  };

  const filteredLogs = logs.filter(
    (l) => filter === "ALL" || l.level === filter || (filter === "DEAL" && l.level === "DEAL")
  );

  const levelColors: Record<string, string> = {
    INFO:   "#8b949e",
    WARN:   "#e3b341",
    ERROR:  "#f85149",
    DEAL:   "#3fb950",
    FILTER: "#58a6ff",
  };

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      background: "var(--bg-card)",
      borderRadius: "14px",
      border: "1px solid var(--border)",
      overflow: "hidden",
      height: "460px",
      fontFamily: "ui-monospace, 'SF Mono', Consolas, 'Liberation Mono', monospace",
    }}>

      {/* ── Header ───────────────────────────────── */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "10px 16px",
        background: "var(--bg-surface)",
        borderBottom: "1px solid var(--border)",
        flexWrap: "wrap",
        gap: "10px",
        flexShrink: 0,
      }}>
        {/* Title */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{
            width: "28px",
            height: "28px",
            borderRadius: "7px",
            background: "var(--ring-green)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <Terminal className="w-3.5 h-3.5" style={{ color: "var(--color-brand-green)" }} />
          </div>
          <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
            Live Console
          </span>
          {/* Live dot */}
          <span style={{
            display: "inline-block",
            width: "7px",
            height: "7px",
            borderRadius: "50%",
            background: "#2ea043",
            boxShadow: "0 0 8px rgba(46,160,67,0.7)",
            animation: "pulse-dot 2s ease-in-out infinite",
          }} />
        </div>

        {/* Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {/* Filter */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Filter className="w-3 h-3" style={{ color: "var(--text-muted)" }} />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{
                background: "var(--bg-surface-hover)",
                border: "1px solid var(--border)",
                color: "var(--text-primary)",
                fontSize: "12px",
                fontWeight: 500,

                padding: "3px 8px",
                borderRadius: "6px",
                outline: "none",
                cursor: "pointer",
                fontFamily: "inherit",
              }}
            >
              <option value="ALL">All Events</option>
              <option value="INFO">Info</option>
              <option value="DEAL">Deals</option>
              <option value="ERROR">Errors</option>
            </select>
          </div>

          {/* Clear button */}
          <button
            onClick={clearLogs}
            style={{
              background: "transparent",
              border: "1px solid transparent",
              color: "var(--text-muted)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "5px",
              fontSize: "12px",
              fontWeight: 500,
              padding: "3px 8px",
              borderRadius: "6px",
              transition: "all 0.15s",
              fontFamily: "inherit",
            }}
            onMouseOver={e => {
              e.currentTarget.style.color = "var(--text-primary)";
              e.currentTarget.style.borderColor = "var(--border-strong)";
              e.currentTarget.style.background = "var(--bg-surface-hover)";
            }}
            onMouseOut={e => {
              e.currentTarget.style.color = "#6e7681";
              e.currentTarget.style.borderColor = "transparent";
              e.currentTarget.style.background = "transparent";
            }}
            title="Clear Console"
          >
            <Trash2 className="w-3 h-3" />
            Clear
          </button>
        </div>
      </div>

      {/* ── Logs area ────────────────────────────── */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "14px 18px",
          display: "flex",
          flexDirection: "column",
          gap: "5px",
          fontSize: "12.5px",
          lineHeight: 1.65,
        }}
        className="custom-scrollbar"
      >
        {filteredLogs.map((log) => {
          const color = levelColors[log.level] || "#8b949e";
          const isHighlight = log.level === "DEAL" || log.level === "ERROR";
          return (
            <div
              key={log.id}
              style={{
                display: "flex",
                gap: "14px",
                alignItems: "flex-start",
                padding: isHighlight ? "4px 8px" : "1px 0",
                borderRadius: isHighlight ? "6px" : "0",
                background: log.level === "DEAL"
                  ? "rgba(63,185,80,0.07)"
                  : log.level === "ERROR"
                    ? "rgba(248,81,73,0.07)"
                    : "transparent",
              }}
            >
              <span style={{
                color: "var(--text-muted)",
                flexShrink: 0,
                fontSize: "11.5px",
                fontVariantNumeric: "tabular-nums",
                marginTop: "1px",
              }}>
                {log.time}
              </span>
              <span style={{
                color: color,
                fontWeight: 700,
                width: "46px",
                flexShrink: 0,
                fontSize: "11.5px",
                marginTop: "1px",
                letterSpacing: "0.04em",
              }}>
                {log.level}
              </span>
              <span style={{
                color: log.level === "ERROR" ? "var(--color-brand-red)" : log.level === "DEAL" ? "var(--color-brand-green)" : "var(--text-primary)",
                wordBreak: "break-word",
                overflowWrap: "anywhere",
                flex: 1,
                fontWeight: isHighlight ? 600 : 400,
              }}>
                {log.message}
              </span>
            </div>
          );
        })}

        {filteredLogs.length === 0 && (
          <div style={{
            color: "var(--text-muted)",
            textAlign: "center",
            marginTop: "60px",
            fontStyle: "italic",
            fontSize: "13px",
          }}>
            Waiting for events…
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}
