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
    <div className="surface-panel p-6 relative overflow-hidden">
      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2 relative z-10">
        {!isComplete && !hasError && <Loader2 className="w-5 h-5 text-[var(--color-brand-green)] animate-spin" />}
        {isComplete && <CheckCircle2 className="w-5 h-5 text-[var(--color-brand-green)]" />}
        {hasError && <AlertCircle className="w-5 h-5 text-[var(--color-brand-red)]" />}
        Search Progress
      </h3>
      
      {error ? (
        <div className="p-4 bg-[var(--color-brand-red)]/10 border border-[var(--color-brand-red)]/30 rounded-xl flex items-start gap-3 text-[var(--color-brand-red)] relative z-10">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <p className="text-sm font-medium">{error}</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 relative z-10">
          <div className="bg-[var(--bg-main)] rounded-xl p-4 border border-[var(--border-color)]">
            <div className="flex items-center gap-2 text-[var(--text-secondary)] mb-2">
              <MapPin className="w-4 h-4" />
              <span className="text-[10px] font-bold uppercase tracking-widest">Radius</span>
            </div>
            <p className="text-2xl font-bold text-[var(--text-primary)]">
              {metrics.currentRadiusKm ? `${metrics.currentRadiusKm.toFixed(1)} km` : '-'}
            </p>
          </div>
          
          <div className="bg-[var(--bg-main)] rounded-xl p-4 border border-[var(--border-color)]">
            <div className="flex items-center gap-2 text-[var(--text-secondary)] mb-2">
              <Store className="w-4 h-4" />
              <span className="text-[10px] font-bold uppercase tracking-widest">Stores Scanned</span>
            </div>
            <p className="text-2xl font-bold text-[var(--text-primary)]">{metrics.storesScanned} / {metrics.storesDiscovered}</p>
          </div>

          <div className="bg-[var(--bg-main)] rounded-xl p-4 border border-[var(--border-color)]">
            <div className="flex items-center gap-2 text-[var(--text-secondary)] mb-2">
              <PackageSearch className="w-4 h-4" />
              <span className="text-[10px] font-bold uppercase tracking-widest">Products Found</span>
            </div>
            <p className="text-2xl font-bold text-[var(--text-primary)]">{metrics.productsFound || 0}</p>
          </div>

          <div className="bg-[var(--bg-main)] rounded-xl p-4 border border-[var(--color-brand-green)]/30 shadow-sm">
            <div className="flex items-center gap-2 text-[var(--color-brand-green)] mb-2">
              <Target className="w-4 h-4" />
              <span className="text-[10px] font-bold uppercase tracking-widest">Deals Matched</span>
            </div>
            <p className="text-2xl font-bold text-[var(--text-primary)]">{metrics.dealsFound || 0}</p>
          </div>
        </div>
      )}
      
      {!isComplete && !hasError && (
        <div className="mt-4 pt-4 border-t border-[var(--border-color)] relative z-10">
          <div className="flex items-center gap-3 text-sm text-[var(--text-secondary)]">
            <div className="w-2 h-2 rounded-full bg-[var(--color-brand-green)] animate-pulse"></div>
            <span className="font-medium text-xs tracking-wide">
              {status === "STARTING" && "Initializing scan..."}
              {status === "LOCAL_SEARCH" && "Checking local store..."}
              {status === "EXPANDING_RADIUS" && `Expanding sweep to ${metrics.currentRadiusKm}km...`}
              {status === "SCANNING_STORES" && "Probing stores for inventory..."}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
