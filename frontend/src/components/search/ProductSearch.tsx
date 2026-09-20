import { useState, useEffect } from "react";
import { Search, Loader2 } from "lucide-react";
import LocationSelector from "./LocationSelector";
import DealCriteria from "./DealCriteria";
import CategorySelector from "./CategorySelector";
import KeywordInput from "./KeywordInput";
import WishlistSection from "./WishlistSection";

interface ProductSearchProps {
  onSearch: (request: any) => void;
  isSearching: boolean;
  onCancel: () => void;
  compact?: boolean;
  initialConfig?: any;
}

const SectionHeader = ({ title, description }: { title: string; description?: string }) => (
  <div style={{ marginBottom: "12px" }}>
    <h3 style={{
      fontSize: "13px",
      fontWeight: 600,
      color: "var(--text-primary)",
      margin: 0,
      marginBottom: description ? "3px" : 0,
    }}>
      {title}
    </h3>
    {description && (
      <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: 0 }}>
        {description}
      </p>
    )}
  </div>
);

export default function ProductSearch({
  onSearch,
  isSearching,
  onCancel,
  compact = false,
  initialConfig,
}: ProductSearchProps) {
  const [categories, setCategories] = useState<string[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>([]);
  const [location, setLocation] = useState<{
    lat: number;
    lng: number;
    title: string;
    local_store_id: string | null;
  } | null>(null);
  const [radiusKm, setRadiusKm] = useState<number>(10);
  const RADIUS_OPTIONS = [3, 5, 10, 15, 20];

  const [criteria, setCriteria] = useState({
    min_discount_pct: 50 as number | null,
    max_price: null as number | null,
    min_price_drop_pct: null as number | null,
    require_historical_low: false,
  });
  
  const [scanInterval, setScanInterval] = useState<number>(15);

  useEffect(() => {
    if (initialConfig) {
      setCategories(initialConfig.categories || []);
      setKeywords(initialConfig.keywords || []);
      setExcludeKeywords(initialConfig.exclude_keywords || []);
      if (initialConfig.lat && initialConfig.lng) {
        setLocation({
          lat: initialConfig.lat,
          lng: initialConfig.lng,
          title: "Saved Location",
          local_store_id: initialConfig.local_store_id || null,
        });
      }
      setRadiusKm(initialConfig.radius_km || 10);
      setCriteria({
        min_discount_pct: initialConfig.min_discount_pct,
        max_price: initialConfig.max_price,
        min_price_drop_pct: initialConfig.min_price_drop_pct,
        require_historical_low: initialConfig.require_historical_low || false,
      });
      setScanInterval(initialConfig.run_interval_minutes || 15);
    }
  }, [initialConfig]);

  const handleStartSearch = () => {
    let selectedWishlistUrls: string[] = [];
    try {
      const stored = localStorage.getItem("worth_it_wishlist");
      if (stored) {
        const items = JSON.parse(stored);
        if (Array.isArray(items)) {
          selectedWishlistUrls = items
            .filter((i: any) => i.selected)
            .map((i: any) => i.url);
        }
      }
    } catch (err) {
      console.error(err);
    }

    const req = {
      categories,
      keywords,
      exclude_keywords: excludeKeywords,
      product_urls: selectedWishlistUrls,
      min_discount_pct: criteria.min_discount_pct,
      max_price: criteria.max_price,
      min_price_drop_pct: criteria.min_price_drop_pct,
      require_historical_low: criteria.require_historical_low,
      lat: location?.lat ?? null,
      lng: location?.lng ?? null,
      local_store_id: location?.local_store_id ?? null,
      radius_km: radiusKm,
      expansion_strategy: "NEARBY_FIRST",
      run_interval_minutes: scanInterval,
    };
    onSearch(req);
  };

  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border)",
        borderRadius: "12px",
        padding: compact ? "20px" : "28px",
      }}
    >
      {/* Wishlist section — always visible */}
      <WishlistSection />

      <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "24px 0" }} />

      {/* Two-column layout: categories left, area+criteria right */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: "32px",
      }}
        className="search-grid"
      >
        {/* Left: Target + Keywords */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px", minWidth: 0 }}>
          <div>
            <SectionHeader title="Target Categories" description="Optional. Discover deals across broad categories." />
            <CategorySelector selected={categories} onSelect={setCategories} compact={false} />
          </div>

          <div>
            <SectionHeader title="Keywords" description="Optional. Specific brands or product names." />
            <KeywordInput keywords={keywords} setKeywords={setKeywords} categories={categories} />
          </div>

          {keywords.length > 0 && (
            <div>
              <SectionHeader title="Exclude Keywords" description="Filter out unwanted matches." />
              <KeywordInput keywords={excludeKeywords} setKeywords={setExcludeKeywords} />
            </div>
          )}
        </div>

        {/* Right: Area + Deal Criteria */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px", minWidth: 0 }}>
          {/* Search Area */}
          <div>
            <SectionHeader title="Search Area" description="Define geographic boundaries of your scan." />
            <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "8px", alignItems: "start" }}>
              <div style={{ minWidth: 0 }}>
                <LocationSelector location={location} setLocation={setLocation} />
              </div>
              <select
                value={radiusKm}
                onChange={e => setRadiusKm(Number(e.target.value))}
                style={{
                  background: "var(--bg-input)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  color: "var(--text-primary)",
                  fontSize: "13px",
                  fontWeight: 500,
                  padding: "9px 12px",
                  outline: "none",
                  cursor: "pointer",
                  fontFamily: "inherit",
                  height: "40px",
                  flexShrink: 0,
                }}
              >
                {RADIUS_OPTIONS.map(r => (
                  <option key={r} value={r}>{r} km</option>
                ))}
              </select>
            </div>
          </div>

          {/* Deal Criteria */}
          <div>
            <SectionHeader title="Deal Criteria" description="Only surface deals matching these thresholds." />
            <div style={{
              background: "var(--bg-muted)",
              border: "1px solid var(--border)",
              borderRadius: "10px",
              padding: "16px",
            }}>
              <DealCriteria criteria={criteria} setCriteria={setCriteria} />
            </div>
          </div>
        </div>
      </div>

      {/* Footer action */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        paddingTop: "24px",
        marginTop: "24px",
        borderTop: "1px solid var(--border)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>
            Scan Interval:
          </span>
          <select
            value={scanInterval}
            onChange={e => setScanInterval(Number(e.target.value))}
            style={{
              background: "var(--bg-input)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              color: "var(--text-primary)",
              fontSize: "13px",
              fontWeight: 500,
              padding: "8px 12px",
              outline: "none",
              cursor: "pointer",
            }}
          >
            <option value={5}>Every 5 mins</option>
            <option value={15}>Every 15 mins</option>
            <option value={30}>Every 30 mins</option>
          </select>
        </div>
        
        {isSearching ? (
          <button
            type="button"
            onClick={onCancel}
            className="btn-danger"
            style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: "160px", justifyContent: "center" }}
          >
            <Loader2 className="w-4 h-4 animate-spin" /> Stop Scan
          </button>
        ) : (
          <button
            type="button"
            onClick={handleStartSearch}
            className="btn-primary"
            style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: "160px", justifyContent: "center" }}
          >
            <Search className="w-4 h-4" /> Start Watch
          </button>
        )}
      </div>

      <style>{`
        @media (max-width: 768px) {
          .search-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}
