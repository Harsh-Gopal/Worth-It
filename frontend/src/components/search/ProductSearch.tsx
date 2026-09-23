import { useState, useEffect } from "react";
import { Play, Square, RotateCcw, Grid, Search, Ban, Target, MapPin, Check } from "lucide-react";
import LocationSelector from "./LocationSelector";
import CategorySelector from "./CategorySelector";
import KeywordInput from "./KeywordInput";
import WishlistSection from "./WishlistSection";
import ScanProgress from "../console/ScanProgress";
import type { TargetRule } from "../../lib/types";
import { liveConsoleStore } from "../../store/liveConsoleStore";

interface ProductSearchProps {
  onSearch: (request: any) => void;
  isSearching: boolean;
  onCancel: () => void;
  compact?: boolean;
  initialConfig?: any;
  scanConsole?: React.ReactNode;
}


const ConfigCard = ({ icon: Icon, iconColor, title, description, count, countLabel, children }: any) => (
  <div className="card" style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "12px", height: "100%" }}>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
      <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
        <div style={{ padding: "8px", background: "var(--bg-input)", borderRadius: "8px", color: iconColor }}>
          <Icon className="w-5 h-5" />
        </div>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <h4 style={{ margin: "0 0 2px 0", fontSize: "14px", fontWeight: 700, color: "var(--text-primary)" }}>{title}</h4>
          <p style={{ margin: 0, fontSize: "12px", color: "var(--text-secondary)" }}>{description}</p>
        </div>
      </div>
      {count !== undefined && (
        <div style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 500 }}>
          {count} {countLabel}
        </div>
      )}
    </div>
    <div style={{ width: "100%", height: "1px", background: "var(--border)", opacity: 0.5 }} />
    <div style={{ flex: 1 }}>
      {children}
    </div>
  </div>
);

