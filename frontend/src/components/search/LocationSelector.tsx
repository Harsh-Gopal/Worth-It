import React, { useState } from "react";
import { MapPin, Loader2, Search, X } from "lucide-react";
import { api } from "../../lib/api";

interface LocationSelectorProps {
  location: { lat: number; lng: number; title: string; local_store_id: string | null } | null;
  setLocation: (loc: any) => void;
}

export default function LocationSelector({ location, setLocation }: LocationSelectorProps) {
  const [query, setQuery] = useState("");
  const [isResolving, setIsResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleResolve = async () => {
    if (!query.trim()) return;
    setIsResolving(true);
    setError(null);
    try {
      const res = await api.get(`/location/resolve?address=${encodeURIComponent(query)}`);
      setLocation({
        lat: res.lat,
        lng: res.lng,
        title: res.address || query,
        local_store_id: res.local_store_id,
      });
      setQuery("");
    } catch (err: any) {
      setError(err.message || "Could not resolve location");
    } finally {
      setIsResolving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleResolve();
    }
  };

  if (location) {
    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "8px",
        padding: "9px 12px",
        background: "var(--ring-green)",
        border: "1px solid rgba(22,163,74,0.35)",
        borderRadius: "8px",
        height: "40px",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", overflow: "hidden", flex: 1, minWidth: 0 }}>
          <MapPin className="w-4 h-4" style={{ color: "var(--color-brand-green)", flexShrink: 0 }} />
          <span style={{
            fontSize: "13px",
            fontWeight: 600,
            color: "var(--text-primary)",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}>
            {location.title}
          </span>
        </div>
        <button
          type="button"
          onClick={() => setLocation(null)}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "22px",
            height: "22px",
            borderRadius: "50%",
            border: "none",
            background: "transparent",
            color: "var(--text-muted)",
            cursor: "pointer",
            flexShrink: 0,
            padding: 0,
          }}
          title="Clear location"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ position: "relative" }}>
        <MapPin className="w-4 h-4" style={{
          position: "absolute",
          left: "10px",
          top: "50%",
          transform: "translateY(-50%)",
          color: "var(--text-muted)",
          pointerEvents: "none",
        }} />
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. 560001, MG Road Bangalore…"
          style={{
            width: "100%",
            background: "var(--bg-input)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            color: "var(--text-primary)",
            fontSize: "13px",
            padding: "9px 40px 9px 32px",
            outline: "none",
            fontFamily: "inherit",
            height: "40px",
            boxSizing: "border-box",
            transition: "border-color 0.15s, box-shadow 0.15s",
          }}
          onFocus={e => {
            e.target.style.borderColor = "var(--color-brand-green)";
            e.target.style.boxShadow = "0 0 0 3px var(--ring-green)";
          }}
          onBlur={e => {
            e.target.style.borderColor = "var(--border)";
            e.target.style.boxShadow = "none";
          }}
        />
        <button
          type="button"
          onClick={handleResolve}
          disabled={isResolving || !query.trim()}
          style={{
            position: "absolute",
            right: "8px",
            top: "50%",
            transform: "translateY(-50%)",
            background: "transparent",
            border: "none",
            cursor: query.trim() ? "pointer" : "default",
            padding: 0,
            display: "flex",
            alignItems: "center",
            color: "var(--color-brand-green)",
            opacity: query.trim() ? 1 : 0.4,
          }}
        >
          {isResolving
            ? <Loader2 className="w-4 h-4 animate-spin" />
            : <Search className="w-4 h-4" />
          }
        </button>
      </div>
      {error && (
        <p style={{ fontSize: "12px", color: "var(--color-brand-red)", marginTop: "4px" }}>
          {error}
        </p>
      )}
    </div>
  );
}
