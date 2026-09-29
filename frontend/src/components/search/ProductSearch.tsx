import { useState, useEffect, useMemo } from "react";
import { Play, Square, RotateCcw, LayoutGrid, TextSearch, FilterX, Radar, MapPinned, RefreshCw, ChevronUp, ChevronDown } from "lucide-react";
import LocationSelector from "./LocationSelector";
import CategorySelector from "./CategorySelector";
import KeywordInput from "./KeywordInput";
import WishlistSection from "./WishlistSection";
import ScanProgress from "../console/ScanProgress";
import type { TargetRule } from "../../lib/types";
import { liveConsoleStore } from "../../store/liveConsoleStore";
import { useAuthStore } from "../../store/authStore";

interface ProductSearchProps {
  onSearch: (request: any) => void;
  isSearching: boolean;
  onCancel: () => void;
  compact?: boolean;
  initialConfig?: any;
  scanConsole?: React.ReactNode;
}

// ── Config card sub-component ────────────────────────────────────────────────
function ConfigCard({ icon: Icon, iconColor, iconBg, title, description, count, countLabel, children, defaultExpanded = false }: any) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  return (
    <div className="card flex flex-col gap-3.5 h-full p-4 md:p-5">
      <div 
        className="flex justify-between items-start cursor-pointer md:cursor-default select-none md:select-text"
        onClick={() => {
          if (window.innerWidth <= 768) {
            setExpanded(!expanded);
          }
        }}
      >
        <div className="flex gap-3 items-center">
          <div className="w-[34px] h-[34px] rounded-[9px] border border-[var(--border)] flex items-center justify-center shrink-0" style={{ background: iconBg || "var(--bg-input)", color: iconColor }}>
            <Icon size={18} strokeWidth={2} />
          </div>
          <div>
            <h4 className="m-0 text-[13.5px] font-bold text-[var(--text-primary)] leading-[1.3]">{title}</h4>
            <p className="m-0 text-[11.5px] text-[var(--text-muted)] leading-[1.4] mt-[2px] hidden md:block">{description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {count !== undefined && (
            <span className="text-[11px] font-bold px-[10px] py-[2px] rounded-[20px] transition-all shrink-0" style={{
              color: count > 0 ? "var(--color-brand-green)" : "var(--text-muted)",
              background: count > 0 ? "var(--ring-green)" : "transparent",
              border: count > 0 ? "1px solid rgba(22,163,74,0.2)" : "1px solid transparent",
            }}>
              {count} {countLabel}
            </span>
          )}
          <div className="md:hidden text-[var(--text-muted)] flex items-center">
            {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </div>
        </div>
      </div>
      <div className="h-[1px] bg-[var(--border)] opacity-60 hidden md:block" />
      <div className={`flex-1 transition-all ${expanded ? 'block animate-fade-in-fast' : 'hidden md:block'}`}>
        <div className="h-[1px] bg-[var(--border)] opacity-60 mb-3.5 block md:hidden" />
        {children}
      </div>
    </div>
  );
}

// ── Platform pill toggle ─────────────────────────────────────────────────────
function PlatformPill({
  label, color, softColor, glowColor, checked, onChange
}: {
  label: string; color: string; softColor: string;
  glowColor: string; checked: boolean; onChange: () => void;
}) {
  return (
    <label style={{ cursor: "pointer", userSelect: "none" }}>
      <input type="checkbox" checked={checked} onChange={onChange} style={{ display: "none" }} />
      <div style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "8px",
        padding: "8px 16px",
        borderRadius: "999px",
        border: `1.5px solid ${checked ? color : "var(--border-strong)"}`,
        background: checked ? softColor : "var(--bg-card)",
        boxShadow: checked ? `0 0 14px ${glowColor}` : "none",
        transition: "all 0.2s cubic-bezier(0.4,0,0.2,1)",
        cursor: "pointer",
      }}>
        <span style={{
          width: "7px",
          height: "7px",
          borderRadius: "50%",
          background: checked ? color : "var(--text-muted)",
          transition: "all 0.2s",
          flexShrink: 0,
        }} />
        <span style={{
          fontSize: "13px",
          fontWeight: 600,
          color: checked ? color : "var(--text-secondary)",
          transition: "color 0.2s",
          letterSpacing: "-0.01em",
        }}>
          {label}
        </span>
      </div>
    </label>
  );
}

