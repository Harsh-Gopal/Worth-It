import { useState, useEffect } from "react";
import { API_BASE } from "./lib/api";
import Monitoring from "./pages/Monitoring";
import TrackHistory from "./pages/TrackHistory";
import Settings from "./pages/Settings";
import { History, Settings as SettingsIcon, Sun, Moon, Activity } from "lucide-react";
import WorthItLogo from "./components/branding/WorthItLogo";
import { AuthModal } from "./components/auth/AuthModal";
import { useAuthStore } from "./store/authStore";

type Tab = "monitoring" | "history" | "settings";

function App() {
  const [activeTab, setActiveTab] = useState<Tab>("monitoring");
  const { setLocked, setSecurityEnabled } = useAuthStore();
  const [appVersion, setAppVersion] = useState<string>("Version Loading...");

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(res => res.json())
      .then(data => {
        if (data.version) {
          const commit = data.git_commit && data.git_commit !== "unknown" ? ` (${data.git_commit})` : "";
          setAppVersion(`${data.version}${commit}`);
        }
      })
      .catch(() => setAppVersion("Version Unknown"));
  }, []);

  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("wi_theme");
      if (stored === "light" || stored === "dark") return stored;
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return "dark";
  });

  useEffect(() => {
    // Check initial auth status
    const checkAuthStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/status`);
        if (res.ok) {
          const data = await res.json();
          setLocked(!data.is_unlocked);
          setSecurityEnabled(data.security_enabled);
        }
      } catch (e) {
        console.error("Failed to check auth status:", e);
      }
    };
    checkAuthStatus();
  }, [setLocked, setSecurityEnabled]);

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
      fetch(`${API_BASE}/alerts/primary`)
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
    { id: "monitoring", label: "Monitor",  icon: <Activity size={18} strokeWidth={2} /> },
    { id: "history",    label: "History",  icon: <History size={18} strokeWidth={2} /> },
    { id: "settings",   label: "Settings", icon: <SettingsIcon size={18} strokeWidth={2} /> },
  ];

  return (
    <div className="flex h-screen overflow-hidden font-sans flex-col md:flex-row w-full bg-[var(--bg-page)] text-[var(--text-primary)]">
      
      {/* ── MOBILE HEADER ───────────────────────────────── */}
      <header className="flex md:hidden items-center justify-between px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-surface)] shrink-0 z-40">
        <WorthItLogo height={22} />
        <button
          onClick={toggleTheme}
          className="p-1.5 rounded-md hover:bg-[var(--nav-hover-bg)] text-[var(--nav-inactive-text)] hover:text-[var(--text-primary)] transition-colors"
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </header>

      {/* ── DESKTOP SIDEBAR ─────────────────────────────────────── */}
      <nav
        className="hidden md:flex flex-col w-[220px] shrink-0 bg-[var(--sidebar-bg)] border-r border-[var(--sidebar-border)] p-0"
      >
        {/* Logo area */}
        <div
          className="pt-5 pb-4 px-4 cursor-pointer border-b border-[var(--sidebar-border)]"
          onClick={() => setActiveTab("monitoring")}
        >
          <WorthItLogo height={26} />
        </div>

        {/* Nav section label */}
        <div className="pt-5 px-4 pb-2">
          <span className="text-[10px] font-bold tracking-[0.08em] uppercase text-[var(--text-muted)]">
            Navigation
          </span>
        </div>

        {/* Nav links */}
        <div className="flex flex-col gap-[2px] flex-1 px-2">
          {navItems.map(item => {
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-[10px] w-full px-3 py-[9px] rounded-[9px] cursor-pointer text-[13.5px] font-medium transition-all relative tracking-[-0.01em] border-none text-left ${active ? 'font-semibold text-[var(--nav-active-text)] bg-[var(--nav-active-bg)]' : 'text-[var(--nav-inactive-text)] bg-transparent hover:bg-[var(--nav-hover-bg)] hover:text-[var(--text-primary)]'}`}
              >
                {/* Active indicator dot */}
                {active && (
                  <span className="absolute left-[4px] top-1/2 -translate-y-1/2 w-[3px] h-[18px] rounded-[2px] bg-[var(--color-brand-green)]" />
                )}
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Bottom: Theme toggle & Version */}
        <div className="pt-3 pb-5 px-2 border-t border-[var(--sidebar-border)]">
          <button
            onClick={toggleTheme}
            className="flex items-center gap-[10px] w-full px-3 py-[9px] rounded-[9px] cursor-pointer text-[13.5px] font-medium text-[var(--nav-inactive-text)] bg-transparent transition-all border-none text-left hover:bg-[var(--nav-hover-bg)] hover:text-[var(--text-primary)]"
          >
            {theme === "dark"
              ? <Sun size={18} strokeWidth={2} />
              : <Moon size={18} strokeWidth={2} />
            }
            <span>{theme === "dark" ? "Light Mode" : "Dark Mode"}</span>
          </button>
          
          {/* App Version */}
          <div className="mt-3 px-3 text-[10px] text-[var(--text-muted)] text-center opacity-70">
            {appVersion}
          </div>
        </div>
      </nav>

      {/* ── MAIN CONTENT ───────────────────────────────── */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden bg-[var(--bg-page)] pb-[calc(60px+env(safe-area-inset-bottom))] md:pb-0">
        <div key={activeTab} className="animate-fade-in">
          {activeTab === "monitoring" && <Monitoring />}
          {activeTab === "history" && <TrackHistory />}
          {activeTab === "settings" && <Settings />}
        </div>
      </main>

      {/* ── MOBILE BOTTOM NAVIGATION ───────────────────── */}
      <nav className="flex md:hidden fixed bottom-0 left-0 right-0 bg-[var(--sidebar-bg)] border-t border-[var(--sidebar-border)] z-50 px-2 justify-around items-center" style={{ paddingBottom: "env(safe-area-inset-bottom)", height: "calc(60px + env(safe-area-inset-bottom))" }}>
        {navItems.map(item => {
          const active = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex flex-col items-center justify-center w-full h-[60px] gap-1 cursor-pointer transition-colors border-none bg-transparent ${active ? 'text-[var(--color-brand-green)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'}`}
            >
              {item.icon}
              <span className="text-[10px] font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <AuthModal />
    </div>
  );
}

export default App;
