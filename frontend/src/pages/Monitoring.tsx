import { useState, useEffect } from "react";
import { API_BASE } from "../lib/api";
import ProductSearch from "../components/search/ProductSearch";
import WorthItHero from "../components/monitor/WorthItHero";
import LiveConsole from "../components/console/LiveConsole";
import { liveConsoleStore } from "../store/liveConsoleStore";
import { Loader2, AlertCircle } from "lucide-react";

export default function Monitoring() {
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialConfig, setInitialConfig] = useState<any>(null);
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);

  useEffect(() => {
    const fetchActiveMonitor = async () => {
      try {
        const res = await fetch(`${API_BASE}/alerts/primary`);
        if (res.ok) {
          const data = await res.json();
          setInitialConfig(data);
          if (data.enabled) {
            setIsSearching(true);
            setStreamUrl(`/api/alerts/primary_monitor/stream`);
          }
        }
      } catch (err) {
        console.error("Failed to fetch active monitor", err);
      } finally {
        setIsLoadingConfig(false);
      }
    };
    fetchActiveMonitor();
  }, []);

  const handleSearch = async (req: any) => {
    setIsSearching(true);
    setError(null);
    try {
      if ("Notification" in window && Notification.permission === "default") {
        Notification.requestPermission();
      }
      if (!req.lat || !req.lng) {
        if (req.search_mode !== "multiple_pincodes" || !req.pincodes || req.pincodes.length === 0) {
          throw new Error("Please select a valid location or enter at least one pincode.");
        }
      }
      if (!req.keywords?.length && !req.categories?.length && !req.product_urls?.length) {
        throw new Error("Please provide at least one Keyword, Category, or Wishlist link to track.");
      }
      const res = await fetch(`${API_BASE}/alerts/primary` , {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
      });
      if (!res.ok) {
        let errorMsg = "Failed to start monitoring";
        try {
          const data = await res.json();
          errorMsg = data.detail || data.message || errorMsg;
        } catch {
          errorMsg = await res.text() || errorMsg;
        }
        throw new Error(errorMsg);
      }
      setStreamUrl(`/api/alerts/primary_monitor/stream?trigger_run=true`);
    } catch (err: any) {
      setError(err.message);
      setIsSearching(false);
      setStreamUrl(null);
    }
  };

  const cancelSearch = async () => {
    try {
      await fetch(`${API_BASE}/alerts/primary/stop` , { method: "PATCH" });
    } catch (err) {
      console.error("Failed to stop monitor", err);
    }
    setStreamUrl(null);
    setIsSearching(false);
    liveConsoleStore.setScanState("IDLE");
  };

  if (isLoadingConfig) {
    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        minHeight: "300px",
        flexDirection: "column",
        gap: "12px",
      }}>
        <Loader2
          size={24} strokeWidth={2} className="animate-spin"
          style={{ color: "var(--color-brand-green)" }}
        />
        <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>Loading configuration…</span>
      </div>
    );
  }

  const showResults = streamUrl !== null || isSearching;

  return (
    /* Outer column — width 100% of <main>, no max-width */
    <div style={{ display: "flex", flexDirection: "column", width: "100%" }}>

      {/* Subtle fixed ambient gradient across the full content area */}
      <div style={{
        position: "fixed",
        top: 0,
        left: "220px",
        right: 0,
        height: "500px",
        background: "radial-gradient(ellipse 60% 40% at 50% 0%, rgba(22,163,74,0.06) 0%, transparent 70%)",
        pointerEvents: "none",
        zIndex: 0,
      }} />

      {/* ── HERO — full available width, only shown before first search ── */}
      {!showResults && (
        <div style={{ width: "100%", position: "relative", zIndex: 1 }}>
          <WorthItHero />
        </div>
      )}

      {/* ── CONTROLS — keep the existing max-width constrained layout ── */}
      <div style={{
        width: "100%",
        maxWidth: "1080px",
        margin: "0 auto",
        padding: showResults ? "32px 28px 48px" : "0 28px 48px",
        position: "relative",
        zIndex: 1,
      }}>

        {/* Error banner */}
        {error && (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "14px 18px",
            background: "rgba(220,38,38,0.06)",
            border: "1px solid rgba(220,38,38,0.25)",
            borderRadius: "10px",
            color: "#f87171",
            fontSize: "14px",
            fontWeight: 500,
            marginBottom: "20px",
          }}>
            <AlertCircle size={16} strokeWidth={2} className="shrink-0" />
            {error}
            <button
              onClick={() => setError(null)}
              style={{
                marginLeft: "auto",
                background: "transparent",
                border: "none",
                color: "inherit",
                cursor: "pointer",
                opacity: 0.7,
                fontSize: "18px",
                lineHeight: 1,
                padding: "0 4px",
              }}
            >×</button>
          </div>
        )}

        {/* Configuration form */}
        <ProductSearch
          onSearch={handleSearch}
          isSearching={isSearching}
          onCancel={cancelSearch}
          compact={showResults}
          initialConfig={initialConfig}
          scanConsole={
            (showResults && streamUrl) ? (
              <div style={{ width: "100%", marginTop: "20px" }}>
                <LiveConsole streamUrl={streamUrl} />
              </div>
            ) : undefined
          }
        />
      </div>
    </div>
  );
}