// ── Main component ────────────────────────────────────────────────────────────
export default function ProductSearch({
  onSearch,
  isSearching,
  onCancel,
  compact: _compact,
  initialConfig,
  scanConsole,
}: ProductSearchProps) {
  const [categories, setCategories] = useState<TargetRule[]>([]);
  const [keywords, setKeywords] = useState<TargetRule[]>([]);
  const [excludeKeywords, setExcludeKeywords] = useState<TargetRule[]>([]);
  const [location, setLocation] = useState<{
    lat: number; lng: number; title: string;
    pincode?: string; local_store_id: string | null;
  } | null>(null);
  const [radiusKm, setRadiusKm] = useState<number>(10);
  const RADIUS_OPTIONS = [3, 5, 10, 15, 20];
  const [searchMode, setSearchMode] = useState<"current_pincode" | "nearby_area" | "multiple_pincodes">("current_pincode");
  const [pincodes, setPincodes] = useState<string[]>([]);
  const [scanInterval, setScanInterval] = useState<number>(15);
  const [platforms, setPlatforms] = useState<string[]>(["swiggy"]);

  const { requestAuth } = useAuthStore();

  // ── Config Dirty State ──────────────────────────────────────────────────────
  const [wishlistTick, setWishlistTick] = useState(0);
  const [sessionConfigStr, setSessionConfigStr] = useState<string | null>(null);
  const [configDirty, setConfigDirty] = useState(false);

  useEffect(() => {
    const handler = () => setWishlistTick(t => t + 1);
    window.addEventListener("wishlist_changed", handler);
    return () => window.removeEventListener("wishlist_changed", handler);
  }, []);

  const currentConfigStr = useMemo(() => {
    let selectedWishlistUrls: string[] = [];
    try {
      const stored = localStorage.getItem("worth_it_wishlist");
      if (stored) {
        const items = JSON.parse(stored);
        if (Array.isArray(items)) {
          selectedWishlistUrls = items.filter((i: any) => i.selected).map((i: any) => i.url);
        }
      }
    } catch (err) {}

    // Sort objects deterministically
    const sortedCategories = [...categories].sort((a, b) => a.name.localeCompare(b.name));
    const sortedKeywords = [...keywords].sort((a, b) => a.name.localeCompare(b.name));

    return JSON.stringify({
      platforms: platforms.slice().sort(),
      categories: sortedCategories.map(c => c.name),
      category_rules: sortedCategories.map(c => c.minDiscount),
      keywords: sortedKeywords.map(k => k.name),
      keyword_rules: sortedKeywords.map(k => k.minDiscount),
      excludeKeywords: [...excludeKeywords].sort((a, b) => a.name.localeCompare(b.name)).map(k => `${k.name}:${k.minDiscount}`),
      radiusKm,
      scanInterval,
      searchMode,
      pincodes: pincodes.slice().sort(),
      location: location ? { lat: location.lat, lng: location.lng, pincode: location.pincode } : null,
      wishlistUrls: selectedWishlistUrls.sort(),
    });
  }, [platforms, categories, keywords, excludeKeywords, radiusKm, scanInterval, searchMode, pincodes, location, wishlistTick]);

  useEffect(() => {
    if (isSearching && sessionConfigStr) {
      if (currentConfigStr !== sessionConfigStr) {
        setConfigDirty(true);
      } else {
        setConfigDirty(false);
      }
    }
  }, [currentConfigStr, isSearching, sessionConfigStr]);

  // Removed problematic useEffect that cleared sessionConfigStr


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
      setExcludeKeywords(initialConfig.exclude_keywords?.map((k: string) => {
        const rule = initialConfig.exclude_keyword_rules?.[k] || {};
        return {
          name: k,
          minDiscount: rule.mode === 'threshold' ? (rule.threshold ?? null) : null
        };
      }) || []);
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
      setPincodes(initialConfig.pincodes || []);
      setScanInterval(initialConfig.run_interval_minutes || 15);
      if (initialConfig.platforms && initialConfig.platforms.length > 0) {
        setPlatforms(initialConfig.platforms.map((p: string) => p === "instamart" ? "swiggy" : p));
      }
    }
  }, [initialConfig]);

  const togglePlatform = (p: string) => {
    requestAuth(() => {
      setPlatforms(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]);
    });
  };

  const handleStartSearch = () => {
    requestAuth(() => {
      if (platforms.length === 0) {
        return; // Validation: Don't start tracking if no platform selected
      }

    let selectedWishlistUrls: string[] = [];
    const product_rules: Record<string, any> = {};
    try {
      const stored = localStorage.getItem("worth_it_wishlist");
      if (stored) {
        const items = JSON.parse(stored);
        if (Array.isArray(items)) {
          const selectedItems = items.filter((i: any) => i.selected);
          selectedWishlistUrls = selectedItems.map((i: any) => i.url);
          selectedItems.forEach((i: any) => {
            if (i.min_discount_pct != null) {
              product_rules[i.url] = { min_discount_pct: i.min_discount_pct };
            }
          });
        }
      }
    } catch (err) {
      console.error(err);
    }

    const category_rules: Record<string, any> = {};
    categories.forEach(c => { category_rules[c.name] = c.minDiscount !== null ? { min_discount_pct: c.minDiscount } : {}; });
    const keyword_rules: Record<string, any> = {};
    keywords.forEach(k => { keyword_rules[k.name] = k.minDiscount !== null ? { min_discount_pct: k.minDiscount } : {}; });
    const exclude_keyword_rules: Record<string, any> = {};
    excludeKeywords.forEach(k => { exclude_keyword_rules[k.name] = k.minDiscount !== null ? { mode: 'threshold', threshold: k.minDiscount } : { mode: 'never' }; });

    setConfigDirty(false);
    setSessionConfigStr(currentConfigStr);

    onSearch({
      categories: categories.map(c => c.name),
      category_rules,
      keywords: keywords.map(k => k.name),
      keyword_rules,
      exclude_keywords: excludeKeywords.map(k => k.name),
      exclude_keyword_rules,
      product_urls: selectedWishlistUrls,
      product_rules,
      platforms: platforms,
      lat: location?.lat ?? null,
      lng: location?.lng ?? null,
      pincode: location?.pincode ?? null,
      local_store_id: location?.local_store_id ?? null,
      radius_km: radiusKm,
      search_mode: searchMode,
      pincodes: pincodes,
      expansion_strategy: "NEARBY_FIRST",
      run_interval_minutes: scanInterval,
      adaptive_mode: true,
    });
    });
  };

  const handleHardReset = () => {
    requestAuth(() => {
      onCancel();
      liveConsoleStore.clearLogs();
      liveConsoleStore.setScanState("IDLE");
      setConfigDirty(false);
      setSessionConfigStr(null);
    });
  };

  const selectStyle: React.CSSProperties = {
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
    height: "40px",
    flexShrink: 0,
    transition: "border-color 0.15s, box-shadow 0.15s",
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "24px",
        background: "var(--bg-page)",
      }}
    >
      {/* ── TOP CONTROL BAR ─────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-5 md:gap-6 p-4 md:p-6 bg-[var(--bg-card)] border border-[var(--border)] rounded-[14px] shadow-[var(--shadow-card)] sticky md:static top-0 z-30 mb-2">
        {/* Platform pills */}
        <div style={{ flex: "1 1 auto", minWidth: "280px" }}>
          <p style={{
            fontSize: "10.5px",
            fontWeight: 700,
            letterSpacing: "0.07em",
            textTransform: "uppercase",
            color: "var(--text-muted)",
            margin: "0 0 12px 0",
          }}>
            Select Platforms
          </p>
          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <PlatformPill
              label="Instamart"
              color="var(--platform-swiggy)"
              softColor="var(--platform-swiggy-soft)"
              glowColor="var(--platform-swiggy-glow)"
              checked={platforms.includes("swiggy")}
              onChange={() => togglePlatform("swiggy")}
            />
            <PlatformPill
              label="Zepto"
              color="var(--platform-zepto)"
              softColor="var(--platform-zepto-soft)"
              glowColor="var(--platform-zepto-glow)"
              checked={platforms.includes("zepto")}
              onChange={() => togglePlatform("zepto")}
            />
            <PlatformPill
              label="Blinkit"
              color="var(--platform-blinkit)"
              softColor="var(--platform-blinkit-soft)"
              glowColor="var(--platform-blinkit-glow)"
              checked={platforms.includes("blinkit")}
              onChange={() => togglePlatform("blinkit")}
            />
            <PlatformPill
              label="Minutes"
              color="var(--platform-minutes)"
              softColor="var(--platform-minutes-soft)"
              glowColor="var(--platform-minutes-glow)"
              checked={platforms.includes("minutes")}
              onChange={() => togglePlatform("minutes")}
            />
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex flex-row md:flex-row gap-2.5 items-center md:items-end flex-wrap pt-2 md:pt-[22px] w-full md:w-auto">
          {isSearching ? (
            configDirty ? (
              <button
                type="button"
                onClick={() => {
                  requestAuth(() => {
                    onCancel(); // Cancel cleanly first
                    setTimeout(() => handleStartSearch(), 50); // Start fresh
                  });
                }}
                disabled={platforms.length === 0}
                className="btn-primary flex-1 md:flex-none min-w-[156px]" style={{ height: "42px", fontSize: "14px", background: "var(--color-brand-blue)" }}
              >
                <RefreshCw size={16} strokeWidth={2} />
                Restart Tracking
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  requestAuth(() => {
                    onCancel();
                    setConfigDirty(false);
                    setSessionConfigStr(null);
                  });
                }}
                className="btn-danger flex-1 md:flex-none min-w-[156px]" style={{ height: "42px", fontSize: "14px" }}
              >
                <Square className="w-4 h-4 fill-current" />
                Stop Tracking
              </button>
            )
          ) : (
            <button
              type="button"
              onClick={handleStartSearch}
              disabled={platforms.length === 0}
              className="btn-primary flex-1 md:flex-none min-w-[156px]" style={{ height: "42px", fontSize: "14px", opacity: platforms.length === 0 ? 0.5 : 1, cursor: platforms.length === 0 ? "not-allowed" : "pointer" }}
            >
              <Play className="w-4 h-4 fill-current" />
              Start Tracking
            </button>
          )}
          <button
            type="button"
            onClick={handleHardReset}
            className="btn-secondary flex-1 md:flex-none min-w-[130px]" style={{ height: "42px", fontSize: "14px" }}
          >
            <RotateCcw size={16} strokeWidth={2} />
            Hard Reset
          </button>
        </div>
      </div>

      {/* ── SCAN PROGRESS BAR ─────────────────────────────── */}
      <ScanProgress intervalMinutes={initialConfig?.run_interval_minutes} isSearching={isSearching} />

      {/* ── ACTIVE TARGETS SUMMARY ───────────────────── */}
      <ConfigCard defaultExpanded={true}
        icon={Radar}
        iconColor="var(--color-brand-green)"
        iconBg="rgba(22,163,74,0.1)"
        title="Active Targets"
        description="Summary of your configured scan filters"
        count={categories.length + keywords.length}
        countLabel="active"
      >
        {(categories.length === 0 && keywords.length === 0) ? (
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "36px",
          }}>
            <span style={{ fontSize: "13px", color: "var(--text-muted)", fontStyle: "italic" }}>
              No targets configured yet.
            </span>
          </div>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "center" }}>
            {categories.map(c => (
              <span
                key={c.name}
                style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "var(--color-brand-green)",
                  background: "var(--ring-green)",
                  border: "1px solid rgba(22,163,74,0.2)",
                  padding: "4px 12px",
                  borderRadius: "999px",
                  letterSpacing: "-0.01em",
                }}
              >
                {c.name}{c.minDiscount !== null && ` ≥${c.minDiscount}%`}
              </span>
            ))}
            {keywords.map(k => (
              <span
                key={k.name}
                style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "#60a5fa",
                  background: "rgba(59,130,246,0.1)",
                  border: "1px solid rgba(59,130,246,0.2)",
                  padding: "4px 12px",
                  borderRadius: "999px",
                  letterSpacing: "-0.01em",
                }}
              >
                {k.name}{k.minDiscount !== null && ` ≥${k.minDiscount}%`}
              </span>
            ))}
          </div>
        )}
      </ConfigCard>

      {/* ── 2×2 CONFIGURATION GRID ───────────────────────── */}
      <div
        className="grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        {/* Target Categories */}
        <ConfigCard
          icon={LayoutGrid}
          iconColor="#a855f7"
          iconBg="rgba(168,85,247,0.1)"
          title="Target Categories"
          description="Discover deals across broad product categories"
          count={categories.length}
          countLabel="categories"
        >
          <CategorySelector selected={categories} onSelect={(c) => requestAuth(() => setCategories(c))} compact={false} />
        </ConfigCard>

        {/* Search Area & Timing */}
        <ConfigCard
          icon={MapPinned}
          iconColor="var(--color-brand-green)"
          iconBg="rgba(22,163,74,0.1)"
          title="Search Area & Timing"
          description="Define geographic boundaries and scanning frequency"
        >
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {/* Mode toggle */}
            <div style={{
              display: "inline-flex",
              background: "var(--bg-input)",
              borderRadius: "8px",
              padding: "3px",
              border: "1px solid var(--border)",
              gap: "3px",
            }}>
              {(["current_pincode", "nearby_area", "multiple_pincodes"] as const).map(mode => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => requestAuth(() => setSearchMode(mode))}
                  style={{
                    padding: "6px 14px",
                    borderRadius: "6px",
                    fontSize: "12.5px",
                    fontWeight: 600,
                    color: searchMode === mode ? "var(--text-primary)" : "var(--text-muted)",
                    background: searchMode === mode ? "var(--bg-surface)" : "transparent",
                    border: searchMode === mode ? "1px solid var(--border-strong)" : "1px solid transparent",
                    boxShadow: searchMode === mode ? "0 1px 3px rgba(0,0,0,0.12)" : "none",
                    cursor: "pointer",
                    transition: "all 0.18s",
                    fontFamily: "inherit",
                    letterSpacing: "-0.01em",
                  }}
                >
                  {mode === "current_pincode" ? "Current Pincode" : mode === "nearby_area" ? "Nearby Area" : "Multiple Pincodes"}
                </button>
              ))}
            </div>

            {searchMode !== "multiple_pincodes" && (
              <div className={`grid gap-2.5 items-start ${searchMode === "nearby_area" ? "grid-cols-1 md:grid-cols-[1fr_auto_auto]" : "grid-cols-1 md:grid-cols-[1fr_auto]"}`}>
                <div style={{ minWidth: 0 }}>
                  <LocationSelector location={location} setLocation={(l) => requestAuth(() => setLocation(l))} />
                </div>

                {searchMode === "nearby_area" && (
                  <select
                    value={radiusKm}
                    onChange={e => { const val = Number(e.target.value); requestAuth(() => setRadiusKm(val)); }}
                    style={selectStyle}
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
                )}

                <select
                  value={scanInterval}
                  onChange={e => { const val = Number(e.target.value); requestAuth(() => setScanInterval(val)); }}
                  style={selectStyle}
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
                  <option value={60}>Every 1 hr</option>
                  <option value={120}>Every 2 hrs</option>
                  <option value={240}>Every 4 hrs</option>
                  <option value={720}>Every 12 hrs</option>
                </select>
              </div>
            )}
            
            {searchMode === "multiple_pincodes" && (
              <div style={{
                display: "flex",
                flexDirection: "column",
                gap: "10px",
              }}>
                <div style={{
                  display: "flex",
                  alignItems: "center",
                  background: "var(--bg-input)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  padding: "6px 12px",
                  gap: "8px",
                  flexWrap: "wrap"
                }}>
                  {pincodes.map(p => (
                    <span key={p} style={{
                      background: "var(--color-brand-green)",
                      color: "white",
                      padding: "4px 8px",
                      borderRadius: "6px",
                      fontSize: "12px",
                      fontWeight: 600,
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px"
                    }}>
                      {p}
                      <button type="button" onClick={() => requestAuth(() => setPincodes(pincodes.filter(x => x !== p)))} style={{ cursor: "pointer", background: "none", border: "none", color: "white", padding: 0 }}>&times;</button>
                    </span>
                  ))}
                  <input
                    type="text"
                    placeholder="Enter pincode (e.g. 560001)..."
                    style={{
                      border: "none",
                      background: "transparent",
                      outline: "none",
                      color: "var(--text-primary)",
                      fontSize: "13px",
                      minWidth: "180px",
                      flex: 1
                    }}
                    onKeyDown={e => {
                      if (e.key === 'Enter' || e.key === ',') {
                        e.preventDefault();
                        const val = e.currentTarget.value.trim().substring(0, 6);
                        if (val.length === 6 && !isNaN(Number(val)) && !pincodes.includes(val) && pincodes.length < 10) {
                          requestAuth(() => setPincodes([...pincodes, val]));
                          e.currentTarget.value = "";
                        }
                      }
                    }}
                  />
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                  <select
                    value={scanInterval}
                    onChange={e => { const val = Number(e.target.value); requestAuth(() => setScanInterval(val)); }}
                    style={selectStyle}
                  >
                    <option value={5}>Every 5 mins</option>
                    <option value={15}>Every 15 mins</option>
                    <option value={30}>Every 30 mins</option>
                    <option value={60}>Every 1 hr</option>
                  </select>
                </div>
              </div>
            )}

          </div>
        </ConfigCard>

        {/* Keywords */}
        <ConfigCard
          icon={TextSearch}
          iconColor="var(--color-brand-green)"
          iconBg="rgba(22,163,74,0.1)"
          title="Keywords"
          description="Track specific brands or product names"
          count={keywords.length}
          countLabel="keywords"
        >
          <KeywordInput
            keywords={keywords}
            setKeywords={(k) => requestAuth(() => setKeywords(k))}
            categories={categories.map(c => c.name)}
            placeholder="Add a keyword..."
          />
        </ConfigCard>

        {/* Exclude Keywords */}
        <ConfigCard
          icon={FilterX}
          iconColor="var(--color-brand-red)"
          iconBg="rgba(220,38,38,0.08)"
          title="Exclude Keywords"
          description="Filter out unwanted matches"
          count={excludeKeywords.length}
          countLabel="excluded"
        >
          <KeywordInput
            keywords={excludeKeywords}
            setKeywords={(kws) => requestAuth(() => setExcludeKeywords(kws))}
            placeholder="Add keyword to exclude..."
            isExcludeMode={true}
          />
        </ConfigCard>
      </div>

      {/* ── WISHLIST TRACKING ──────────────────────────── */}
      <WishlistSection />

      

      {/* ── LIVE CONSOLE (injected) ────────────────────── */}
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
