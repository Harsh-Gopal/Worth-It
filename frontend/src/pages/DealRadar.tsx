import { useState } from "react";
import { useDealSearch } from "../hooks/useDealSearch";
import ProductSearch from "../components/search/ProductSearch";
import SearchProgress from "../components/search-progress/SearchProgress";
import DealList from "../components/deals/DealList";
import DealMap from "../components/map/DealMap";

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
    <div className="flex flex-col gap-6 w-full h-full">
      
      {/* Search Hero Area */}
      {!showResults && (
        <div className="mt-12 mb-8 flex flex-col items-center justify-center text-center px-4">
          <div className="relative mb-6">
            <div className="absolute inset-0 rounded-full bg-[var(--color-neon-green)] blur-2xl opacity-20 animate-pulse"></div>
            <img src="/logo.svg" alt="Worth-It" className="h-24 md:h-32 relative z-10" />
          </div>
          <p className="text-lg md:text-xl text-[var(--color-text-muted)] max-w-2xl mx-auto font-light leading-relaxed">
            Find the price worth buying. Deploy automated scans across dark stores to instantly locate historical lows and hidden discounts.
          </p>
        </div>
      )}

      {/* Main Search Component */}
      <div className={`transition-all duration-700 ease-in-out w-full ${showResults ? '' : 'max-w-4xl mx-auto'}`}>
        <ProductSearch 
          onSearch={handleSearch} 
          isSearching={isSearching}
          onCancel={cancelSearch}
          compact={showResults}
        />
      </div>

      {showResults && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-4 flex-1 min-h-0 pb-4">
          {/* Left Column: Progress & List */}
          <div className="lg:col-span-5 xl:col-span-4 flex flex-col gap-6 h-full overflow-y-auto pr-2 custom-scrollbar">
            <SearchProgress status={status} metrics={metrics} error={error} />
            <DealList deals={deals} />
          </div>

          {/* Right Column: Map */}
          <div className="lg:col-span-7 xl:col-span-8 h-[50vh] lg:h-full min-h-[400px] rounded-2xl overflow-hidden shadow-2xl border border-[var(--color-radar-border)] relative">
            <div className="absolute inset-0 bg-[var(--color-neon-green)] opacity-5 blur-xl"></div>
            <DealMap stores={stores} deals={deals} currentRadiusKm={metrics.currentRadiusKm} centerLat={searchIntent?.lat} centerLng={searchIntent?.lng} />
          </div>
        </div>
      )}
    </div>
  );
}
