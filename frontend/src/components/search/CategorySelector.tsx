

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
        className="w-full h-[46px] bg-[var(--color-radar-bg)] border border-[var(--color-radar-border)] text-white text-sm rounded-xl focus:ring-[var(--color-neon-green)] focus:border-[var(--color-neon-green)] block p-2.5 outline-none font-medium"
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
              ? 'bg-[var(--color-neon-green-glow)] text-[var(--color-neon-green)] border-[var(--color-neon-green)] shadow-[0_0_8px_var(--color-neon-green-glow)]'
              : 'bg-[var(--color-radar-bg)] text-[var(--color-text-muted)] border-[var(--color-radar-border)] hover:border-[var(--color-text-muted)] hover:text-white'
          }`}
        >
          {category}
        </button>
      ))}
    </div>
  );
}
