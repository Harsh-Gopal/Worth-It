/**
 * LocationSelector — pincode / address autocomplete with live suggestions.
 *
 * Uses the /api/location/suggest endpoint (backed by Nominatim) to provide
 * real-time autocomplete as the user types a pincode or locality name.
 * On selection, coordinates are pre-resolved from the suggestion (no extra round-trip).
 * If needed, a fallback resolve call is made via /api/location/resolve.
 *
 * Previous problem: only had a plain input + resolve button; no autocomplete,
 * and used the broken /api/location/resolve which crashed with:
 *   'StoreResolution' object has no attribute 'external_store_id'
 * That backend bug is now fixed; this component adds proper UX on top.
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import { MapPin, Loader2, X, Search } from "lucide-react";
import { api } from "../../lib/api";

interface Suggestion {
  place_id: string;
  display_name: string;
  main_text: string;
  secondary_text: string;
  lat?: number;
  lng?: number;
}

interface LocationValue {
  lat: number;
  lng: number;
  title: string;
  pincode?: string;
  local_store_id: string | null;
}

interface LocationSelectorProps {
  location: LocationValue | null;
  setLocation: (loc: LocationValue | null) => void;
}

function useDebounce<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}

export default function LocationSelector({ location, setLocation }: LocationSelectorProps) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [focusedIdx, setFocusedIdx] = useState(-1);

  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const debouncedQuery = useDebounce(query, 350);

  // Fetch suggestions when debounced query changes
  useEffect(() => {
    if (debouncedQuery.trim().length < 2) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    // Cancel previous request
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setIsFetching(true);
    fetch(`/api/location/suggest?q=${encodeURIComponent(debouncedQuery)}`, {
      signal: abortRef.current.signal,
    })
      .then((r) => r.json())
      .then((data) => {
        setSuggestions(data.suggestions || []);
        setShowDropdown(true);
        setFocusedIdx(-1);
      })
      .catch((e) => {
        if (e.name !== "AbortError") {
          setSuggestions([]);
        }
      })
      .finally(() => setIsFetching(false));
  }, [debouncedQuery]);

  // Close dropdown on outside click
  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const isPincode = (str: string) => /^\d{6}$/.test(str.trim());

  const resolveAndSelect = useCallback(
    async (suggestion: Suggestion) => {
      setShowDropdown(false);
      
      let detectedPincode: string | undefined = undefined;
      if (isPincode(suggestion.main_text)) {
        detectedPincode = suggestion.main_text.trim();
      } else if (isPincode(query)) {
        detectedPincode = query.trim();
      }

      setQuery("");
      setError(null);

      // If the suggestion already has lat/lng (from Nominatim search endpoint), use them directly
      if (suggestion.lat !== undefined && suggestion.lng !== undefined) {
        setIsLoading(true);
        try {
          // Still call resolve to get local_store_id
          const res = await api.get(
            `/location/resolve?address=${encodeURIComponent(suggestion.display_name)}`
          );
          setLocation({
            lat: suggestion.lat,
            lng: suggestion.lng,
            title: suggestion.main_text || suggestion.display_name,
            pincode: detectedPincode,
            local_store_id: res.local_store_id ?? null,
          });
        } catch {
          // Degraded mode: no store ID, still set coords
          setLocation({
            lat: suggestion.lat!,
            lng: suggestion.lng!,
            title: suggestion.main_text || suggestion.display_name,
            pincode: detectedPincode,
            local_store_id: null,
          });
        } finally {
          setIsLoading(false);
        }
      } else {
        // Fallback: resolve by display name
        setIsLoading(true);
        try {
          const res = await api.get(
            `/location/resolve?address=${encodeURIComponent(suggestion.display_name)}`
          );
          setLocation({
            lat: res.lat,
            lng: res.lng,
            title: suggestion.main_text || res.address || suggestion.display_name,
            pincode: detectedPincode,
            local_store_id: res.local_store_id ?? null,
          });
        } catch (e: any) {
          setError(e.message || "Could not resolve location");
        } finally {
          setIsLoading(false);
        }
      }
    },
    [setLocation, query]
  );

  // Manual resolve from input when user presses Enter or clicks Search
  const handleManualResolve = useCallback(async () => {
    const q = query.trim();
    if (!q) return;
    
    let detectedPincode: string | undefined = undefined;
    if (isPincode(q)) {
      detectedPincode = q;
    }

    setIsLoading(true);
    setError(null);
    setShowDropdown(false);
    try {
      const res = await api.get(`/location/resolve?address=${encodeURIComponent(q)}`);
      setLocation({
        lat: res.lat,
        lng: res.lng,
        title: res.address || q,
        pincode: detectedPincode,
        local_store_id: res.local_store_id ?? null,
      });
      setQuery("");
    } catch (e: any) {
      setError(e.message || "Could not resolve location");
    } finally {
      setIsLoading(false);
    }
  }, [query, setLocation]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedIdx((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedIdx((i) => Math.max(i - 1, -1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (focusedIdx >= 0 && suggestions[focusedIdx]) {
        resolveAndSelect(suggestions[focusedIdx]);
      } else {
        handleManualResolve();
      }
    } else if (e.key === "Escape") {
      setShowDropdown(false);
    }
  };

  // ── Show confirmed location ────────────────────────────────────────────────
  if (location) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "8px",
          padding: "9px 12px",
          background: "var(--ring-green)",
          border: "1px solid rgba(22,163,74,0.35)",
          borderRadius: "8px",
          height: "40px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px", overflow: "hidden", flex: 1, minWidth: 0 }}>
          <MapPin className="w-4 h-4" style={{ color: "var(--color-brand-green)", flexShrink: 0 }} />
          <span
            style={{
              fontSize: "13px",
              fontWeight: 600,
              color: "var(--text-primary)",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {location.pincode || location.title}
          </span>
          {location.local_store_id && (
            <span style={{ fontSize: "10px", color: "var(--text-muted)", flexShrink: 0 }}>
              Store: {location.local_store_id.replace("synthetic_", "~")}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={() => setLocation(null)}
          style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            width: "22px", height: "22px", borderRadius: "50%", border: "none",
            background: "transparent", color: "var(--text-muted)", cursor: "pointer", flexShrink: 0, padding: 0,
          }}
          title="Clear location"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  // ── Input + dropdown ───────────────────────────────────────────────────────
  return (
    <div style={{ position: "relative" }} ref={wrapperRef}>
      {/* Input row */}
      <div style={{ position: "relative" }}>
        <MapPin
          className="w-4 h-4"
          style={{
            position: "absolute", left: "10px", top: "50%",
            transform: "translateY(-50%)", color: "var(--text-muted)", pointerEvents: "none",
          }}
        />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
          placeholder="Enter pincode or locality (e.g. 800014)"
          disabled={isLoading}
          style={{
            width: "100%",
            padding: "9px 38px 9px 34px",
            background: "var(--bg-input)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            fontSize: "13px",
            color: "var(--text-primary)",
            fontFamily: "inherit",
            outline: "none",
            height: "40px",
            boxSizing: "border-box",
          }}
          onFocusCapture={(e) => {
            e.currentTarget.style.borderColor = "var(--color-brand-green)";
            e.currentTarget.style.boxShadow = "0 0 0 3px var(--ring-green)";
          }}
          onBlurCapture={(e) => {
            e.currentTarget.style.borderColor = "var(--border)";
            e.currentTarget.style.boxShadow = "none";
          }}
        />
        <button
          type="button"
          onClick={handleManualResolve}
          disabled={isLoading || !query.trim()}
          style={{
            position: "absolute", right: "6px", top: "50%", transform: "translateY(-50%)",
            background: "transparent", border: "none", cursor: "pointer",
            color: query.trim() ? "var(--color-brand-green)" : "var(--text-muted)",
            display: "flex", alignItems: "center", padding: "4px",
          }}
          title="Resolve location"
        >
          {isLoading || isFetching ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Search className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <p style={{ fontSize: "12px", color: "var(--color-brand-red)", marginTop: "4px" }}>
          {error}
        </p>
      )}

      {/* Suggestions dropdown */}
      {showDropdown && suggestions.length > 0 && (
        <div
          style={{
            position: "absolute", top: "100%", left: 0, right: 0, marginTop: "4px",
            background: "var(--bg-surface)", border: "1px solid var(--border)",
            borderRadius: "8px", boxShadow: "var(--shadow-card)",
            zIndex: 1000, overflow: "hidden", maxHeight: "260px", overflowY: "auto",
          }}
        >
          {suggestions.map((s, idx) => (
            <button
              key={s.place_id || idx}
              type="button"
              onMouseDown={(e) => {
                e.preventDefault(); // prevent blur before click
                resolveAndSelect(s);
              }}
              onMouseEnter={() => setFocusedIdx(idx)}
              style={{
                display: "flex", flexDirection: "column", alignItems: "flex-start",
                width: "100%", padding: "10px 14px", border: "none", borderBottom: "1px solid var(--border)",
                background: idx === focusedIdx ? "var(--bg-surface-hover)" : "transparent",
                cursor: "pointer", textAlign: "left", gap: "2px",
                transition: "background 0.1s",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <MapPin className="w-3 h-3" style={{ color: "var(--color-brand-green)", flexShrink: 0 }} />
                <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
                  {s.main_text}
                </span>
              </div>
              {s.secondary_text && (
                <span
                  style={{
                    fontSize: "11px", color: "var(--text-muted)", paddingLeft: "18px",
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                    maxWidth: "100%",
                  }}
                >
                  {s.secondary_text}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* No results hint */}
      {showDropdown && debouncedQuery.length >= 2 && suggestions.length === 0 && !isFetching && (
        <div
          style={{
            position: "absolute", top: "100%", left: 0, right: 0, marginTop: "4px",
            background: "var(--bg-surface)", border: "1px solid var(--border)",
            borderRadius: "8px", padding: "10px 14px",
            fontSize: "12px", color: "var(--text-muted)", zIndex: 1000, boxShadow: "var(--shadow-card)",
          }}
        >
          No results — press ↵ to resolve "{debouncedQuery}" directly
        </div>
      )}
    </div>
  );
}
