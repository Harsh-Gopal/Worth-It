import { useState } from "react";
import WorthIt from "./pages/DealRadar";
import Alerts from "./pages/Alerts";
import Settings from "./pages/Settings";
import { Radar, Settings as SettingsIcon, Bell } from "lucide-react";

function App() {
  const [activeTab, setActiveTab] = useState<"search" | "alerts" | "settings">("search");

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-radar-bg)] font-sans text-white">
      {/* Sidebar Navigation */}
      <nav className="w-20 md:w-64 flex flex-col items-center md:items-start bg-[var(--color-radar-panel)] border-r border-[var(--color-radar-border)] py-6 shadow-2xl z-10 transition-all duration-300">
        <div className="flex items-center gap-3 px-0 md:px-6 mb-10 cursor-pointer" onClick={() => setActiveTab("search")}>
          <div className="flex items-center gap-3">
            <img src="/logo.svg" alt="Worth-It Logo" className="w-auto h-8" />
          </div>
        </div>
        
        <div className="flex flex-col w-full gap-2 px-3 md:px-4">
          <button
            onClick={() => setActiveTab("search")}
            className={`flex items-center justify-center md:justify-start gap-3 w-full p-3 rounded-xl transition-all ${
              activeTab === "search" 
                ? "bg-[var(--color-radar-border)] text-white shadow-md border-l-4 border-[var(--color-neon-green)]" 
                : "text-[var(--color-text-muted)] hover:text-white hover:bg-[var(--color-radar-panel-light)] border-l-4 border-transparent"
            }`}
            title="Radar Search"
          >
            <Radar className="w-5 h-5" />
            <span className="hidden md:block font-medium">Search</span>
          </button>
          
          <button
            onClick={() => setActiveTab("alerts")}
            className={`flex items-center justify-center md:justify-start gap-3 w-full p-3 rounded-xl transition-all ${
              activeTab === "alerts" 
                ? "bg-[var(--color-radar-border)] text-white shadow-md border-l-4 border-[var(--color-neon-green)]" 
                : "text-[var(--color-text-muted)] hover:text-white hover:bg-[var(--color-radar-panel-light)] border-l-4 border-transparent"
            }`}
            title="Active Alerts"
          >
            <Bell className="w-5 h-5" />
            <span className="hidden md:block font-medium">My Alerts</span>
          </button>
          
          <button
            onClick={() => setActiveTab("settings")}
            className={`flex items-center justify-center md:justify-start gap-3 w-full p-3 rounded-xl transition-all ${
              activeTab === "settings" 
                ? "bg-[var(--color-radar-border)] text-white shadow-md border-l-4 border-[var(--color-neon-green)]" 
                : "text-[var(--color-text-muted)] hover:text-white hover:bg-[var(--color-radar-panel-light)] border-l-4 border-transparent"
            }`}
            title="System Settings"
          >
            <SettingsIcon className="w-5 h-5" />
            <span className="hidden md:block font-medium">Settings</span>
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 h-full overflow-y-auto overflow-x-hidden relative">
        <div className="absolute inset-0 pointer-events-none" style={{
          background: 'radial-gradient(circle at center, transparent 0%, var(--color-radar-bg) 100%)'
        }}></div>
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
