import type { DealResult } from "../../lib/types";
import { ExternalLink, Tag, MapPin, Activity } from "lucide-react";

interface DealCardProps {
  deal: DealResult;
  onHover?: () => void;
  onClick?: () => void;
}

export default function DealCard({ deal, onHover, onClick }: DealCardProps) {
  const { product, store, discount_percent, historical_low_before_now, price_drop_percent, trigger_reasons, is_historical_low } = deal;
  
  const reasons = trigger_reasons || [];
  const isHistLow = is_historical_low || historical_low_before_now;

  return (
    <div 
      className="glass-panel glass-panel-hover p-4 cursor-pointer flex flex-col sm:flex-row gap-4 group relative overflow-hidden"
      onMouseEnter={onHover}
      onClick={onClick}
    >
      {/* Decorative pulse if deal is really good */}
      {isHistLow && (
        <div className="absolute -inset-4 bg-[var(--color-neon-green)] opacity-5 blur-3xl rounded-full group-hover:opacity-10 transition-opacity"></div>
      )}

      {/* Product Image Placeholder */}
      <div className="w-full sm:w-32 h-32 bg-[var(--color-radar-bg)] rounded-xl flex-shrink-0 flex items-center justify-center overflow-hidden border border-[var(--color-radar-border)] relative z-10">
        {product.image_url ? (
          <img src={product.image_url} alt={product.name} className="w-full h-full object-contain mix-blend-screen group-hover:scale-105 transition-transform duration-300" />
        ) : (
          <Tag className="w-8 h-8 text-[var(--color-text-muted)]" />
        )}
      </div>

      <div className="flex-1 flex flex-col relative z-10">
        <div className="flex justify-between items-start gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-white line-clamp-2 leading-tight mb-1 group-hover:text-[var(--color-neon-green)] transition-colors">
              {product.name}
            </h3>
            <p className="text-sm text-[var(--color-text-muted)] mb-2 truncate">
              {product.brand && <span className="font-medium text-[var(--color-text-muted)]">{product.brand}</span>}
              {product.brand && product.size && " • "}
              {product.size}
            </p>
          </div>
          <div className="flex flex-col items-end shrink-0">
            <span className="text-xl font-bold text-white neon-text">₹{product.price}</span>
            <span className="text-sm text-[var(--color-text-muted)] line-through">₹{product.mrp}</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-3">
          <div className="px-2 py-1 bg-[var(--color-radar-bg)] text-white text-xs font-bold rounded-md border border-[var(--color-deal-trigger)] shadow-[0_0_8px_rgba(255,59,59,0.3)] flex items-center gap-1">
            🔥 {discount_percent.toFixed(0)}% OFF
          </div>
          
          {isHistLow && (
            <div className="px-2 py-1 bg-[var(--color-radar-bg)] text-white text-xs font-bold rounded-md neon-border flex items-center gap-1">
              📉 HIST LOW
            </div>
          )}

          {price_drop_percent && price_drop_percent > 0 ? (
            <div className="px-2 py-1 bg-[var(--color-radar-bg)] text-white text-xs font-bold rounded-md border border-cyan-500 shadow-[0_0_8px_rgba(6,182,212,0.3)] flex items-center gap-1">
              <Activity className="w-3 h-3 text-cyan-400" /> {price_drop_percent.toFixed(1)}% DROP
            </div>
          ) : null}
        </div>

        <div className="mt-auto pt-3 border-t border-[var(--color-radar-border)] flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
            <MapPin className="w-3.5 h-3.5 text-[var(--color-neon-green)]" />
            <span className="font-medium text-white">{store.name}</span>
            {store.distance_km !== undefined && store.distance_km !== null && <span>• {store.distance_km.toFixed(1)} km</span>}
          </div>
          
          {product.product_url && (
            <a 
              href={product.product_url} 
              target="_blank" 
              rel="noreferrer"
              className="text-[var(--color-radar-bg)] hover:text-black flex items-center gap-1 text-xs font-bold bg-[var(--color-neon-green)] hover:bg-white px-3 py-1.5 rounded-lg transition-colors shadow-[0_0_10px_var(--color-neon-green-glow)]"
              onClick={(e) => e.stopPropagation()}
            >
              Buy <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
        
        {reasons.length > 0 && (
          <div className="mt-2 text-[10px] text-[var(--color-neon-green)] opacity-70 font-medium uppercase tracking-wider">
            Match: {reasons.join(", ")}
          </div>
        )}
      </div>
    </div>
  );
}

