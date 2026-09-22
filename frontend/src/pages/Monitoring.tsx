import { useState, useEffect } from "react";
import ProductSearch from "../components/search/ProductSearch";
import WorthItLogo from "../components/branding/WorthItLogo";
import LiveConsole from "../components/console/LiveConsole";
import ScanProgress from "../components/console/ScanProgress";
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
        />
      </div>

      {/* Results / Live Console */}
      {showResults && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px", marginTop: "16px" }}>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: "16px 0" }}>
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: "8px", 
              background: "rgba(34, 197, 94, 0.1)", 
              padding: "8px 16px", 
              borderRadius: "20px",
              border: "1px solid rgba(34, 197, 94, 0.2)"
            }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--color-brand-green)", display: "inline-block", boxShadow: "0 0 8px var(--color-brand-green)" }} />
              <span style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-brand-green)", letterSpacing: "0.5px" }}>Live Monitor Active</span>
            </div>
          </div>
          
          {streamUrl && (
            <div style={{ width: "100%" }}>
              <ScanProgress />
              <div style={{ marginTop: "16px" }}>
                <LiveConsole streamUrl={streamUrl} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