export default function ProductSearch({
  onSearch,
  isSearching,
  onCancel,
  compact = false,
  initialConfig,
  scanConsole,
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
  const [searchMode, setSearchMode] = useState<"current_pincode" | "nearby_area">("current_pincode");


  const [scanInterval, setScanInterval] = useState<number>(15);

  const [platforms, setPlatforms] = useState<string[]>(["swiggy"]);

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
      setSearchMode(initialConfig.search_mode || "current_pincode");
      setScanInterval(initialConfig.run_interval_minutes || 15);
      
      if (initialConfig.platforms && initialConfig.platforms.length > 0) {
        setPlatforms(initialConfig.platforms.map((p: string) => p === "instamart" ? "swiggy" : p));
      }
    }
  }, [initialConfig]);

  const togglePlatform = (p: string) => {
    setPlatforms(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]);
  };

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
      platforms: platforms.length > 0 ? platforms : ["swiggy"],

      lat: location?.lat ?? null,
      lng: location?.lng ?? null,
      pincode: location?.pincode ?? null,
      local_store_id: location?.local_store_id ?? null,
      radius_km: radiusKm,
      search_mode: searchMode,
      expansion_strategy: "NEARBY_FIRST",
      run_interval_minutes: scanInterval,
      adaptive_mode: true, // Default to true for MVP
    };
    onSearch(req);
  };

  const handleHardReset = () => {
    onCancel();
    liveConsoleStore.clearLogs();
    liveConsoleStore.setScanState("IDLE");
  };

  return (
    <div
      className="flex flex-col bg-[var(--bg-page)] border border-[var(--border)] rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] overflow-hidden"
      style={{
        padding: compact ? "24px" : "32px",
      }}
    >
      {/* 1. TOP ROW: Platforms & Actions */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", flexWrap: "wrap", gap: "24px" }}>
        
        {/* Left Area: Platform Selection */}
        <div style={{ flex: "1 1 auto", minWidth: "300px" }}>
          <h3 style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)", margin: "0 0 12px 0", letterSpacing: "0.5px" }}>
            Select Platforms
          </h3>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            {/* Swiggy Instamart */}
            <label className="flex cursor-pointer" style={{ margin: 0 }}>
              <input type="checkbox" checked={platforms.includes("swiggy")} onChange={() => togglePlatform("swiggy")} style={{ display: 'none' }} />
              <div className="card" style={{
                padding: "12px 16px",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                transition: "all 0.2s",
                border: `1px solid ${platforms.includes("swiggy") ? "var(--platform-swiggy)" : "var(--border-strong)"}`,
                backgroundColor: platforms.includes("swiggy") ? "rgba(252, 128, 25, 0.08)" : "var(--bg-surface)",
                boxShadow: platforms.includes("swiggy") ? "0 0 16px var(--platform-swiggy-glow)" : "none",
                minWidth: "160px"
              }}>
                <div style={{
                  width: "20px", height: "20px", borderRadius: "4px",
                  border: `2px solid ${platforms.includes("swiggy") ? "var(--platform-swiggy)" : "var(--text-muted)"}`,
                  backgroundColor: platforms.includes("swiggy") ? "var(--platform-swiggy)" : "transparent",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "#fff", flexShrink: 0, opacity: platforms.includes("swiggy") ? 1 : 0.5
                }}>
                  {platforms.includes("swiggy") && <Check className="w-3 h-3" strokeWidth={4} />}
                </div>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "14px", fontWeight: 700, color: platforms.includes("swiggy") ? "var(--platform-swiggy)" : "var(--text-primary)" }}>Swiggy Instamart</span>
                </div>
              </div>
            </label>

            {/* Zepto */}
            <label className="flex cursor-pointer" style={{ margin: 0 }}>
              <input type="checkbox" checked={platforms.includes("zepto")} onChange={() => togglePlatform("zepto")} style={{ display: 'none' }} />
              <div className="card" style={{
                padding: "12px 16px",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                transition: "all 0.2s",
                border: `1px solid ${platforms.includes("zepto") ? "var(--platform-zepto)" : "var(--border-strong)"}`,
                backgroundColor: platforms.includes("zepto") ? "rgba(255, 50, 105, 0.08)" : "var(--bg-surface)",
                boxShadow: platforms.includes("zepto") ? "0 0 16px var(--platform-zepto-glow)" : "none",
                minWidth: "160px"
              }}>
                <div style={{
                  width: "20px", height: "20px", borderRadius: "4px",
                  border: `2px solid ${platforms.includes("zepto") ? "var(--platform-zepto)" : "var(--text-muted)"}`,
                  backgroundColor: platforms.includes("zepto") ? "var(--platform-zepto)" : "transparent",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "#fff", flexShrink: 0, opacity: platforms.includes("zepto") ? 1 : 0.5
                }}>
                  {platforms.includes("zepto") && <Check className="w-3 h-3" strokeWidth={4} />}
                </div>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "14px", fontWeight: 700, color: platforms.includes("zepto") ? "var(--platform-zepto)" : "var(--text-primary)" }}>Zepto</span>
                </div>
              </div>
            </label>

            {/* Blinkit */}
            <label className="flex cursor-pointer" style={{ margin: 0 }}>
              <input type="checkbox" checked={platforms.includes("blinkit")} onChange={() => togglePlatform("blinkit")} style={{ display: 'none' }} />
              <div className="card" style={{
                padding: "12px 16px",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                transition: "all 0.2s",
                border: `1px solid ${platforms.includes("blinkit") ? "var(--platform-blinkit)" : "var(--border-strong)"}`,
                backgroundColor: platforms.includes("blinkit") ? "rgba(248, 203, 70, 0.08)" : "var(--bg-surface)",
                boxShadow: platforms.includes("blinkit") ? "0 0 16px var(--platform-blinkit-glow)" : "none",
                minWidth: "160px"
              }}>
                <div style={{
                  width: "20px", height: "20px", borderRadius: "4px",
                  border: `2px solid ${platforms.includes("blinkit") ? "var(--platform-blinkit)" : "var(--text-muted)"}`,
                  backgroundColor: platforms.includes("blinkit") ? "var(--platform-blinkit)" : "transparent",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "#000", flexShrink: 0, opacity: platforms.includes("blinkit") ? 1 : 0.5
                }}>
                  {platforms.includes("blinkit") && <Check className="w-3 h-3" strokeWidth={4} />}
                </div>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "14px", fontWeight: 700, color: platforms.includes("blinkit") ? "var(--platform-blinkit)" : "var(--text-primary)" }}>Blinkit</span>
                </div>
              </div>
            </label>

            {/* Minutes */}
            <label className="flex cursor-pointer" style={{ margin: 0 }}>
              <input type="checkbox" checked={platforms.includes("minutes")} onChange={() => togglePlatform("minutes")} style={{ display: 'none' }} />
              <div className="card" style={{
                padding: "12px 16px",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                transition: "all 0.2s",
                border: `1px solid ${platforms.includes("minutes") ? "var(--platform-minutes)" : "var(--border-strong)"}`,
                backgroundColor: platforms.includes("minutes") ? "rgba(40, 116, 240, 0.08)" : "var(--bg-surface)",
                boxShadow: platforms.includes("minutes") ? "0 0 16px var(--platform-minutes-glow)" : "none",
                minWidth: "160px"
              }}>
                <div style={{
                  width: "20px", height: "20px", borderRadius: "4px",
                  border: `2px solid ${platforms.includes("minutes") ? "var(--platform-minutes)" : "var(--text-muted)"}`,
                  backgroundColor: platforms.includes("minutes") ? "var(--platform-minutes)" : "transparent",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "#fff", flexShrink: 0, opacity: platforms.includes("minutes") ? 1 : 0.5
                }}>
                  {platforms.includes("minutes") && <Check className="w-3 h-3" strokeWidth={4} />}
                </div>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "14px", fontWeight: 700, color: platforms.includes("minutes") ? "var(--platform-minutes)" : "var(--text-primary)" }}>Minutes</span>
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Right Area: Actions */}
        <div style={{ display: "flex", gap: "12px", alignItems: "flex-end", flexWrap: "wrap", marginTop: "29px" }}>
          {!isSearching ? (
            <button
              type="button"
              onClick={handleStartSearch}
              className="btn-primary"
              style={{ 
                display: "flex", alignItems: "center", gap: "8px", 
                minWidth: "160px", justifyContent: "center", height: "48px"
              }}
            >
              <Play className="w-5 h-5 fill-current" /> Start Tracking
            </button>
          ) : (
            <button
              type="button"
              onClick={onCancel}
              className="btn-danger"
              style={{ 
                display: "flex", alignItems: "center", gap: "8px", 
                minWidth: "160px", justifyContent: "center", height: "48px"
              }}
            >
              <Square className="w-5 h-5 fill-current" /> Stop Tracking
            </button>
          )}
          
          <button
            type="button"
            onClick={handleHardReset}
            className="btn-secondary"
            style={{ 
              display: "flex", alignItems: "center", gap: "8px", 
              minWidth: "140px", justifyContent: "center", height: "48px"
            }}
          >
            <RotateCcw className="w-5 h-5" /> Hard Reset
          </button>
        </div>
      </div>

      <div style={{ marginBottom: "32px", width: "100%" }}>
        <ScanProgress intervalMinutes={initialConfig?.run_interval_minutes} isSearching={isSearching} />
      </div>

      {/* Configuration Area Wrapper */}
      <div className="w-full h-px bg-[var(--border)] opacity-60 mb-8"></div>

      {/* 3. Target Configuration Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)",
        gap: "24px",
        marginBottom: "32px"
      }}
        className="search-grid"
      >
        <ConfigCard 
          icon={Grid} 
          iconColor="#a855f7" 
          title="Target Categories" 
          description="Discover deals across broad product categories" 
          count={categories.length} 
          countLabel="categories"
        >
          <CategorySelector selected={categories} onSelect={setCategories} compact={false} />
        </ConfigCard>

        <ConfigCard 
          icon={MapPin} 
          iconColor="var(--color-brand-green)" 
          title="Search Area & Timing" 
          description="Define geographic boundaries and scanning frequency" 
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <div style={{ display: "flex", background: "var(--bg-input)", padding: "4px", borderRadius: "10px", width: "fit-content", gap: "4px" }}>
              <button
                type="button"
                onClick={() => setSearchMode("current_pincode")}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  fontSize: "13px",
                  fontWeight: 600,
                  color: searchMode === "current_pincode" ? "var(--text-primary)" : "var(--text-secondary)",
                  background: searchMode === "current_pincode" ? "var(--bg-card)" : "transparent",
                  border: "none",
                  boxShadow: searchMode === "current_pincode" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                  cursor: "pointer",
                  transition: "all 0.2s"
                }}
              >
                Current Pincode Only
              </button>
              <button
                type="button"
                onClick={() => setSearchMode("nearby_area")}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  fontSize: "13px",
                  fontWeight: 600,
                  color: searchMode === "nearby_area" ? "var(--text-primary)" : "var(--text-secondary)",
                  background: searchMode === "nearby_area" ? "var(--bg-card)" : "transparent",
                  border: "none",
                  boxShadow: searchMode === "nearby_area" ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                  cursor: "pointer",
                  transition: "all 0.2s"
                }}
              >
                Nearby Area
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: searchMode === "nearby_area" ? "1fr auto auto" : "1fr auto", gap: "12px", alignItems: "start" }}>
              <div style={{ minWidth: 0 }}>
                <LocationSelector location={location} setLocation={setLocation} />
              </div>
              
              {searchMode === "nearby_area" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
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
                      padding: "0 12px",
                      outline: "none",
                      cursor: "pointer",
                      fontFamily: "inherit",
                      height: "44px",
                      flexShrink: 0,
                      transition: "border-color 0.15s, box-shadow 0.15s",
                    }}
                    onFocus={e => {
                      e.target.style.borderColor = "var(--color-brand-green)";
                      e.target.style.boxShadow = "0 0 0 3px var(--ring-green)";
                    }}
                    onBlur={e => {
                      e.target.style.borderColor = "var(--border)";
                      e.target.style.boxShadow = "none";
                    }}
                  >
                    {RADIUS_OPTIONS.map(r => (
                      <option key={r} value={r}>{r} km radius</option>
                    ))}
                  </select>
                </div>
              )}

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
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
                    padding: "0 12px",
                    outline: "none",
                    cursor: "pointer",
                    fontFamily: "inherit",
                    height: "44px",
                    flexShrink: 0,
                    transition: "border-color 0.15s, box-shadow 0.15s",
                  }}
                  onFocus={e => {
                    e.target.style.borderColor = "var(--color-brand-green)";
                    e.target.style.boxShadow = "0 0 0 3px var(--ring-green)";
                  }}
                  onBlur={e => {
                    e.target.style.borderColor = "var(--border)";
                    e.target.style.boxShadow = "none";
                  }}
                >
                  <option value={5}>Every 5 mins</option>
                  <option value={15}>Every 15 mins</option>
                  <option value={30}>Every 30 mins</option>
                </select>
              </div>
            </div>
          </div>
        </ConfigCard>

        <ConfigCard 
          icon={Search} 
          iconColor="var(--color-brand-green)" 
          title="Keywords" 
          description="Track specific brands or product names" 
          count={keywords.length} 
          countLabel="keywords"
        >
          <KeywordInput keywords={keywords} setKeywords={setKeywords} categories={categories.map(c => c.name)} placeholder="Add a keyword..." />
        </ConfigCard>

        <ConfigCard 
          icon={Ban} 
          iconColor="var(--color-brand-red)" 
          title="Exclude Keywords" 
          description="Filter out unwanted matches" 
          count={excludeKeywords.length} 
          countLabel="excluded"
        >
          <KeywordInput 
            keywords={excludeKeywords.map(k => ({ name: k, minDiscount: 0 }))} 
            setKeywords={(kws) => setExcludeKeywords(kws.map(k => k.name))} 
            placeholder="Add keyword to exclude..."
          />
        </ConfigCard>
      </div>

      {/* 4. Wishlist Tracking */}
      <div className="mb-8">
        <WishlistSection />
      </div>

      {/* Active Targets */}
      <div className="mb-8">
        <ConfigCard 
          icon={Target} 
          iconColor="var(--color-brand-green)" 
          title="Active Targets" 
          description="Your configured filters" 
          count={categories.length + keywords.length} 
          countLabel="active"
        >
          {(categories.length === 0 && keywords.length === 0) ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", minHeight: "40px" }}>
              <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>No active targets configured.</span>
            </div>
          ) : (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "center" }}>
              {categories.map(c => (
                <span key={c.name} style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-brand-green)", background: "rgba(34, 197, 94, 0.1)", padding: "6px 10px", borderRadius: "8px", border: "1px solid rgba(34, 197, 94, 0.2)" }}>
                  {c.name}{c.minDiscount !== null && ` (≥${c.minDiscount}%)`}
                </span>
              ))}
              {keywords.map(k => (
                <span key={k.name} style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-brand-green)", background: "rgba(34, 197, 94, 0.1)", padding: "6px 10px", borderRadius: "8px", border: "1px solid rgba(34, 197, 94, 0.2)" }}>
                  {k.name}{k.minDiscount !== null && ` (≥${k.minDiscount}%)`}
                </span>
              ))}
            </div>
          )}
        </ConfigCard>
      </div>
      {/* 6. Live Console (Injected via scanConsole prop) */}
      {scanConsole && (
        <div style={{ width: "100%" }}>
          {scanConsole}
        </div>
      )}

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

