const CATEGORIES = [
  "Sports & Fitness",
  "Beauty & Grooming",
  "Baby Care",
  "Snacks & Beverages",
  "Pet Care",
  "Home & Kitchen",
  "Electronics",
  "Daily Essentials",
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
        onChange={e => onSelect([e.target.value])}
        style={{
          width: "100%",
          background: "var(--bg-input)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          color: "var(--text-primary)",
          fontSize: "13px",
          padding: "9px 12px",
          outline: "none",
          cursor: "pointer",
          fontFamily: "inherit",
          height: "40px",
        }}
      >
        <option value="" disabled>Select a category…</option>
        {CATEGORIES.map(c => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
    );
  }

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
      {CATEGORIES.map(category => {
        const active = selected.includes(category);
        return (
          <button
            key={category}
            type="button"
            onClick={() => toggleCategory(category)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              fontSize: "12px",
              fontWeight: 600,
              padding: "5px 12px",
              borderRadius: "6px",
              border: active
                ? "1px solid var(--color-brand-green)"
                : "1px solid var(--border)",
              background: active
                ? "var(--ring-green)"
                : "var(--bg-muted)",
              color: active
                ? "var(--color-brand-green)"
                : "var(--text-secondary)",
              cursor: "pointer",
              transition: "all 0.15s ease",
              fontFamily: "inherit",
              letterSpacing: "0.01em",
            }}
          >
            {category}
          </button>
        );
      })}
    </div>
  );
}
