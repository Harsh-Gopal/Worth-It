import { useState, useEffect } from "react";
import { Play, Square, RotateCcw, Grid3x3, Search, Ban, Target, MapPin } from "lucide-react";
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

// ── Config card sub-component ────────────────────────────────────────────────
function ConfigCard({ icon: Icon, iconColor, iconBg, title, description, count, countLabel, children }: any) {
  return (
    <div
      className="card"
      style={{
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
        height: "100%",
      }}
    >
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <div style={{
            width: "34px",
            height: "34px",
            borderRadius: "9px",
            background: iconBg || "var(--bg-input)",
            border: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: iconColor,
            flexShrink: 0,
          }}>
            <Icon className="w-4 h-4" />
          </div>
          <div>
            <h4 style={{ margin: 0, fontSize: "13.5px", fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.3 }}>{title}</h4>
            <p style={{ margin: 0, fontSize: "11.5px", color: "var(--text-muted)", lineHeight: 1.4, marginTop: "2px" }}>{description}</p>
          </div>
        </div>
        {count !== undefined && (
          <span style={{
            fontSize: "11px",
            fontWeight: 700,
            color: count > 0 ? "var(--color-brand-green)" : "var(--text-muted)",
            background: count > 0 ? "var(--ring-green)" : "transparent",
            border: count > 0 ? "1px solid rgba(22,163,74,0.2)" : "1px solid transparent",
            borderRadius: "20px",
            padding: "2px 10px",
            transition: "all 0.2s",
            flexShrink: 0,
          }}>
            {count} {countLabel}
          </span>
        )}
      </div>

      {/* Divider */}
      <div style={{ height: "1px", background: "var(--border)", opacity: 0.6 }} />

      {/* Content */}
      <div style={{ flex: 1 }}>
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
        {/* Indicator dot */}
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
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>([]);
  const [location, setLocation] = useState<{
    lat: number; lng: number; title: string;
    pincode?: string; local_store_id: string | null;
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
          selectedWishlistUrls = items.filter((i: any) => i.selected).map((i: any) => i.url);
        }
      }
    } catch (err) {
      console.error(err);
    }

    const category_rules: Record<string, any> = {};
    categories.forEach(c => { category_rules[c.name] = c.minDiscount !== null ? { min_discount_pct: c.minDiscount } : {}; });
    const keyword_rules: Record<string, any> = {};
    keywords.forEach(k => { keyword_rules[k.name] = k.minDiscount !== null ? { min_discount_pct: k.minDiscount } : {}; });

    onSearch({
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
      adaptive_mode: true,
    });
  };

  const handleHardReset = () => {
    onCancel();
    liveConsoleStore.clearLogs();
    liveConsoleStore.setScanState("IDLE");
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
      <div style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: "24px",
        flexWrap: "wrap",
        padding: "22px 24px",
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "14px",
        boxShadow: "var(--shadow-card)",
      }}>
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
        <div style={{
          display: "flex",
          gap: "10px",
          alignItems: "flex-end",
          flexWrap: "wrap",
          paddingTop: "22px",
        }}>
          {!isSearching ? (
            <button
              type="button"
              onClick={handleStartSearch}
              className="btn-primary"
              style={{ minWidth: "156px", height: "42px", fontSize: "14px" }}
            >
              <Play className="w-4 h-4 fill-current" />
              Start Tracking
            </button>
          ) : (
            <button
              type="button"
              onClick={onCancel}
              className="btn-danger"
              style={{ minWidth: "156px", height: "42px", fontSize: "14px" }}
            >
              <Square className="w-4 h-4 fill-current" />
              Stop Tracking
            </button>
          )}
          <button
            type="button"
            onClick={handleHardReset}
            className="btn-secondary"
            style={{ minWidth: "130px", height: "42px", fontSize: "14px" }}
          >
            <RotateCcw className="w-4 h-4" />
            Hard Reset
          </button>
        </div>
      </div>

      {/* ── SCAN PROGRESS BAR ─────────────────────────────── */}
      <ScanProgress intervalMinutes={initialConfig?.run_interval_minutes} isSearching={isSearching} />

      {/* ── 2×2 CONFIGURATION GRID ───────────────────────── */}
      <div
        className="search-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0,1fr) minmax(0,1fr)",
          gap: "16px",
        }}
      >
        {/* Target Categories */}
        <ConfigCard
          icon={Grid3x3}
          iconColor="#a855f7"
          iconBg="rgba(168,85,247,0.1)"
          title="Target Categories"
          description="Discover deals across broad product categories"
          count={categories.length}
          countLabel="categories"
        >
          <CategorySelector selected={categories} onSelect={setCategories} compact={false} />
        </ConfigCard>

        {/* Search Area & Timing */}
        <ConfigCard
          icon={MapPin}
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
              {(["current_pincode", "nearby_area"] as const).map(mode => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setSearchMode(mode)}
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
                  {mode === "current_pincode" ? "Current Pincode" : "Nearby Area"}
                </button>
              ))}
            </div>

            {/* Location + selects row */}
            <div style={{
              display: "grid",
              gridTemplateColumns: searchMode === "nearby_area" ? "1fr auto auto" : "1fr auto",
              gap: "10px",
              alignItems: "start",
            }}>
              <div style={{ minWidth: 0 }}>
                <LocationSelector location={location} setLocation={setLocation} />
              </div>

              {searchMode === "nearby_area" && (
                <select
                  value={radiusKm}
                  onChange={e => setRadiusKm(Number(e.target.value))}
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
                onChange={e => setScanInterval(Number(e.target.value))}
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
              </select>
            </div>
          </div>
        </ConfigCard>

        {/* Keywords */}
        <ConfigCard
          icon={Search}
          iconColor="var(--color-brand-green)"
          iconBg="rgba(22,163,74,0.1)"
          title="Keywords"
          description="Track specific brands or product names"
          count={keywords.length}
          countLabel="keywords"
        >
          <KeywordInput
            keywords={keywords}
            setKeywords={setKeywords}
            categories={categories.map(c => c.name)}
            placeholder="Add a keyword..."
          />
        </ConfigCard>

        {/* Exclude Keywords */}
        <ConfigCard
          icon={Ban}
          iconColor="var(--color-brand-red)"
          iconBg="rgba(220,38,38,0.08)"
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

      {/* ── WISHLIST TRACKING ──────────────────────────── */}
      <WishlistSection />

      {/* ── ACTIVE TARGETS SUMMARY ───────────────────── */}
      <ConfigCard
        icon={Target}
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
