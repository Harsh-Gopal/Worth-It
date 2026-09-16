

interface DealCriteriaProps {
  criteria: any;
  setCriteria: (criteria: any) => void;
}

export default function DealCriteria({ criteria, setCriteria }: DealCriteriaProps) {
  const update = (key: string, value: any) => {
    setCriteria({ ...criteria, [key]: value });
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      <div>
        <label className="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1">Min Discount %</label>
        <div className="relative">
          <input 
            type="number" 
            className="input-field block w-full p-2 outline-none text-[var(--text-primary)] font-bold" 
            placeholder="50"
            value={criteria.min_discount_pct || ''}
            onChange={(e) => update('min_discount_pct', e.target.value ? parseFloat(e.target.value) : null)}
          />
          <span className="absolute inset-y-0 right-3 flex items-center text-[var(--color-brand-red)] font-bold text-sm pointer-events-none">%</span>
        </div>
      </div>
      
      <div>
        <label className="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1">Max Price (₹)</label>
        <div className="relative">
          <input 
            type="number" 
            className="input-field block w-full p-2 pl-7 outline-none text-[var(--text-primary)] font-bold" 
            placeholder="e.g. 500"
            value={criteria.max_price || ''}
            onChange={(e) => update('max_price', e.target.value ? parseFloat(e.target.value) : null)}
          />
          <span className="absolute inset-y-0 left-3 flex items-center text-[var(--text-secondary)] font-bold text-sm pointer-events-none">₹</span>
        </div>
      </div>

      <div>
        <label className="block text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-1">Price Drop %</label>
        <div className="relative">
          <input 
            type="number" 
            className="input-field block w-full p-2 outline-none text-[var(--text-primary)] font-bold" 
            placeholder="e.g. 10"
            value={criteria.min_price_drop_pct || ''}
            onChange={(e) => update('min_price_drop_pct', e.target.value ? parseFloat(e.target.value) : null)}
          />
          <span className="absolute inset-y-0 right-3 flex items-center text-[var(--color-brand-green)] font-bold text-sm pointer-events-none">%</span>
        </div>
      </div>

      <div className="flex items-center mt-6">
        <label className="relative flex items-center cursor-pointer group">
          <input 
            type="checkbox" 
            className="sr-only peer"
            checked={criteria.require_historical_low}
            onChange={(e) => update('require_historical_low', e.target.checked)}
          />
          <div className="w-9 h-5 bg-[var(--border-color)] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-[var(--border-color)] after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[var(--color-brand-green)] shadow-inner"></div>
          <span className="ml-2 text-sm font-bold text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">Historical Low Only</span>
        </label>
      </div>
    </div>
  );
}
