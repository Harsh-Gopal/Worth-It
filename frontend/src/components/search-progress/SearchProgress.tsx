
import { Loader2, CheckCircle2, AlertCircle, MapPin, Store, PackageSearch, Target } from 'lucide-react';

interface SearchProgressProps {
  status: string;
  metrics: any;
  error: string | null;
}

export default function SearchProgress({ status, metrics, error }: SearchProgressProps) {
  if (status === "IDLE") return null;

  const isComplete = status === "COMPLETED";
  const hasError = !!error;

  return (
    <div className="glass-panel p-6 relative overflow-hidden">
      {/* Background sweep animation effect */}
      {!isComplete && !hasError && (
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[var(--color-neon-green-glow)] to-transparent opacity-20 -skew-x-12 animate-[sweep_2s_ease-in-out_infinite]" style={{ backgroundSize: '200% 100%' }}></div>
      )}

      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2 relative z-10">
        {!isComplete && !hasError && <Loader2 className="w-5 h-5 text-[var(--color-neon-green)] animate-spin" />}
        {isComplete && <CheckCircle2 className="w-5 h-5 text-[var(--color-neon-green)]" />}
        {hasError && <AlertCircle className="w-5 h-5 text-[var(--color-deal-trigger)]" />}
        Radar Telemetry
      </h3>
      
      {error ? (
        <div className="p-4 bg-[var(--color-radar-bg)] border border-[var(--color-deal-trigger)] rounded-xl flex items-start gap-3 text-red-400 relative z-10">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <p className="text-sm">{error}</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 relative z-10">
          <div className="bg-[var(--color-radar-bg)] rounded-xl p-4 border border-[var(--color-radar-border)]">
            <div className="flex items-center gap-2 text-[var(--color-text-muted)] mb-2">
              <MapPin className="w-4 h-4 text-cyan-400" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-cyan-400">Radius</span>
            </div>
            <p className="text-2xl font-bold text-white neon-text">
              {metrics.currentRadiusKm ? `${metrics.currentRadiusKm.toFixed(1)} km` : '-'}
            </p>
          </div>
          
          <div className="bg-[var(--color-radar-bg)] rounded-xl p-4 border border-[var(--color-radar-border)]">
            <div className="flex items-center gap-2 text-[var(--color-text-muted)] mb-2">
              <Store className="w-4 h-4 text-indigo-400" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-400">Stores Scanned</span>
            </div>
            <p className="text-2xl font-bold text-white">{metrics.storesScanned} / {metrics.storesDiscovered}</p>
          </div>

          <div className="bg-[var(--color-radar-bg)] rounded-xl p-4 border border-[var(--color-radar-border)]">
            <div className="flex items-center gap-2 text-[var(--color-text-muted)] mb-2">
              <PackageSearch className="w-4 h-4 text-purple-400" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-purple-400">Products Found</span>
            </div>
            <p className="text-2xl font-bold text-white">{metrics.productsFound || 0}</p>
          </div>

          <div className="bg-[var(--color-radar-bg)] rounded-xl p-4 border border-[var(--color-neon-green)] shadow-[0_0_10px_var(--color-neon-green-glow)]">
            <div className="flex items-center gap-2 text-[var(--color-neon-green)] mb-2">
              <Target className="w-4 h-4" />
              <span className="text-[10px] font-bold uppercase tracking-widest">Deals Matched</span>
            </div>
            <p className="text-2xl font-bold text-[var(--color-neon-green)] neon-text">{metrics.dealsFound || 0}</p>
          </div>
        </div>
      )}
      
      {!isComplete && !hasError && (
        <div className="mt-4 pt-4 border-t border-[var(--color-radar-border)] relative z-10">
          <div className="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
            <div className="w-2 h-2 rounded-full bg-[var(--color-neon-green)] animate-pulse shadow-[0_0_8px_var(--color-neon-green)]"></div>
            <span className="font-mono text-xs">
              {status === "STARTING" && "> INITIALIZING_RADAR..."}
              {status === "LOCAL_SEARCH" && "> CHECKING_LOCAL_STORE..."}
              {status === "EXPANDING_RADIUS" && `> EXPANDING_SWEEP_TO_${metrics.currentRadiusKm}KM...`}
              {status === "SCANNING_STORES" && "> PROBING_STORES_FOR_INVENTORY..."}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
