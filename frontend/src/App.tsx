import { useState, useEffect } from "react";
import WorthIt from "./pages/DealRadar";
import Alerts from "./pages/Alerts";
import Settings from "./pages/Settings";
import { Search, Bell, Settings as SettingsIcon, Sun, Moon } from "lucide-react";
import WorthItLogo from "./components/branding/WorthItLogo";

type Tab = "search" | "wishlist" | "alerts" | "settings";

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("search");

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

  const toggleTheme = () => setTheme(prev => prev === "dark" ? "light" : "dark");

  const navItems: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "search",   label: "Search",    icon: <Search className="w-[18px] h-[18px]" /> },
    { id: "alerts",   label: "My Alerts", icon: <Bell className="w-[18px] h-[18px]" /> },
    { id: "settings", label: "Settings",  icon: <SettingsIcon className="w-[18px] h-[18px]" /> },
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
          onClick={() => setActiveTab("search")}
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
        <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "32px 32px 64px" }}>
          {activeTab === "search"   && <WorthIt />}
          {activeTab === "alerts"   && <Alerts />}
          {activeTab === "settings" && <Settings />}
        </div>
      </main>
    </div>
  );
}

export default App;
