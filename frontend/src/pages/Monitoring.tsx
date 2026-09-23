import { useState, useEffect } from "react";
import ProductSearch from "../components/search/ProductSearch";
import WorthItLogo from "../components/branding/WorthItLogo";
import LiveConsole from "../components/console/LiveConsole";
import { liveConsoleStore } from "../store/liveConsoleStore";
import { Loader2 } from "lucide-react";

export default function Monitoring() {
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialConfig, setInitialConfig] = useState<any>(null);
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);

  // Fetch active monitor on mount
  useEffect(() => {
    const fetchActiveMonitor = async () => {
      try {
        const res = await fetch("/api/alerts/primary");
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

      // 1. Validate on frontend
      if (!req.lat || !req.lng) {
        throw new Error("Please select a valid location.");
      }
      if (!req.keywords?.length && !req.categories?.length && !req.product_urls?.length) {
        throw new Error("Please provide at least one Keyword, Category, or Wishlist link to track.");
      }

      // 2. Persist configuration
      const res = await fetch("/api/alerts/primary", {
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

      // 3. Connect live terminal and trigger run via SSE
      setStreamUrl(`/api/alerts/primary_monitor/stream?trigger_run=true`);
      
    } catch (err: any) {
      setError(err.message);
      setIsSearching(false);
      setStreamUrl(null);
    }
  };

  const cancelSearch = async () => {
    try {
      await fetch("/api/alerts/primary/stop", { method: "PATCH" });
    } catch (err) {
      console.error("Failed to stop monitor", err);
    }
    setStreamUrl(null);
    setIsSearching(false);
    liveConsoleStore.setScanState("IDLE");
  };

  if (isLoadingConfig) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "48px" }}>
        <Loader2 className="w-6 h-6 animate-spin" style={{ color: "var(--color-brand-green)" }} />
      </div>
    );
  }

  const showResults = streamUrl !== null || isSearching;

  return (
    <div className="flex flex-col gap-8 w-full max-w-[1100px] mx-auto px-6 py-8 md:px-10 md:py-10">
      {/* Premium Background Mesh */}
      <div style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: "100vh",
        background: "radial-gradient(circle at 50% 0%, rgba(22, 163, 74, 0.08) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(0, 136, 204, 0.04) 0%, transparent 40%)",
        pointerEvents: "none",
        zIndex: -1,
      }} />

      {/* Hero — shown only before first search */}
      {!showResults && (
        <div style={{
          textAlign: "center",
          padding: "40px 16px 32px",
          position: "relative",
        }}>
          <div style={{ display: "inline-block", marginBottom: "24px", filter: "drop-shadow(0 0 20px rgba(22,163,74,0.2))" }}>
            <WorthItLogo height={48} showTagline={false} />
          </div>
          <h1 style={{
            fontSize: "42px",
            fontWeight: 800,
            letterSpacing: "-0.02em",
            margin: "0 0 16px 0",
            background: "linear-gradient(135deg, #ffffff 0%, #a1a1aa 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}>
            Find the price worth buying.
          </h1>
          <p style={{
            fontSize: "18px",
            color: "var(--text-secondary)",
            maxWidth: "600px",
            margin: "0 auto",
            lineHeight: 1.6,
            fontWeight: 400,
          }}>
            Search across multiple rapid-delivery stores simultaneously. Track deals, evaluate stock, and set automated alerts.
          </p>
        </div>
      )}

      {error && (
        <div style={{
          padding: "16px",
          background: "var(--ring-red)",
          border: "1px solid rgba(220,38,38,0.3)",
          borderRadius: "8px",
          color: "var(--color-brand-red)",
          fontSize: "14px",
          fontWeight: 500,
        }}>
          {error}
        </div>
      )}

      {/* Configuration form always visible so user can edit and restart */}
      <div style={{ width: "100%" }}>
        <ProductSearch
          onSearch={handleSearch}
          isSearching={isSearching}
          onCancel={cancelSearch}
          compact={showResults} // Make compact if terminal is open
          initialConfig={initialConfig}
          scanConsole={
            (showResults && streamUrl) ? (
              <div style={{ width: "100%", marginTop: "16px" }}>
                <LiveConsole streamUrl={streamUrl} />
              </div>
            ) : undefined
          }
        />
      </div>
    </div>
  );
}
