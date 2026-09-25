import { useState, useEffect } from "react";
import Monitoring from "./pages/Monitoring";
import TrackHistory from "./pages/TrackHistory";
import Settings from "./pages/Settings";
import { Search, History, Settings as SettingsIcon, Sun, Moon } from "lucide-react";
import WorthItLogo from "./components/branding/WorthItLogo";

type Tab = "monitoring" | "history" | "settings";

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("monitoring");

  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("wi_theme");
      if (stored === "light" || stored === "dark") return stored;
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return "dark";
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "light") {
      root.classList.add("light");
      root.classList.remove("dark");
    } else {
      root.classList.remove("light");
      root.classList.add("dark");
    }
    localStorage.setItem("wi_theme", theme);
  }, [theme]);

  // Connect to SSE stream globally
  useEffect(() => {
    import("./store/liveConsoleStore").then(({ liveConsoleStore }) => {
      fetch("/api/alerts/primary")
        .then(res => res.json())
        .then(data => {
          if (data && data.enabled) {
            liveConsoleStore.connect("/api/alerts/primary_monitor/stream");
          }
        })
        .catch(err => console.error("Failed to check active monitor on boot", err));
    });
  }, []);

  const toggleTheme = () => setTheme(prev => prev === "dark" ? "light" : "dark");

  const navItems: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "monitoring", label: "Monitor",  icon: <Search className="w-[17px] h-[17px]" /> },
    { id: "history",    label: "History",  icon: <History className="w-[17px] h-[17px]" /> },
    { id: "settings",   label: "Settings", icon: <SettingsIcon className="w-[17px] h-[17px]" /> },
  ];

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", fontFamily: "'Inter', sans-serif" }}>

      {/* ── SIDEBAR ─────────────────────────────────────── */}
      <nav
        style={{
          width: "220px",
          flexShrink: 0,
          display: "flex",
          flexDirection: "column",
          background: "var(--sidebar-bg)",
          borderRight: "1px solid var(--sidebar-border)",
          padding: "0",
        }}
      >
        {/* Logo area */}
        <div
          style={{
            padding: "20px 16px 16px 16px",
            cursor: "pointer",
            borderBottom: "1px solid var(--sidebar-border)",
          }}
          onClick={() => setActiveTab("monitoring")}
        >
          <WorthItLogo height={26} />
        </div>

        {/* Nav section label */}
        <div style={{ padding: "20px 16px 8px 16px" }}>
          <span style={{
            fontSize: "10px",
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "var(--text-muted)",
          }}>
            Navigation
          </span>
        </div>

        {/* Nav links */}
        <div style={{ display: "flex", flexDirection: "column", gap: "2px", flex: 1, padding: "0 8px" }}>
          {navItems.map(item => {
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  width: "100%",
                  padding: "9px 12px",
                  borderRadius: "9px",
                  border: "none",
                  cursor: "pointer",
                  fontFamily: "'Inter', sans-serif",
                  fontSize: "13.5px",
                  fontWeight: active ? 600 : 500,
                  color: active ? "var(--nav-active-text)" : "var(--nav-inactive-text)",
                  background: active ? "var(--nav-active-bg)" : "transparent",
                  transition: "all 0.15s ease",
                  textAlign: "left",
                  position: "relative",
                  letterSpacing: active ? "-0.01em" : "0",
                }}
                onMouseEnter={e => {
                  if (!active) (e.currentTarget as HTMLElement).style.background = "var(--nav-hover-bg)";
                  if (!active) (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.background = active ? "var(--nav-active-bg)" : "transparent";
                  (e.currentTarget as HTMLElement).style.color = active ? "var(--nav-active-text)" : "var(--nav-inactive-text)";
                }}
              >
                {/* Active indicator dot */}
                {active && (
                  <span style={{
                    position: "absolute",
                    left: "4px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    width: "3px",
                    height: "18px",
                    borderRadius: "2px",
                    background: "var(--color-brand-green)",
                  }} />
                )}
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Bottom: Theme toggle */}
        <div style={{ padding: "12px 8px 20px 8px", borderTop: "1px solid var(--sidebar-border)" }}>
          <button
            onClick={toggleTheme}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              width: "100%",
              padding: "9px 12px",
              borderRadius: "9px",
              border: "none",
              cursor: "pointer",
              fontFamily: "'Inter', sans-serif",
              fontSize: "13.5px",
              fontWeight: 500,
              color: "var(--nav-inactive-text)",
              background: "transparent",
              transition: "all 0.15s ease",
              textAlign: "left",
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.background = "var(--nav-hover-bg)";
              (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.background = "transparent";
              (e.currentTarget as HTMLElement).style.color = "var(--nav-inactive-text)";
            }}
          >
            {theme === "dark"
              ? <Sun className="w-[17px] h-[17px]" />
              : <Moon className="w-[17px] h-[17px]" />
            }
            <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
          </button>
        </div>
      </nav>

      {/* ── MAIN CONTENT ───────────────────────────────── */}
      <main
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          background: "var(--bg-page)",
        }}
      >
        <div key={activeTab} style={{ animation: "fadeIn 0.22s ease-out both" }}>
          {activeTab === "monitoring" && <Monitoring />}
          {activeTab === "history" && <TrackHistory />}
          {activeTab === "settings" && <Settings />}
        </div>
      </main>
    </div>
  );
}

export default App;
