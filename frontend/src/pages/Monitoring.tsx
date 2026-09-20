import { useState, useEffect } from "react";
import ProductSearch from "../components/search/ProductSearch";
import WorthItLogo from "../components/branding/WorthItLogo";
import LiveConsole from "../components/console/LiveConsole";
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
        const data = await res.json();
        throw new Error(data.detail || "Failed to start monitoring");
      }

      // 3. Trigger immediate run
      await fetch("/api/alerts/primary_monitor/run", { method: "POST" });

      // 4. Connect live terminal
      setStreamUrl(`/api/alerts/primary_monitor/stream`);
      
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
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "100%" }}>
      {/* Hero — shown only before first search */}
      {!showResults && (
        <div style={{
          textAlign: "center",
          padding: "48px 16px 32px",
        }}>
          <div style={{ display: "inline-block", marginBottom: "20px" }}>
            <WorthItLogo height={40} showTagline={false} />
          </div>
          <p style={{
            fontSize: "16px",
            color: "var(--text-secondary)",
            maxWidth: "520px",
            margin: "0 auto",
            lineHeight: 1.6,
            fontWeight: 400,
          }}>
            Find the price worth buying. Search across multiple stores simultaneously for deals and stock.
          </p>
        </div>
      )}

      {error && (
        <div style={{
          padding: "12px 16px",
          background: "var(--ring-red)",
          border: "1px solid rgba(220,38,38,0.3)",
          borderRadius: "8px",
          color: "var(--color-brand-red)",
          fontSize: "14px",
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
        />
      </div>

      {/* Results / Live Console */}
      {showResults && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ fontSize: "16px", fontWeight: 600, color: "var(--color-brand-green)", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--color-brand-green)", display: "inline-block", boxShadow: "0 0 8px var(--color-brand-green)" }} />
              Live Monitor Active
            </h2>
          </div>
          
          {streamUrl && <LiveConsole streamUrl={streamUrl} />}
        </div>
      )}
    </div>
  );
}
