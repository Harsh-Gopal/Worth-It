interface DealCriteriaProps {
  criteria: {
    min_discount_pct: number | null;
    max_price: number | null;
    min_price_drop_pct: number | null;
    require_historical_low: boolean;
  };
  setCriteria: (criteria: any) => void;
}

const fieldStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "6px",
  minWidth: 0,
};

const labelStyle: React.CSSProperties = {
  fontSize: "11px",
  fontWeight: 600,
  color: "var(--text-secondary)",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
};

const helperStyle: React.CSSProperties = {
  fontSize: "11px",
  color: "var(--text-muted)",
  marginTop: "-2px",
};

const inputWrapStyle: React.CSSProperties = {
  position: "relative",
  display: "flex",
  alignItems: "center",
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-input)",
  border: "1px solid var(--border)",
  borderRadius: "8px",
  color: "var(--text-primary)",
  fontSize: "14px",
  padding: "9px 40px 9px 12px",
  outline: "none",
  transition: "border-color 0.15s ease, box-shadow 0.15s ease",
  fontFamily: "inherit",
  minWidth: 0,
  boxSizing: "border-box",
};

const unitStyle: React.CSSProperties = {
  position: "absolute",
  right: "12px",
  top: "50%",
  transform: "translateY(-50%)",
  fontSize: "13px",
  fontWeight: 600,
  color: "var(--text-muted)",
  pointerEvents: "none",
  userSelect: "none",
};

import React from "react";

export default function DealCriteria({ criteria, setCriteria }: DealCriteriaProps) {
  const update = (key: string, value: any) => {
    setCriteria({ ...criteria, [key]: value });
  };

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = "var(--color-brand-green)";
    e.target.style.boxShadow = "0 0 0 3px var(--ring-green)";
  };
  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = "var(--border)";
    e.target.style.boxShadow = "none";
  };

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
        gap: "16px",
      }}
    >
      {/* Min Discount */}
      <div style={fieldStyle}>
        <span style={labelStyle}>Min Discount</span>
        <span style={helperStyle}>Filter by minimum % off</span>
        <div style={inputWrapStyle}>
          <input
            type="number"
            min={0}
            max={100}
            style={inputStyle}
            placeholder="e.g. 50"
            value={criteria.min_discount_pct ?? ""}
            onChange={e => update("min_discount_pct", e.target.value ? parseFloat(e.target.value) : null)}
            onFocus={handleFocus}
            onBlur={handleBlur}
          />
          <span style={{ ...unitStyle, color: "var(--color-brand-red)" }}>%</span>
        </div>
      </div>

      {/* Max Price */}
      <div style={fieldStyle}>
        <span style={labelStyle}>Max Price</span>
        <span style={helperStyle}>Upper price limit</span>
        <div style={inputWrapStyle}>
          <input
            type="number"
            min={0}
            style={{ ...inputStyle, paddingLeft: "28px", paddingRight: "12px" }}
            placeholder="e.g. 500"
            value={criteria.max_price ?? ""}
            onChange={e => update("max_price", e.target.value ? parseFloat(e.target.value) : null)}
            onFocus={handleFocus}
            onBlur={handleBlur}
          />
          <span style={{ ...unitStyle, right: "auto", left: "10px", color: "var(--text-muted)" }}>₹</span>
        </div>
      </div>

      {/* Price Drop % */}
      <div style={fieldStyle}>
        <span style={labelStyle}>Price Drop %</span>
        <span style={helperStyle}>Recent price reduction</span>
        <div style={inputWrapStyle}>
          <input
            type="number"
            min={0}
            max={100}
            style={inputStyle}
            placeholder="e.g. 10"
            value={criteria.min_price_drop_pct ?? ""}
            onChange={e => update("min_price_drop_pct", e.target.value ? parseFloat(e.target.value) : null)}
            onFocus={handleFocus}
            onBlur={handleBlur}
          />
          <span style={{ ...unitStyle, color: "var(--color-brand-green)" }}>%</span>
        </div>
      </div>

      {/* Historical Low */}
      <div style={fieldStyle}>
        <span style={labelStyle}>Historical Low</span>
        <span style={helperStyle}>Only show all-time lows</span>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", paddingTop: "6px" }}>
          <button
            type="button"
            role="switch"
            aria-checked={criteria.require_historical_low}
            onClick={() => update("require_historical_low", !criteria.require_historical_low)}
            style={{
              position: "relative",
              width: "40px",
              height: "22px",
              borderRadius: "100px",
              border: "none",
              cursor: "pointer",
              flexShrink: 0,
              background: criteria.require_historical_low
                ? "var(--color-brand-green)"
                : "var(--border-strong)",
              transition: "background 0.2s ease",
              padding: 0,
            }}
          >
            <span
              style={{
                position: "absolute",
                top: "2px",
                left: criteria.require_historical_low ? "20px" : "2px",
                width: "18px",
                height: "18px",
                borderRadius: "50%",
                background: "#ffffff",
                transition: "left 0.2s ease",
                boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
              }}
            />
          </button>
          <span
            style={{
              fontSize: "13px",
              fontWeight: 500,
              color: criteria.require_historical_low ? "var(--color-brand-green)" : "var(--text-secondary)",
              transition: "color 0.2s ease",
            }}
          >
            {criteria.require_historical_low ? "Enabled" : "Disabled"}
          </span>
        </div>
      </div>
    </div>
  );
}
