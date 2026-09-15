

const CATEGORIES = [
  "Sports & Fitness",
  "Beauty & Grooming",
  "Baby Care",
  "Snacks & Beverages",
  "Pet Care",
  "Home & Kitchen",
  "Electronics",
  "Daily Essentials"
];

interface CategorySelectorProps {
  selected: string[];
  onSelect: (categories: string[]) => void;
  compact?: boolean;
}

export default function CategorySelector({ selected, onSelect, compact }: CategorySelectorProps) {
  const toggleCategory = (category: string) => {
    if (selected.includes(category)) {
      onSelect(selected.filter(c => c !== category));
    } else {
      onSelect([...selected, category]);
    }
  };

  if (compact) {
    return (
      <select 
        value={selected.length > 0 ? selected[0] : ""} 
        onChange={(e) => onSelect([e.target.value])}
        className="w-full h-[46px] bg-[var(--bg-main)] border border-[var(--border-color)] text-white text-sm rounded-xl focus:ring-[var(--color-brand-green)] focus:border-[var(--color-brand-green)] block p-2.5 outline-none font-medium"
      >
        <option value="" disabled>Select a category...</option>
        {CATEGORIES.map(c => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {CATEGORIES.map(category => (
        <button
          key={category}
          type="button"
          onClick={() => toggleCategory(category)}
          className={`px-3 py-1.5 text-xs font-bold uppercase tracking-wider rounded-lg transition-all border ${
            selected.includes(category)
              ? 'bg-[var(--ring-color)] text-[var(--color-brand-green)] border-[var(--color-brand-green)] shadow-[0_0_8px_var(--ring-color)]'
              : 'bg-[var(--bg-main)] text-[var(--text-secondary)] border-[var(--border-color)] hover:border-[var(--text-secondary)] hover:text-white'
          }`}
        >
          {category}
        </button>
      ))}
    </div>
  );
}
