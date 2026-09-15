import type { SearchStatus, SearchMetrics } from "../../hooks/useDealSearch";
import { CheckCircle2, AlertCircle, XCircle } from "lucide-react";
import clsx from "clsx";

interface SearchProgressProps {
  status: SearchStatus;
  metrics: SearchMetrics;
  error?: string | null;
}

export default function SearchProgress({ status, metrics, error }: SearchProgressProps) {
  if (status === "IDLE") return null;

  const isScanning = ["STARTING", "LOCAL_SEARCH", "EXPANDING_RADIUS", "SCANNING_STORES"].includes(status);
  
  return (
    <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex flex-col gap-4 transition-all">
      <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
        {isScanning ? (
          <div className="relative flex h-3 w-3 mr-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-brand-500"></span>
          </div>
        ) : status === "ERROR" || status === "CANCELLED" ? (
          <XCircle className="text-red-500 w-5 h-5" />
        ) : (
          <CheckCircle2 className="text-emerald-500 w-5 h-5" />
        )}
        
        <h3 className="font-semibold text-slate-800">
          {status === "STARTING" && "Initializing search..."}
          {status === "LOCAL_SEARCH" && "Checking your local store..."}
          {status === "EXPANDING_RADIUS" && `Expanding search to ${metrics.currentRadiusKm} km...`}
          {status === "SCANNING_STORES" && "Scanning discovered stores..."}
          {status === "DEAL_FOUND" && "🔥 Deals found! Scanning remaining stores..."}
          {status === "COMPLETED" && (metrics.dealsFound > 0 ? "Search completed." : "Search completed. No qualifying deals found.")}
          {status === "CANCELLED" && "Search cancelled."}
          {status === "ERROR" && "Search failed."}
        </h3>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Stores Discovered</span>
          <span className="font-medium text-slate-700">{metrics.storesDiscovered}</span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Stores Scanned</span>
          <span className="font-medium text-slate-700">
            {metrics.storesScanned} <span className="text-slate-400 font-normal">/ {metrics.storesDiscovered}</span>
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Relevant Products</span>
          <span className="font-medium text-slate-700">{metrics.productsFound}</span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-slate-500">Qualifying Deals</span>
          <span className={clsx("font-semibold", metrics.dealsFound > 0 ? "text-brand-600" : "text-slate-700")}>
            {metrics.dealsFound}
          </span>
        </div>
      </div>

      {error && (
        <div className="mt-2 p-3 bg-red-50 border border-red-100 rounded-lg flex gap-2 items-start text-red-700 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p>{error}</p>
        </div>
      )}
      
      {status === "COMPLETED" && metrics.elapsedTimeMs && (
        <div className="text-xs text-slate-400 text-right mt-1">
          Took {(metrics.elapsedTimeMs / 1000).toFixed(1)}s
        </div>
      )}
    </div>
  );
}
