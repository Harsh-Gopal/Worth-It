import { useState } from "react";
import type { AlertRule } from "../../lib/types";
import { Bell, Search, Percent, MapPin, X } from "lucide-react";

interface AlertFormProps {
  initialKeyword?: string;
  initialDiscount?: number;
  initialRadius?: number;
  onSubmit: (rule: Partial<AlertRule>) => void;
  onCancel: () => void;
}

export default function AlertForm({ initialKeyword = "", initialDiscount = 50, initialRadius = 10, onSubmit, onCancel }: AlertFormProps) {
  const [keyword, setKeyword] = useState(initialKeyword);
  const [minDiscount, setMinDiscount] = useState(initialDiscount);
  const [radiusKm, setRadiusKm] = useState(initialRadius);
  const [inStock, setInStock] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) return;

    onSubmit({
      categories: [],
      keywords: [keyword.trim()],
      exclude_keywords: [],
      min_discount_pct: minDiscount || undefined,
      radius_km: radiusKm,
      require_in_stock: inStock,
      enabled: true,
      condition_operator: "AND",
      expansion_strategy: "NEARBY_FIRST",
      ranking_strategy: "BEST_DISCOUNT",
      platform: "instamart",
      cooldown_hours: 24,
    });
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden w-full max-w-md mx-auto relative z-50">
      <div className="flex justify-between items-center p-4 border-b border-slate-100 bg-brand-50">
        <h3 className="font-bold text-slate-800 flex items-center gap-2">
          <Bell className="w-5 h-5 text-brand-600" />
          Create Deal Alert
        </h3>
        <button onClick={onCancel} className="text-slate-400 hover:text-slate-600">
          <X className="w-5 h-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="p-6 flex flex-col gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Product Keyword</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
            <input
              type="text"
              required
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Min Discount</label>
            <div className="relative">
              <Percent className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
              <input
                type="number"
                min="0"
                max="100"
                value={minDiscount}
                onChange={(e) => setMinDiscount(parseInt(e.target.value) || 0)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Search Radius</label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 h-4 w-4" />
              <select
                value={radiusKm}
                onChange={(e) => setRadiusKm(parseInt(e.target.value))}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none appearance-none"
              >
                <option value={3}>3 km</option>
                <option value={5}>5 km</option>
                <option value={10}>10 km</option>
                <option value={15}>15 km</option>
              </select>
            </div>
          </div>
        </div>

        <div>
          <label className="flex items-center gap-2 cursor-pointer mt-2">
            <input
              type="checkbox"
              checked={inStock}
              onChange={(e) => setInStock(e.target.checked)}
              className="rounded text-brand-500 focus:ring-brand-500 w-4 h-4 cursor-pointer"
            />
            <span className="text-sm font-medium text-slate-700">Must be in stock</span>
          </label>
        </div>

        <button
          type="submit"
          className="w-full py-3 mt-4 rounded-xl font-semibold text-white bg-brand-600 hover:bg-brand-700 transition-colors shadow-sm flex justify-center items-center gap-2"
        >
          <Bell className="w-4 h-4" /> Save Alert
        </button>
      </form>
    </div>
  );
}
