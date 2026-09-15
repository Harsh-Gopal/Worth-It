import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import LocationSelector from './LocationSelector';
import DealCriteria from './DealCriteria';
import CategorySelector from './CategorySelector';
import KeywordInput from './KeywordInput';

interface ProductSearchProps {
  onSearch: (request: any) => void;
  isSearching: boolean;
  onCancel: () => void;
  compact?: boolean;
}

export default function ProductSearch({ onSearch, isSearching, onCancel, compact = false }: ProductSearchProps) {
  const [searchMode, setSearchMode] = useState<"keyword" | "wishlist">("keyword");
  
  const [categories, setCategories] = useState<string[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>([]);
  const [productUrls, setProductUrls] = useState<string[]>([]);
  
  const [location, setLocation] = useState<{lat: number, lng: number, title: string, local_store_id: string | null} | null>(null);
  const [radiusKm, setRadiusKm] = useState<number>(10);
  const RADIUS_OPTIONS = [3, 5, 10, 15, 20];

  const [criteria, setCriteria] = useState({
    min_discount_pct: 50,
    max_price: null,
    min_price_drop_pct: null,
    require_historical_low: false
  });

  const handleStartSearch = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Construct search request
    const req = {
      categories: searchMode === "keyword" ? categories : [],
      keywords: searchMode === "keyword" ? keywords : [],
      exclude_keywords: searchMode === "keyword" ? excludeKeywords : [],
      product_urls: searchMode === "wishlist" ? productUrls : [],
      min_discount_pct: criteria.min_discount_pct,
      max_price: criteria.max_price,
      min_price_drop_pct: criteria.min_price_drop_pct,
      require_historical_low: criteria.require_historical_low,
      lat: location?.lat,
      lng: location?.lng,
      local_store_id: location?.local_store_id,
      radius_km: radiusKm,
      expansion_strategy: 'NEARBY_FIRST'
    };
    
    onSearch(req);
  };

  const isFormValid = () => {
    if (searchMode === "keyword") {
      if (categories.length === 0 && keywords.length === 0) return false;
    } else {
      if (productUrls.length === 0) return false;
    }
    return true;
  };

  return (
    <div className={`glass-panel transition-all duration-700 ease-in-out ${compact ? 'p-5' : 'p-6 md:p-8'}`}>
      
      {/* Mode Switcher */}
      <div className="flex bg-[var(--color-radar-bg)] rounded-xl border border-[var(--color-radar-border)] p-1 w-full max-w-sm mb-6 mx-auto relative z-10">
        <button
          type="button"
          onClick={() => setSearchMode("keyword")}
          className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${
            searchMode === "keyword" 
              ? "bg-[var(--color-radar-panel-light)] text-[var(--color-neon-green)] shadow-[0_0_10px_var(--color-neon-green-glow)] border border-[var(--color-neon-green)]/30" 
              : "text-[var(--color-text-muted)] hover:text-white"
          }`}
        >
          Discover Deals
        </button>
        <button
          type="button"
          onClick={() => setSearchMode("wishlist")}
          className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${
            searchMode === "wishlist" 
              ? "bg-[var(--color-radar-panel-light)] text-[var(--color-neon-green)] shadow-[0_0_10px_var(--color-neon-green-glow)] border border-[var(--color-neon-green)]/30" 
              : "text-[var(--color-text-muted)] hover:text-white"
          }`}
        >
          Track Wishlist
        </button>
      </div>

      <form onSubmit={handleStartSearch} className="space-y-8 relative z-10">
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left Column: Target Definition */}
          <div className="space-y-6">
            
            {searchMode === "keyword" ? (
              <>
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1">Target Categories</h3>
                  <p className="text-xs text-[var(--color-text-muted)] mb-3 font-mono">Select one or more broad categories to monitor.</p>
                  <CategorySelector selected={categories} onSelect={setCategories} compact={compact} />
                </div>

                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1">Target Keywords</h3>
                  <p className="text-xs text-[var(--color-text-muted)] mb-3 font-mono">Specific brands or product names (e.g. whey protein, amul).</p>
                  <KeywordInput keywords={keywords} setKeywords={setKeywords} />
                </div>

                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1">Exclude Keywords</h3>
                  <p className="text-xs text-[var(--color-text-muted)] mb-3 font-mono">Ignore products containing these words (e.g. shaker, cookie).</p>
                  <KeywordInput keywords={excludeKeywords} setKeywords={setExcludeKeywords} />
                </div>
              </>
            ) : (
              <div>
                <h3 className="text-sm font-bold text-[var(--color-neon-green)] uppercase tracking-wider mb-1">Wishlist URLs</h3>
                <p className="text-xs text-[var(--color-text-muted)] mb-3 font-mono">Paste direct Instamart product URLs to track exactly these items.</p>
                <KeywordInput keywords={productUrls} setKeywords={setProductUrls} placeholder="https://www.swiggy.com/instamart/item/..." />
                <div className="mt-4 p-4 bg-[var(--color-radar-bg)] rounded-xl border border-[var(--color-radar-border)]">
                  <p className="text-xs text-[var(--color-text-muted)] font-mono leading-relaxed">
                    <span className="text-cyan-400 font-bold">&gt; TARGET_LOCK_ENGAGED</span><br/>
                    Wishlist mode bypasses category search and directly queries dark store inventory for the exact canonical product IDs extracted from your URLs.
                  </p>
                </div>
              </div>
            )}
            
          </div>

          {/* Right Column: Conditions & Area */}
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-1">Scan Perimeter</h3>
              <p className="text-xs text-[var(--color-text-muted)] mb-3 font-mono">Define the geographic boundaries of your scan.</p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-2">
                  <LocationSelector location={location} setLocation={setLocation} />
                </div>
                <div>
                  <select 
                    value={radiusKm} 
                    onChange={(e) => setRadiusKm(Number(e.target.value))}
                    className="w-full bg-[var(--color-radar-bg)] border border-[var(--color-radar-border)] text-white text-sm font-bold rounded-xl focus:ring-[var(--color-neon-green)] focus:border-[var(--color-neon-green)] block p-2.5 h-[46px] outline-none"
                  >
                    {RADIUS_OPTIONS.map(r => (
                      <option key={r} value={r}>{r} km Radius</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="bg-[var(--color-radar-bg)] border border-[var(--color-radar-border)] rounded-xl p-5">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">Trigger Conditions</h3>
              <DealCriteria criteria={criteria} setCriteria={setCriteria} />
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-[var(--color-radar-border)] flex justify-end">
           {isSearching ? (
             <button
               type="button"
               onClick={onCancel}
               className="w-full md:w-auto flex items-center justify-center gap-2 bg-[var(--color-radar-bg)] text-[var(--color-deal-trigger)] border border-[var(--color-deal-trigger)] font-bold py-3 px-8 rounded-xl hover:bg-[var(--color-deal-trigger)]/10 transition-colors shadow-[0_0_15px_rgba(255,59,59,0.2)]"
             >
               <Loader2 className="w-5 h-5 animate-spin" /> ABORT SCAN
             </button>
           ) : (
             <button
               type="submit"
               disabled={!isFormValid()}
               className="w-full md:w-auto flex items-center justify-center gap-2 bg-[var(--color-neon-green)] text-black font-extrabold py-3 px-10 rounded-xl hover:bg-white disabled:opacity-50 transition-all shadow-[0_0_20px_var(--color-neon-green-glow)]"
             >
               <Search className="w-5 h-5" /> INITIATE SCAN
             </button>
           )}
        </div>

      </form>
    </div>
  );
}
