
import type { TargetRule } from "../../lib/types";
import { X } from "lucide-react";
import { useState } from "react";
import DiscountPopover from "./DiscountPopover";

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

const DEFAULT_THRESHOLDS: Record<string, number> = {
  "Sports & Fitness": 30,
  "Beauty & Grooming": 15,
  "Baby Care": 10,
  "Snacks & Beverages": 10,
  "Pet Care": 10,
  "Home & Kitchen": 15,
  "Electronics": 20,
  "Daily Essentials": 5,
};

interface CategorySelectorProps {
  selected: TargetRule[];
  onSelect: (categories: TargetRule[]) => void;
  compact?: boolean;
}

export default function CategorySelector({ selected, onSelect, compact }: CategorySelectorProps) {
  const handleConfirmThreshold = (category: string, minDiscount: number | null) => {
    const existing = selected.find(c => c.name === category);
    if (existing) {
      onSelect(selected.map(c => c.name === category ? { ...c, minDiscount } : c));
    } else {
      onSelect([...selected, { name: category, minDiscount }]);
    }
  };

  const handleRemoveCategory = (category: string) => {
    onSelect(selected.filter(c => c.name !== category));
    if (activePopover === category) {
      setActivePopover(null);
    }
  };

  const [activePopover, setActivePopover] = useState<string | null>(null);
  const [activeAnchor, setActiveAnchor] = useState<HTMLElement | null>(null);

  if (compact) {
    return (
      <select
        value={selected.length > 0 ? selected[0].name : ""}
        onChange={e => {
          const val = e.target.value;
          const defaultPct = DEFAULT_THRESHOLDS[val] || 15;
          onSelect([{ name: val, minDiscount: defaultPct }]);
        }}
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
    <div style={{ position: "relative" }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
        {CATEGORIES.map(category => {
          const activeRule = selected.find(c => c.name === category);
          const active = !!activeRule;
          
          return (
            <div key={category} style={{ display: "inline-flex", alignItems: "center", position: "relative" }}>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
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
                  transition: "all 0.15s ease",
                  fontFamily: "inherit",
                  letterSpacing: "0.01em",
                }}
              >
                <button
                  type="button"
                  onClick={() => {
                    if (!active) {
                      handleConfirmThreshold(category, null);
                      setActivePopover(category);
                    }
                  }}
                  style={{
                    background: "none",
                    border: "none",
                    padding: 0,
                    margin: 0,
                    color: "inherit",
                    fontWeight: "inherit",
                    fontSize: "inherit",
                    cursor: active ? "default" : "pointer",
                    outline: "none"
                  }}
                >
                  {category}
                </button>
                {active && (
                  <div style={{ 
                    display: "inline-flex", 
                    alignItems: "center", 
                    background: activeRule.minDiscount !== null ? "rgba(34, 197, 94, 0.15)" : "transparent",
                    padding: "1px 4px",
                    borderRadius: "4px",
                    fontSize: "11px",
                    color: "var(--color-brand-green)"
                  }}>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (activePopover === category) {
                          setActivePopover(null);
                          setActiveAnchor(null);
                        } else {
                          setActivePopover(category);
                          setActiveAnchor(e.currentTarget);
                        }
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        padding: 0,
                        margin: 0,
                        color: "inherit",
                        fontWeight: "bold",
                        cursor: "pointer",
                        outline: "none"
                      }}
                    >
                      {activeRule.minDiscount !== null ? `≥${activeRule.minDiscount}%` : 'Set %'}
                    </button>
                    {activePopover === category && (
                      <DiscountPopover
                        targetName={category}
                        currentDiscount={activeRule.minDiscount}
                        anchorEl={activeAnchor}
                        onApply={(val) => {
                          handleConfirmThreshold(category, val ?? (DEFAULT_THRESHOLDS[category] || 15));
                          setActivePopover(null);
                          setActiveAnchor(null);
                        }}
                        onClose={() => {
                          setActivePopover(null);
                          setActiveAnchor(null);
                          if (activeRule.minDiscount === null) {
                            handleRemoveCategory(category);
                          }
                        }}
                      />
                    )}
                  </div>
                )}
                {active && (
                  <button
                    type="button"
                    onClick={() => handleRemoveCategory(category)}
                    style={{
                      background: "transparent",
                      border: "none",
                      padding: "4px",
                      cursor: "pointer",
                      color: "inherit",
                      display: "flex",
                      alignItems: "center",
                      marginLeft: "2px",
                      opacity: 0.7
                    }}
                    onMouseEnter={e => e.currentTarget.style.color = "var(--color-brand-red)"}
                    onMouseLeave={e => e.currentTarget.style.color = "inherit"}
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
