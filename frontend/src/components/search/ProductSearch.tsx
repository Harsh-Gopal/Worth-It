import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import LocationSelector from './LocationSelector';
import DealCriteria from './DealCriteria';
import CategorySelector from './CategorySelector';
import KeywordInput from './KeywordInput';
import WishlistSection from './WishlistSection';

interface ProductSearchProps {
  onSearch: (request: any) => void;
  isSearching: boolean;
  onCancel: () => void;
  compact?: boolean;
}

export default function ProductSearch({ onSearch, isSearching, onCancel, compact = false }: ProductSearchProps) {
  
  const [categories, setCategories] = useState<string[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [excludeKeywords, setExcludeKeywords] = useState<string[]>([]);
  
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
    
    // Read directly from local storage to avoid complex context setup for MVP
    let selectedWishlistUrls: string[] = [];
    try {
      const stored = localStorage.getItem('worth_it_wishlist');
      if (stored) {
        const items = JSON.parse(stored);
        if (Array.isArray(items)) {
          selectedWishlistUrls = items.filter((i: any) => i.selected).map((i: any) => i.url);
        }
      }
    } catch (err) {
      console.error(err);
    }
    
    // Construct combined search request
    const req = {
      categories: categories,
      keywords: keywords,
      exclude_keywords: excludeKeywords,
      product_urls: selectedWishlistUrls,
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
    // Just a basic check. Actual validation depends on if there's anything to search
    // We can't synchronously check localStorage easily for this boolean state, so we just let them click it
    // and if both are empty, the backend will return nothing. But let's allow submission.
    return true; 
  };

  return (
    <div className={`surface-panel transition-all duration-700 ease-in-out ${compact ? 'p-5' : 'p-6 md:p-8'}`}>
      <div className="space-y-8 relative z-10">
        
        {/* Top Section: Wishlist */}
        <WishlistSection />
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left Column: Target Definition */}
          <div className="space-y-6">
            
            <div>
              <h3 className="text-sm font-semibold text-[var(--text-primary)] tracking-wide mb-1">Target Categories</h3>
              <p className="text-xs text-[var(--text-secondary)] mb-3">Optional. Discover deals across broad categories.</p>
              <CategorySelector selected={categories} onSelect={setCategories} compact={compact} />
            </div>

            <div>
              <h3 className="text-sm font-semibold text-[var(--text-primary)] tracking-wide mb-1">Keywords</h3>
              <p className="text-xs text-[var(--text-secondary)] mb-3">Optional. Specific brands or product names to search.</p>
              <KeywordInput keywords={keywords} setKeywords={setKeywords} />
            </div>

            {keywords.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)] tracking-wide mb-1">Exclude Keywords</h3>
                <KeywordInput keywords={excludeKeywords} setKeywords={setExcludeKeywords} />
              </div>
            )}
            
          </div>

          {/* Right Column: Conditions & Area */}
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-[var(--text-primary)] tracking-wide mb-1">Search Area</h3>
              <p className="text-xs text-[var(--text-secondary)] mb-3">Define the geographic boundaries of your scan.</p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-2">
                  <LocationSelector location={location} setLocation={setLocation} />
                </div>
                <div>
                  <select 
                    value={radiusKm} 
                    onChange={(e) => setRadiusKm(Number(e.target.value))}
                    className="input-field h-[46px]"
                  >
                    {RADIUS_OPTIONS.map(r => (
                      <option key={r} value={r}>{r} km Radius</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="bg-[var(--bg-main)] border border-[var(--border-color)] rounded-xl p-5">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] tracking-wide mb-4">Deal Criteria</h3>
              <DealCriteria criteria={criteria} setCriteria={setCriteria} />
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-[var(--border-color)] flex justify-end">
           {isSearching ? (
             <button
               type="button"
               onClick={onCancel}
               className="btn-danger w-full md:w-auto"
             >
               <Loader2 className="w-5 h-5 animate-spin" /> Stop Scan
             </button>
           ) : (
             <button
               type="button"
               onClick={handleStartSearch}
               disabled={!isFormValid()}
               className="btn-primary w-full md:w-auto disabled:opacity-50"
             >
               <Search className="w-5 h-5" /> Start Search
             </button>
           )}
        </div>

      </div>
    </div>
  );
}
