import { useState } from "react";
import { useDealSearch } from "../hooks/useDealSearch";
import ProductSearch from "../components/search/ProductSearch";
import SearchProgress from "../components/search-progress/SearchProgress";
import DealList from "../components/deals/DealList";
import DealMap from "../components/map/DealMap";
import WorthItLogo from "../components/branding/WorthItLogo";

export default function DealRadar() {
  const { startSearch, cancelSearch, status, metrics, stores, deals, error } = useDealSearch();
  const [searchIntent, setSearchIntent] = useState<any>(null);

  const handleSearch = (req: any) => {
    setSearchIntent(req);
    startSearch(req);
  };

  const isSearching = ["STARTING", "LOCAL_SEARCH", "EXPANDING_RADIUS", "SCANNING_STORES"].includes(status);
  const showResults = status !== "IDLE" || isSearching;

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
            Find the price worth buying. Scan dark stores across your area to locate historical lows and hidden discounts.
          </p>
        </div>
      )}

      {/* Search form */}
      <div style={{ width: "100%" }}>
        <ProductSearch
          onSearch={handleSearch}
          isSearching={isSearching}
          onCancel={cancelSearch}
          compact={showResults}
        />
      </div>

      {/* Results */}
      {showResults && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "380px 1fr",
          gap: "20px",
          minHeight: "480px",
        }}
          className="results-grid"
        >
          {/* Left: progress + list */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", overflowY: "auto", minWidth: 0 }}>
            <SearchProgress status={status} metrics={metrics} error={error} />
            <DealList deals={deals} />
          </div>

          {/* Right: map */}
          <div style={{
            borderRadius: "12px",
            overflow: "hidden",
            border: "1px solid var(--border)",
            minHeight: "400px",
          }}>
            <DealMap
              stores={stores}
              deals={deals}
              currentRadiusKm={metrics.currentRadiusKm}
              centerLat={searchIntent?.lat}
              centerLng={searchIntent?.lng}
            />
          </div>
        </div>
      )}

      <style>{`
        @media (max-width: 1024px) {
          .results-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}
