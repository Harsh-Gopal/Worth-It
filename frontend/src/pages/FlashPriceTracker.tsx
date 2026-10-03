import React, { useState, useEffect } from 'react';
import { API_BASE } from '../lib/api';
import { Loader2, Zap, AlertCircle, ShoppingCart } from 'lucide-react';
import { ProductImage } from '../components/common/ProductImage';
import { useAuthStore } from '../store/authStore';

interface FlashPriceResult {
  product_id: string;
  name: string | null;
  brand: string | null;
  image_url: string | null;
  normal_price: number | null;
  mrp: number | null;
  special_price: number | null;
  non_flash_price: number | null;
  flash_end_time: string | null;
  redemption_limit: number | null;
  extraction_method: string;
  serviceable: boolean;
  has_flash_sale: boolean;
  error: string | null;
}

export default function FlashPriceTracker() {
  const [urlInput, setUrlInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FlashPriceResult | null>(null);
  const { requestAuth } = useAuthStore();

  const [lat, setLat] = useState<number>(25.5941); // default Patna
  const [lng, setLng] = useState<number>(85.1376);

  useEffect(() => {
    // Try to get current location from Worth-It state if available
    const stored = localStorage.getItem('worth_it_location');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed.lat && parsed.lng) {
          setLat(parsed.lat);
          setLng(parsed.lng);
        }
      } catch (e) {
        // ignore
      }
    }
  }, []);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    requestAuth(async () => {
      setLoading(true);
      setError(null);
      setResult(null);

      try {
        const params = new URLSearchParams({
          url: urlInput.trim(),
          lat: lat.toString(),
          lng: lng.toString(),
        });

        const res = await fetch(`${API_BASE}/flash-price/lookup?${params}`);
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || 'Failed to lookup flash price');
        }

        const data = await res.json();
        setResult(data);
      } catch (err: any) {
        setError(err.message || 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    });
  };

  return (
    <div className="flex flex-col h-full bg-[var(--bg-page)] pb-[60px] md:pb-0">
      <div className="flex flex-col px-4 md:px-8 max-w-4xl w-full mx-auto pb-8 pt-4 md:pt-6">
        
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-blue-500/10 rounded-xl text-blue-500">
              <Zap size={24} strokeWidth={2.5} />
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-bold tracking-tight m-0 text-[var(--text-primary)] flex items-center gap-2">
                Instamart Flash Deals
              </h1>
              <p className="text-[13px] md:text-[14px] text-[var(--text-secondary)] mt-1">
                Extract hidden blue-highlighted promotional prices that regular trackers miss.
              </p>
            </div>
          </div>
        </div>

        {/* Input Card */}
        <div className="card p-4 md:p-6 flex flex-col gap-4 bg-[var(--bg-card)] border border-[var(--border)] rounded-[12px] shadow-sm mb-6">
          <form onSubmit={handleLookup} className="flex flex-col gap-4">
            <div>
              <label className="text-[12px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-2 block">
                Instamart Product URL
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="https://instamart.in/item/..."
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  className="input flex-1 bg-[var(--bg-input)] border border-[var(--border)] rounded-[8px] px-3 py-2 text-[14px] text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !urlInput.trim()}
                  className="btn btn-primary bg-blue-500 hover:bg-blue-600 text-white rounded-[8px] px-4 py-2 flex items-center justify-center min-w-[100px] disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-[14px]"
                >
                  {loading ? <Loader2 size={18} className="animate-spin" /> : 'Check'}
                </button>
              </div>
            </div>
            
            <div className="flex gap-4 items-center">
               <div className="flex flex-col">
                 <label className="text-[11px] font-medium text-[var(--text-secondary)] mb-1">Latitude</label>
                 <input 
                   type="number" 
                   step="any"
                   value={lat} 
                   onChange={(e) => setLat(Number(e.target.value))}
                   className="input bg-[var(--bg-input)] border border-[var(--border)] rounded-[6px] px-2 py-1.5 text-[12px] w-[120px]"
                 />
               </div>
               <div className="flex flex-col">
                 <label className="text-[11px] font-medium text-[var(--text-secondary)] mb-1">Longitude</label>
                 <input 
                   type="number" 
                   step="any"
                   value={lng} 
                   onChange={(e) => setLng(Number(e.target.value))}
                   className="input bg-[var(--bg-input)] border border-[var(--border)] rounded-[6px] px-2 py-1.5 text-[12px] w-[120px]"
                 />
               </div>
               <div className="flex-1 text-[11px] text-[var(--text-muted)] mt-4">
                 Coordinates determine which dark store responds.
               </div>
            </div>
          </form>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-[10px] flex items-start gap-3">
            <AlertCircle size={20} className="text-red-500 shrink-0 mt-0.5" />
            <div className="text-[14px] text-red-500 font-medium">
              {error}
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center p-12 gap-3 text-[var(--text-secondary)]">
            <Loader2 size={32} className="animate-spin text-blue-500" />
            <span className="text-[14px] font-medium animate-pulse">Extracting promotional price details...</span>
          </div>
        )}

        {/* Result State */}
        {result && !loading && (
          <div className="card bg-[var(--bg-card)] border border-[var(--border)] rounded-[12px] overflow-hidden shadow-sm animate-fade-in">
            {/* Result Header */}
            <div className="p-4 md:p-6 border-b border-[var(--border)] flex gap-4 md:gap-6 items-start">
              <div className="w-[80px] h-[80px] md:w-[100px] md:h-[100px] rounded-lg overflow-hidden shrink-0 border border-[var(--border)] bg-white flex items-center justify-center p-2">
                <ProductImage src={result.image_url || undefined} alt={result.name || 'Product'} />
              </div>
              <div className="flex flex-col flex-1 min-w-0">
                {result.brand && (
                  <span className="text-[12px] font-bold tracking-wider text-[var(--text-muted)] uppercase mb-1">
                    {result.brand}
                  </span>
                )}
                <h3 className="text-[16px] md:text-[18px] font-bold text-[var(--text-primary)] leading-snug mb-2 line-clamp-2">
                  {result.name || result.product_id}
                </h3>
                
                <div className="flex items-center gap-2 mt-auto">
                   <span className={`px-2 py-1 rounded-[4px] text-[11px] font-bold uppercase ${result.serviceable ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                     {result.serviceable ? 'Serviceable' : 'Unserviceable'}
                   </span>
                   {result.error && (
                     <span className="px-2 py-1 rounded-[4px] text-[11px] font-bold uppercase bg-yellow-500/10 text-yellow-500">
                       Warning: {result.error}
                     </span>
                   )}
                </div>
              </div>
            </div>

            {/* Price Details */}
            <div className="p-4 md:p-6 grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 bg-[var(--bg-surface)]">
              
              {/* Normal Price Box */}
              <div className="flex flex-col p-4 rounded-[10px] border border-[var(--border)] bg-[var(--bg-card)]">
                <div className="text-[12px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
                  Regular Offer Price
                </div>
                <div className="flex items-end gap-2 mt-2">
                  {result.normal_price !== null ? (
                    <>
                      <span className="text-[28px] font-bold text-[var(--text-primary)] leading-none">
                        ₹{result.normal_price}
                      </span>
                      {result.mrp && result.mrp > result.normal_price && (
                        <span className="text-[14px] text-[var(--text-muted)] line-through mb-1">
                          ₹{result.mrp}
                        </span>
                      )}
                    </>
                  ) : (
                    <span className="text-[16px] text-[var(--text-muted)] italic">Unavailable</span>
                  )}
                </div>
              </div>

              {/* Flash Price Box */}
              <div className={`flex flex-col p-4 rounded-[10px] border ${result.has_flash_sale ? 'border-blue-500/50 bg-blue-500/5' : 'border-[var(--border)] bg-[var(--bg-card)]'}`}>
                <div className="flex justify-between items-start mb-1">
                  <div className={`text-[12px] font-semibold uppercase tracking-wider ${result.has_flash_sale ? 'text-blue-500' : 'text-[var(--text-secondary)]'}`}>
                    Promotional Flash Price
                  </div>
                  {result.has_flash_sale && (
                    <div className="bg-blue-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-[4px] uppercase tracking-wider flex items-center gap-1">
                      <Zap size={10} className="fill-current" /> Active
                    </div>
                  )}
                </div>
                
                <div className="flex items-end gap-2 mt-2">
                  {result.has_flash_sale ? (
                    <>
                      <span className="text-[28px] font-bold text-blue-500 leading-none drop-shadow-sm">
                        ₹{result.special_price}
                      </span>
                      {result.flash_end_time && (
                        <span className="text-[13px] font-medium text-blue-500/80 mb-1">
                          Only till {result.flash_end_time}
                        </span>
                      )}
                    </>
                  ) : (
                    <span className="text-[16px] text-[var(--text-muted)] italic">No flash sale detected</span>
                  )}
                </div>
                
                {result.has_flash_sale && result.redemption_limit && (
                   <div className="mt-3 text-[12px] text-[var(--text-secondary)] flex items-center gap-1.5">
                     <ShoppingCart size={14} />
                     <span>Limit {result.redemption_limit} per user</span>
                   </div>
                )}
              </div>

            </div>
            
            {/* Developer Metadata */}
            <div className="bg-[#0f172a] text-[#94a3b8] p-3 text-[11px] font-mono flex items-center justify-between border-t border-[var(--border)]">
              <div>Method: {result.extraction_method}</div>
              {result.non_flash_price && (
                <div>Post-sale price: ₹{result.non_flash_price}</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
