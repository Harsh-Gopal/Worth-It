import { useState, useEffect } from "react";
import Monitoring from "./pages/Monitoring";
import TrackHistory from "./pages/TrackHistory";
import Settings from "./pages/Settings";
import { Search, History, Bell, Settings as SettingsIcon, Sun, Moon } from "lucide-react";
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
    return "light";
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("wi_theme", theme);
  }, [theme]);

  // Connect to SSE stream globally so it's active even if Monitoring tab is never opened
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
    { id: "monitoring", label: "Monitor",  icon: <Search className="w-[18px] h-[18px]" /> },
    { id: "history",    label: "History",  icon: <History className="w-[18px] h-[18px]" /> },
    { id: "settings",   label: "Settings", icon: <SettingsIcon className="w-[18px] h-[18px]" /> },
  ];

  return (
    <div className="flex h-screen overflow-hidden" style={{ fontFamily: "'Inter', sans-serif" }}>

      {/* ── SIDEBAR ───────────────────────────────────── */}
      <nav
        style={{
          width: "240px",
          flexShrink: 0,
          display: "flex",
          flexDirection: "column",
          background: "var(--sidebar-bg)",
          borderRight: "1px solid var(--sidebar-border)",
          padding: "20px 12px",
          gap: 0,
        }}
      >
        {/* Logo */}
        <div
          style={{ padding: "0 8px 24px 8px", cursor: "pointer" }}
          onClick={() => setActiveTab("monitoring")}
        >
          <WorthItLogo height={28} />
        </div>

        {/* Nav links */}
        <div style={{ display: "flex", flexDirection: "column", gap: "2px", flex: 1 }}>
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
                  borderRadius: "8px",
                  border: "none",
                  cursor: "pointer",
                  fontFamily: "'Inter', sans-serif",
                  fontSize: "14px",
                  fontWeight: active ? 600 : 500,
                  color: active ? "var(--nav-active-text)" : "var(--nav-inactive-text)",
                  background: active ? "var(--nav-active-bg)" : "transparent",
                  transition: "all 0.15s ease",
                  textAlign: "left",
                }}
                onMouseEnter={e => {
                  if (!active) (e.currentTarget as HTMLElement).style.background = "var(--nav-hover-bg)";
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.background = active ? "var(--nav-active-bg)" : "transparent";
                }}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Theme toggle at bottom */}
        <button
          onClick={toggleTheme}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            width: "100%",
            padding: "9px 12px",
            borderRadius: "8px",
            border: "none",
            cursor: "pointer",
            fontFamily: "'Inter', sans-serif",
            fontSize: "14px",
            fontWeight: 500,
            color: "var(--nav-inactive-text)",
            background: "transparent",
            transition: "all 0.15s ease",
            textAlign: "left",
          }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "var(--nav-hover-bg)"; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}
        >
          {theme === "dark"
            ? <Sun className="w-[18px] h-[18px]" />
            : <Moon className="w-[18px] h-[18px]" />
          }
          <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
        </button>
      </nav>

      {/* ── MAIN CONTENT ──────────────────────────────── */}
      <main
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          background: "var(--bg-page)",
        }}
      >
        <div className="tab-content" style={{ animation: "fadeIn 0.2s ease-in-out" }}>
          {activeTab === "monitoring" && <Monitoring />}
          {activeTab === "history" && <TrackHistory />}
          {activeTab === "settings" && <Settings />}
        </div>
      </main>
    </div>
  );
}

export default App;
