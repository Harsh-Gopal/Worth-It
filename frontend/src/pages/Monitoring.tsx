import { useState, useEffect } from "react";
import ProductSearch from "../components/search/ProductSearch";
import WorthItLogo from "../components/branding/WorthItLogo";
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
      if (!req.lat || !req.lng) {
        throw new Error("Please select a valid location.");
      }
      if (!req.keywords?.length && !req.categories?.length && !req.product_urls?.length) {
        throw new Error("Please provide at least one Keyword, Category, or Wishlist link to track.");
      }
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
          className="w-6 h-6 animate-spin"
          style={{ color: "var(--color-brand-green)" }}
        />
        <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>Loading configuration…</span>
      </div>
    );
  }

  const showResults = streamUrl !== null || isSearching;

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      gap: "0",
      width: "100%",
      maxWidth: "1080px",
      margin: "0 auto",
      padding: "32px 28px 48px",
    }}>
      {/* Subtle ambient gradient — dark mode only */}
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

      {/* Hero — only before first search */}
      {!showResults && (
        <div style={{
          textAlign: "center",
          padding: "40px 16px 48px",
          position: "relative",
          zIndex: 1,
          animation: "fadeIn 0.3s ease-out both",
        }}>
          {/* Logo */}
          <div style={{
            display: "inline-block",
            marginBottom: "32px",
          }}>
            <WorthItLogo height={52} showTagline={false} />
          </div>

          {/* Heading */}
          <h1 style={{
            fontSize: "clamp(28px, 4vw, 46px)",
            fontWeight: 800,
            letterSpacing: "-0.03em",
            margin: "0 0 16px 0",
            background: "linear-gradient(135deg, var(--text-primary) 0%, var(--color-brand-green) 50%, var(--text-secondary) 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            lineHeight: 1.15,
          }}>
            Find the price worth buying.
          </h1>

          <p style={{
            fontSize: "16px",
            color: "var(--text-secondary)",
            maxWidth: "520px",
            margin: "0 auto",
            lineHeight: 1.7,
            fontWeight: 400,
          }}>
            Monitor Instamart, Zepto, and Blinkit simultaneously.
            Track deals, set thresholds, and get alerted instantly.
          </p>
        </div>
      )}

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
          zIndex: 1,
          position: "relative",
        }}>
          <AlertCircle className="w-4 h-4 shrink-0" />
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
      <div style={{ width: "100%", position: "relative", zIndex: 1 }}>
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
