import { useState, useEffect, useRef } from "react";
import { Terminal, Filter, Trash2 } from "lucide-react";
import { useLiveConsole } from "../../store/liveConsoleStore";

interface LiveConsoleProps {
  streamUrl?: string;
  alertId?: string; // Kept for backwards compatibility if needed later
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
    
    // We do NOT disconnect on unmount so the console survives page navigation!
  }, [alertId, streamUrl, connect]);



  // Auto-scroll
  useEffect(() => {
    if (isAutoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isAutoScroll]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const isAtBottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 10;
    setIsAutoScroll(isAtBottom);
  };

  const filteredLogs = logs.filter(
    (l) => filter === "ALL" || l.level === filter || (filter === "DEAL" && l.level === "DEAL")
  );

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      background: "var(--bg-input)",
      borderRadius: "16px",
      border: "1px solid var(--border-strong)",
      boxShadow: "inset 0 2px 10px rgba(0, 0, 0, 0.2)",
      overflow: "hidden",
      height: "480px",
      fontFamily: "ui-monospace, SFMono-Regular, Consolas, monospace",
      width: "100%",
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 20px",
        background: "var(--bg-surface)",
        borderBottom: "1px solid var(--border-strong)",
        color: "var(--text-primary)",
        flexWrap: "wrap",
        gap: "12px"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "14px", fontWeight: 600 }}>
          <Terminal className="w-4 h-4 text-[#8b949e]" />
          Live Console
          <span style={{ 
            display: "inline-block", 
            width: "8px", 
            height: "8px", 
            borderRadius: "50%", 
            background: "#2ea043",
            boxShadow: "0 0 8px rgba(46, 160, 67, 0.6)",
            marginLeft: "2px"
          }} />
        </div>
        
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Filter className="w-3.5 h-3.5 text-[#8b949e]" />
            <select 
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid #30363d",
                color: "#c9d1d9",
                fontSize: "12px",
                fontWeight: 500,
                padding: "4px 8px",
                borderRadius: "6px",
                outline: "none",
                cursor: "pointer",
              }}
            >
              <option value="ALL">All Events</option>
              <option value="INFO">Info</option>
              <option value="DEAL">Deals</option>
              <option value="ERROR">Errors</option>
            </select>
          </div>
          
          <button 
            onClick={clearLogs}
            style={{
              background: "transparent",
              border: "1px solid transparent",
              color: "#8b949e",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "12px",
              fontWeight: 500,
              padding: "4px 8px",
              borderRadius: "6px",
              transition: "all 0.2s",
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.color = "#c9d1d9";
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.color = "#8b949e";
              e.currentTarget.style.background = "transparent";
            }}
            title="Clear Console"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear</span>
          </button>
        </div>
      </div>

      {/* Logs Area */}
      <div 
        ref={scrollRef}
        onScroll={handleScroll}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px 24px",
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          fontSize: "13px",
          lineHeight: 1.6,
        }}
      >
        {filteredLogs.map((log) => {
          let color = "#c9d1d9";
          if (log.level === "ERROR") color = "#f85149";
          if (log.level === "WARN") color = "#d29922";
          if (log.level === "DEAL") color = "#3fb950";
          if (log.level === "FILTER") color = "#58a6ff";

          return (
            <div key={log.id} style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
              <span style={{ color: "#8b949e", flexShrink: 0, opacity: 0.8, fontSize: "12px", marginTop: "2px" }}>{log.time}</span>
              <span style={{ 
                color: color, 
                fontWeight: log.level === "DEAL" ? 700 : 600,
                width: "52px",
                flexShrink: 0,
                fontSize: "12px",
                marginTop: "2px",
              }}>
                {log.level}
              </span>
              <span style={{ 
                color: log.level === "ERROR" ? "#f85149" : "#c9d1d9", 
                wordBreak: "break-word",
                overflowWrap: "anywhere",
                flex: 1,
              }}>
                {log.message}
              </span>
            </div>
          );
        })}
        {filteredLogs.length === 0 && (
          <div style={{ color: "#8b949e", textAlign: "center", marginTop: "40px", fontStyle: "italic" }}>
            Waiting for events...
          </div>
        )}
      </div>
    </div>
  );
}
