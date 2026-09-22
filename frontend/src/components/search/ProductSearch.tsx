import { useState, useEffect } from "react";
import { Search, Loader2 } from "lucide-react";
import LocationSelector from "./LocationSelector";
import CategorySelector from "./CategorySelector";
import KeywordInput from "./KeywordInput";
import WishlistSection from "./WishlistSection";
import type { TargetRule } from "../../lib/types";

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
  const [categories, setCategories] = useState<TargetRule[]>([]);
  const [keywords, setKeywords] = useState<TargetRule[]>([]);
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>([]);
  const [location, setLocation] = useState<{
    lat: number;
    lng: number;
    title: string;
    pincode?: string;
    local_store_id: string | null;
  } | null>(null);
  const [radiusKm, setRadiusKm] = useState<number>(10);
  const RADIUS_OPTIONS = [3, 5, 10, 15, 20];


  const [scanInterval, setScanInterval] = useState<number>(15);

  useEffect(() => {
    if (initialConfig) {
      setCategories(initialConfig.categories?.map((c: string) => ({ 
        name: c, 
        minDiscount: initialConfig.category_rules?.[c]?.min_discount_pct ?? 15 
      })) || []);
      
      setKeywords(initialConfig.keywords?.map((k: string) => ({ 
        name: k, 
        minDiscount: initialConfig.keyword_rules?.[k]?.min_discount_pct ?? 15 
      })) || []);
      
      setExcludeKeywords(initialConfig.exclude_keywords || []);
      if (initialConfig.lat && initialConfig.lng) {
        setLocation({
          lat: initialConfig.lat,
          lng: initialConfig.lng,
          title: initialConfig.pincode || "Saved Location",
          pincode: initialConfig.pincode,
          local_store_id: initialConfig.local_store_id || null,
        });
      }
      setRadiusKm(initialConfig.radius_km || 10);

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

    const category_rules: Record<string, any> = {};
    categories.forEach(c => category_rules[c.name] = c.minDiscount !== null ? { min_discount_pct: c.minDiscount } : {});

    const keyword_rules: Record<string, any> = {};
    keywords.forEach(k => keyword_rules[k.name] = k.minDiscount !== null ? { min_discount_pct: k.minDiscount } : {});

    const req = {
      categories: categories.map(c => c.name),
      category_rules,
      keywords: keywords.map(k => k.name),
      keyword_rules,
      exclude_keywords: excludeKeywords,
      product_urls: selectedWishlistUrls,

      lat: location?.lat ?? null,
      lng: location?.lng ?? null,
      pincode: location?.pincode ?? null,
      local_store_id: location?.local_store_id ?? null,
      radius_km: radiusKm,
      expansion_strategy: "NEARBY_FIRST",
      run_interval_minutes: scanInterval,
      adaptive_mode: true, // Default to true for MVP
    };
    onSearch(req);
  };

  return (
    <div
      className="flex flex-col bg-[var(--bg-page)] border border-[var(--border)] rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] overflow-hidden"
      style={{
        padding: compact ? "24px" : "32px",
      }}
    >
      {/* Wishlist section — always visible */}
      <div className="mb-8">
        <WishlistSection />
      </div>

      <div className="w-full h-px bg-[var(--border)] opacity-60 mb-8"></div>

      {/* Two-column layout: categories left, area+criteria right */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)",
        gap: "40px",
      }}
        className="search-grid"
      >
        {/* Left: Target + Keywords */}
        <div style={{ display: "flex", flexDirection: "column", gap: "32px", minWidth: 0 }}>
          <div>
            <SectionHeader title="Target Categories" description="Optional. Discover deals across broad categories." />
            <div className="mt-4">
              <CategorySelector selected={categories} onSelect={setCategories} compact={false} />
            </div>
          </div>

          <div>
            <SectionHeader title="Keywords" description="Optional. Specific brands or product names." />
            <div className="mt-4">
              <KeywordInput keywords={keywords} setKeywords={setKeywords} categories={categories.map(c => c.name)} />
            </div>
          </div>

          {keywords.length > 0 && (
            <div>
              <SectionHeader title="Exclude Keywords" description="Filter out unwanted matches." />
              <div className="mt-4">
                <KeywordInput 
                  keywords={excludeKeywords.map(k => ({ name: k, minDiscount: 0 }))} 
                  setKeywords={(kws) => setExcludeKeywords(kws.map(k => k.name))} 
                />
              </div>
            </div>
          )}
        </div>

        {/* Right: Area + Deal Criteria */}
        <div style={{ display: "flex", flexDirection: "column", gap: "32px", minWidth: 0 }}>
          {/* Search Area */}
          <div>
            <SectionHeader title="Search Area" description="Define geographic boundaries of your scan." />
            <div className="mt-4" style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "12px", alignItems: "start" }}>
              <div style={{ minWidth: 0 }}>
                <LocationSelector location={location} setLocation={setLocation} />
              </div>
              <select
                value={radiusKm}
                onChange={e => setRadiusKm(Number(e.target.value))}
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  color: "var(--text-primary)",
                  fontSize: "13px",
                  fontWeight: 500,
                  padding: "0 12px",
                  outline: "none",
                  cursor: "pointer",
                  fontFamily: "inherit",
                  height: "44px",
                  flexShrink: 0,
                  boxShadow: "0 1px 2px rgba(0,0,0,0.02)",
                }}
              >
                {RADIUS_OPTIONS.map(r => (
                  <option key={r} value={r}>{r} km</option>
                ))}
              </select>
            </div>
          </div>


        </div>
      </div>

      {/* Footer action */}
      <div style={{
        display: "flex",
        flexDirection: "column",
        gap: "24px",
        paddingTop: "32px",
        marginTop: "32px",
        borderTop: "1px solid var(--border)",
      }}>
        {/* Active Targets */}
        {(categories.length > 0 || keywords.length > 0) && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "center" }}>
            <span style={{ fontSize: "13px", color: "var(--text-secondary)", fontWeight: 600, marginRight: "8px" }}>
              Active Targets:
            </span>
            {categories.map(c => (
              <span key={c.name} style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-brand-green)", background: "rgba(34, 197, 94, 0.1)", padding: "4px 8px", borderRadius: "6px", border: "1px solid rgba(34, 197, 94, 0.2)" }}>
                {c.name}{c.minDiscount !== null && ` (≥${c.minDiscount}%)`}
              </span>
            ))}
            {keywords.map(k => (
              <span key={k.name} style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-brand-green)", background: "rgba(34, 197, 94, 0.1)", padding: "4px 8px", borderRadius: "6px", border: "1px solid rgba(34, 197, 94, 0.2)" }}>
                {k.name}{k.minDiscount !== null && ` (≥${k.minDiscount}%)`}
              </span>
            ))}
          </div>
        )}

        {/* Scan Controls Row */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-secondary)" }}>
              Scan Interval:
            </span>
            <select
              value={scanInterval}
              onChange={e => setScanInterval(Number(e.target.value))}
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                color: "var(--text-primary)",
                fontSize: "13px",
                fontWeight: 500,
                padding: "8px 12px",
                outline: "none",
                cursor: "pointer",
                boxShadow: "0 1px 2px rgba(0,0,0,0.02)",
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
              style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: "160px", justifyContent: "center", height: "44px", borderRadius: "8px", fontWeight: 600 }}
            >
              <Loader2 className="w-4 h-4 animate-spin" /> Stop Scan
            </button>
          ) : (
            <button
              type="button"
              onClick={handleStartSearch}
              className="btn-primary"
              style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: "160px", justifyContent: "center", height: "44px", borderRadius: "8px", fontWeight: 600 }}
            >
              <Search className="w-4 h-4" /> Start Watch
            </button>
          )}
        </div>
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
