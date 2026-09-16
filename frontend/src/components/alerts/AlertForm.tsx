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

const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-input)",
  border: "1px solid var(--border)",
  borderRadius: "8px",
  color: "var(--text-primary)",
  fontSize: "14px",
  padding: "9px 12px 9px 36px",
  outline: "none",
  fontFamily: "inherit",
  boxSizing: "border-box",
  transition: "border-color 0.15s, box-shadow 0.15s",
};

import React from "react";

export default function AlertForm({
  initialKeyword = "",
  initialDiscount = 50,
  initialRadius = 10,
  onSubmit,
  onCancel,
}: AlertFormProps) {
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

  const onFocus = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => {
    e.target.style.borderColor = "var(--color-brand-green)";
    e.target.style.boxShadow = "0 0 0 3px var(--ring-green)";
  };
  const onBlur = (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => {
    e.target.style.borderColor = "var(--border)";
    e.target.style.boxShadow = "none";
  };

  return (
    <div style={{
      background: "var(--bg-surface)",
      border: "1px solid var(--border)",
      borderRadius: "12px",
      overflow: "hidden",
      width: "100%",
      maxWidth: "420px",
      margin: "0 auto",
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "14px 16px",
        borderBottom: "1px solid var(--border)",
      }}>
        <h3 style={{
          fontSize: "14px",
          fontWeight: 600,
          color: "var(--text-primary)",
          margin: 0,
          display: "flex",
          alignItems: "center",
          gap: "6px",
        }}>
          <Bell className="w-4 h-4" style={{ color: "var(--color-brand-green)" }} />
          Create Deal Alert
        </h3>
        <button
          onClick={onCancel}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "var(--text-muted)",
            padding: 0,
            display: "flex",
          }}
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit} style={{ padding: "16px", display: "flex", flexDirection: "column", gap: "14px" }}>
        <div>
          <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
            Product Keyword
          </label>
          <div style={{ position: "relative" }}>
            <Search className="w-4 h-4" style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)", pointerEvents: "none" }} />
            <input
              type="text"
              required
              value={keyword}
              onChange={e => setKeyword(e.target.value)}
              style={inputStyle}
              onFocus={onFocus}
              onBlur={onBlur}
              placeholder="e.g. amul butter, whey protein"
            />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          <div>
            <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
              Min Discount
            </label>
            <div style={{ position: "relative" }}>
              <Percent className="w-4 h-4" style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)", pointerEvents: "none" }} />
              <input
                type="number"
                min="0"
                max="100"
                value={minDiscount}
                onChange={e => setMinDiscount(parseInt(e.target.value) || 0)}
                style={inputStyle}
                onFocus={onFocus}
                onBlur={onBlur}
              />
            </div>
          </div>
          <div>
            <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
              Search Radius
            </label>
            <div style={{ position: "relative" }}>
              <MapPin className="w-4 h-4" style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)", pointerEvents: "none" }} />
              <select
                value={radiusKm}
                onChange={e => setRadiusKm(parseInt(e.target.value))}
                style={{ ...inputStyle, appearance: "none" }}
                onFocus={onFocus}
                onBlur={onBlur}
              >
                <option value={3}>3 km</option>
                <option value={5}>5 km</option>
                <option value={10}>10 km</option>
                <option value={15}>15 km</option>
              </select>
            </div>
          </div>
        </div>

        <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={inStock}
            onChange={e => setInStock(e.target.checked)}
            style={{ accentColor: "var(--color-brand-green)", width: "16px", height: "16px", cursor: "pointer" }}
          />
          <span style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-primary)" }}>
            Must be in stock
          </span>
        </label>

        <button type="submit" className="btn-primary" style={{ width: "100%", justifyContent: "center" }}>
          <Bell className="w-4 h-4" /> Save Alert
        </button>
      </form>
    </div>
  );
}
