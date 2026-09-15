import type { DealResult } from "../../lib/types";
import { ExternalLink, Tag, MapPin, Activity, Bookmark } from "lucide-react";

interface DealCardProps {
  deal: DealResult & { source?: string };
  onHover?: () => void;
  onClick?: () => void;
}

export default function DealCard({ deal, onHover, onClick }: DealCardProps) {
  const { product, store, discount_percent, historical_low_before_now, price_drop_percent, trigger_reasons, is_historical_low, source } = deal;
  
  const reasons = trigger_reasons || [];
  const isHistLow = is_historical_low || historical_low_before_now;
  const isWishlist = source === "wishlist";

  return (
    <div 
      className="surface-panel surface-panel-hover p-4 cursor-pointer flex flex-col sm:flex-row gap-4 relative overflow-hidden"
      onMouseEnter={onHover}
      onClick={onClick}
    >
      {/* Product Image Placeholder */}
      <div className="w-full sm:w-32 h-32 bg-[var(--bg-main)] rounded-xl flex-shrink-0 flex items-center justify-center overflow-hidden border border-[var(--border-color)] relative z-10">
        {product.image_url ? (
          <img src={product.image_url} alt={product.name} className="w-full h-full object-contain" />
        ) : (
          <Tag className="w-8 h-8 text-[var(--text-muted)]" />
        )}
      </div>

      <div className="flex-1 flex flex-col relative z-10">
        <div className="flex justify-between items-start gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-[var(--text-primary)] line-clamp-2 leading-tight mb-1">
              {product.name}
            </h3>
            <p className="text-sm text-[var(--text-secondary)] mb-2 truncate">
              {product.brand && <span className="font-medium text-[var(--text-secondary)]">{product.brand}</span>}
              {product.brand && product.size && " • "}
              {product.size}
            </p>
          </div>
          <div className="flex flex-col items-end shrink-0">
            <span className="text-xl font-bold text-[var(--text-primary)]">₹{product.price}</span>
            <span className="text-sm text-[var(--text-secondary)] line-through">₹{product.mrp}</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-3">
          {isWishlist && (
            <div className="px-2 py-1 bg-[var(--bg-main)] text-[var(--text-primary)] text-xs font-bold rounded-md border border-[var(--color-brand-green)] flex items-center gap-1 shadow-sm">
              <Bookmark className="w-3 h-3 text-[var(--color-brand-green)]" fill="currentColor" /> Tracked
            </div>
          )}

          <div className="px-2 py-1 bg-[var(--color-brand-red)]/10 text-[var(--color-brand-red)] text-xs font-bold rounded-md border border-[var(--color-brand-red)]/20 flex items-center gap-1 shadow-sm">
            🔥 {discount_percent.toFixed(0)}% OFF
          </div>
          
          {isHistLow && (
            <div className="px-2 py-1 bg-[var(--color-brand-green)]/10 text-[var(--color-brand-green)] text-xs font-bold rounded-md border border-[var(--color-brand-green)]/20 flex items-center gap-1 shadow-sm">
              📉 HIST LOW
            </div>
          )}

          {price_drop_percent && price_drop_percent > 0 ? (
            <div className="px-2 py-1 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 text-xs font-bold rounded-md border border-cyan-500/20 flex items-center gap-1 shadow-sm">
              <Activity className="w-3 h-3" /> {price_drop_percent.toFixed(1)}% DROP
            </div>
          ) : null}
        </div>

        <div className="mt-auto pt-3 border-t border-[var(--border-color)] flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
            <MapPin className="w-3.5 h-3.5 text-[var(--color-brand-green)]" />
            <span className="font-medium text-[var(--text-primary)]">{store.name}</span>
            {store.distance_km !== undefined && store.distance_km !== null && <span>• {store.distance_km.toFixed(1)} km</span>}
          </div>
          
          {product.product_url && (
            <a 
              href={product.product_url} 
              target="_blank" 
              rel="noreferrer"
              className="text-white hover:text-white flex items-center gap-1 text-xs font-bold bg-[var(--color-brand-green)] hover:bg-[var(--color-brand-green-dark)] px-3 py-1.5 rounded-lg transition-colors"
              onClick={(e) => e.stopPropagation()}
            >
              Buy <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
        
        {reasons.length > 0 && !isWishlist && (
          <div className="mt-2 text-[10px] text-[var(--text-muted)] font-medium uppercase tracking-wider">
            Match: {reasons.join(", ")}
          </div>
        )}
      </div>
    </div>
  );
}
