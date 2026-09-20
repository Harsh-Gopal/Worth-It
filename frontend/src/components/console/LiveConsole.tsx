import { useState, useEffect, useRef } from "react";
import { Terminal, Filter, Trash2 } from "lucide-react";
import { useLiveConsole, type LogEvent } from "../../store/liveConsoleStore";

interface LiveConsoleProps {
  streamUrl?: string;
  alertId?: string; // Kept for backwards compatibility if needed later
}

export default function LiveConsole({ streamUrl, alertId }: LiveConsoleProps) {
  const { logs, connect, disconnect, clearLogs } = useLiveConsole();
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
      background: "#0d1117",
      borderRadius: "12px",
      border: "1px solid #30363d",
      overflow: "hidden",
      height: "400px",
      fontFamily: "ui-monospace, SFMono-Regular, Consolas, monospace",
    }}>
      {/* Header */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "8px 16px",
        background: "#161b22",
        borderBottom: "1px solid #30363d",
        color: "#c9d1d9",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", fontWeight: 600 }}>
          <Terminal className="w-4 h-4" />
          Live Console
          <span style={{ 
            display: "inline-block", 
            width: "8px", 
            height: "8px", 
            borderRadius: "50%", 
            background: "#2ea043",
            boxShadow: "0 0 8px #2ea043"
          }} />
        </div>
        
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <Filter className="w-3 h-3 text-muted" />
            <select 
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{
                background: "transparent",
                border: "none",
                color: "#8b949e",
                fontSize: "12px",
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
              background: "none",
              border: "none",
              color: "#8b949e",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
            }}
            title="Clear Console"
          >
            <Trash2 className="w-4 h-4" />
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
          padding: "12px 16px",
          display: "flex",
          flexDirection: "column",
          gap: "4px",
          fontSize: "13px",
        }}
      >
        {filteredLogs.map((log) => {
          let color = "#c9d1d9";
          if (log.level === "ERROR") color = "#f85149";
          if (log.level === "WARN") color = "#d29922";
          if (log.level === "DEAL") color = "#3fb950";
          if (log.level === "FILTER") color = "#58a6ff";

          return (
            <div key={log.id} style={{ display: "flex", gap: "12px", lineHeight: 1.5 }}>
              <span style={{ color: "#8b949e", flexShrink: 0 }}>{log.time}</span>
              <span style={{ 
                color: color, 
                fontWeight: log.level === "DEAL" ? 700 : 500,
                width: "48px",
                flexShrink: 0,
              }}>
                {log.level}
              </span>
              <span style={{ color: log.level === "ERROR" ? "#f85149" : "#c9d1d9", wordBreak: "break-word" }}>
                {log.message}
              </span>
            </div>
          );
        })}
        {filteredLogs.length === 0 && (
          <div style={{ color: "#8b949e", fontStyle: "italic" }}>No logs matching filter...</div>
        )}
      </div>
    </div>
  );
}
