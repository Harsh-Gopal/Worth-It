import { useState, useEffect } from "react";
import WorthIt from "./pages/DealRadar";
import Alerts from "./pages/Alerts";
import Settings from "./pages/Settings";
import { Radar, Settings as SettingsIcon, Bell, Sun, Moon } from "lucide-react";

function App() {
  const [activeTab, setActiveTab] = useState<"search" | "alerts" | "settings">("search");
  
  // Theme state
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("theme");
      if (stored === "light" || stored === "dark") return stored;
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return "dark";
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === "dark" ? "light" : "dark");
  };

  return (
    <div className="flex h-screen overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <nav className="w-20 md:w-64 flex flex-col items-center md:items-start surface-panel rounded-none border-t-0 border-b-0 border-l-0 py-6 z-10">
        <div className="flex items-center gap-3 px-0 md:px-6 mb-10 cursor-pointer" onClick={() => setActiveTab("search")}>
          <div className="flex items-center gap-3">
            <img src="/logo.svg" alt="Worth-It Logo" className="w-auto h-8" />
          </div>
        </div>
        
        <div className="flex flex-col w-full gap-2 px-3 md:px-4 flex-1">
          <button
            onClick={() => setActiveTab("search")}
            className={`flex items-center justify-center md:justify-start gap-3 w-full p-3 rounded-xl transition-all ${
              activeTab === "search" 
                ? "bg-[var(--bg-surface-hover)] text-[var(--text-primary)] font-bold shadow-sm" 
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)] font-medium"
            }`}
          >
            <Radar className="w-5 h-5" />
            <span className="hidden md:block">Search</span>
          </button>
          
          <button
            onClick={() => setActiveTab("alerts")}
            className={`flex items-center justify-center md:justify-start gap-3 w-full p-3 rounded-xl transition-all ${
              activeTab === "alerts" 
                ? "bg-[var(--bg-surface-hover)] text-[var(--text-primary)] font-bold shadow-sm" 
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)] font-medium"
            }`}
          >
            <Bell className="w-5 h-5" />
            <span className="hidden md:block">My Alerts</span>
          </button>
          
          <button
            onClick={() => setActiveTab("settings")}
            className={`flex items-center justify-center md:justify-start gap-3 w-full p-3 rounded-xl transition-all ${
              activeTab === "settings" 
                ? "bg-[var(--bg-surface-hover)] text-[var(--text-primary)] font-bold shadow-sm" 
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)] font-medium"
            }`}
          >
            <SettingsIcon className="w-5 h-5" />
            <span className="hidden md:block">Settings</span>
          </button>
        </div>

        {/* Theme Toggle */}
        <div className="mt-auto w-full px-3 md:px-4">
          <button
            onClick={toggleTheme}
            className="flex items-center justify-center md:justify-start gap-3 w-full p-3 rounded-xl transition-all text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)] font-medium"
          >
            {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            <span className="hidden md:block">{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 h-full overflow-y-auto overflow-x-hidden relative bg-[var(--bg-main)]">
        <div className="relative z-10 p-6 md:p-8 max-w-7xl mx-auto min-h-full">
          {activeTab === "search" && <WorthIt />}
          {activeTab === "alerts" && <Alerts />}
          {activeTab === "settings" && <Settings />}
        </div>
      </main>
    </div>
  );
}

export default App;
