import React, { useState } from "react";
import { Plus, Trash2, Loader2, Bookmark } from "lucide-react";
import { useWishlist } from "../../hooks/useWishlist";
import { ProductImage } from "../common/ProductImage";

export default function WishlistSection() {
  const { items, isLoading, error, addUrl, removeUrl, toggleSelection } = useWishlist();
  const [urlInput, setUrlInput] = useState("");

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = urlInput.trim();
    if (!trimmed) return;
    const success = await addUrl(trimmed);
    if (success) setUrlInput("");
  };

  const selectedCount = items.filter(i => i.selected).length;

  return (
    <div>
      {/* Section heading */}
      <div style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        marginBottom: "12px",
        gap: "12px",
        flexWrap: "wrap",
      }}>
        <div>
          <h3 style={{
            fontSize: "13px",
            fontWeight: 600,
            color: "var(--text-primary)",
            margin: "0 0 2px",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}>
            <Bookmark className="w-4 h-4" style={{ color: "var(--color-brand-green)" }} />
            Wishlist Tracking
          </h3>
          <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: 0 }}>
            Optional. Selected products are prioritized in results alongside category search.
          </p>
        </div>
        {items.length > 0 && (
          <span style={{
            fontSize: "11px",
            fontWeight: 700,
            color: selectedCount > 0 ? "var(--color-brand-green)" : "var(--text-muted)",
            background: selectedCount > 0 ? "var(--ring-green)" : "var(--bg-muted)",
            border: `1px solid ${selectedCount > 0 ? "rgba(22,163,74,0.3)" : "var(--border)"}`,
            borderRadius: "6px",
            padding: "3px 10px",
            flexShrink: 0,
          }}>
            {selectedCount}/{items.length} tracked
          </span>
        )}
      </div>

      {/* URL input */}
      <form onSubmit={handleAdd} style={{ display: "flex", gap: "8px", marginBottom: error ? "8px" : "12px" }}>
        <input
          type="url"
          placeholder="Paste Swiggy Instamart product URL…"
          value={urlInput}
          onChange={e => setUrlInput(e.target.value)}
          disabled={isLoading}
          style={{
            flex: 1,
            minWidth: 0,
            background: "var(--bg-input)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            color: "var(--text-primary)",
            fontSize: "13px",
            padding: "8px 12px",
            outline: "none",
            fontFamily: "inherit",
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
          type="submit"
          disabled={isLoading || !urlInput.trim()}
          className="btn-primary"
          style={{ padding: "8px 16px", flexShrink: 0, fontSize: "13px" }}
        >
          {isLoading
            ? <Loader2 className="w-4 h-4 animate-spin" />
            : <Plus className="w-4 h-4" />
          }
          <span style={{ display: "none" }} className="sm-visible">Add</span>
        </button>
      </form>

      {/* Error message */}
      {error && (
        <div style={{
          padding: "8px 12px",
          background: "var(--ring-red)",
          border: "1px solid rgba(220,38,38,0.25)",
          borderRadius: "6px",
          fontSize: "12px",
          color: "var(--color-brand-red)",
          marginBottom: "10px",
        }}>
          {error}
        </div>
      )}

      {/* Wishlist items */}
      {items.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "6px", maxHeight: "260px", overflowY: "auto" }}
          className="custom-scrollbar"
        >
          {items.map(item => (
            <div
              key={item.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "10px 12px",
                background: item.selected ? "var(--ring-green)" : "var(--bg-muted)",
                border: item.selected
                  ? "1px solid rgba(22,163,74,0.3)"
                  : "1px solid var(--border)",
                borderRadius: "8px",
                transition: "all 0.15s",
              }}
            >
              {/* Checkbox */}
              <label style={{
                position: "relative",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                flexShrink: 0,
              }}>
                <input
                  type="checkbox"
                  checked={item.selected}
                  onChange={() => toggleSelection(item.id)}
                  style={{ position: "absolute", opacity: 0, width: 0, height: 0 }}
                />
                <div style={{
                  width: "18px",
                  height: "18px",
                  borderRadius: "4px",
                  border: item.selected
                    ? "2px solid var(--color-brand-green)"
                    : "2px solid var(--border-strong)",
                  background: item.selected ? "var(--color-brand-green)" : "var(--bg-input)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.15s",
                  flexShrink: 0,
                }}>
                  {item.selected && (
                    <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                      <path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
              </label>

              {/* Product image */}
              <div style={{
                width: "40px",
                height: "40px",
                borderRadius: "6px",
                background: "#ffffff",
                border: "1px solid var(--border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                overflow: "hidden",
              }}>
                <ProductImage
                  src={item.image_url}
                  alt={item.name}
                  productName={item.name}
                  style={{ width: "100%", height: "100%", objectFit: "contain", padding: "2px" }}
                  fallbackClassName="w-5 h-5 text-[var(--text-muted)]"
                />
              </div>

              {/* Product info */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{
                  fontSize: "13px",
                  fontWeight: 600,
                  color: "var(--text-primary)",
                  margin: 0,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}>
                  {item.name}
                </p>
                <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "2px", display: "flex", gap: "8px" }}>
                  {item.price > 0 && (
                    <>
                      <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>₹{item.price}</span>
                      {item.mrp > item.price && (
                        <span style={{ textDecoration: "line-through" }}>₹{item.mrp}</span>
                      )}
                    </>
                  )}
                  {item.price === 0 && <span style={{ color: "var(--text-muted)" }}>Price unknown</span>}
                </div>
              </div>

              {/* Remove button */}
              <button
                type="button"
                onClick={() => removeUrl(item.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "28px",
                  height: "28px",
                  borderRadius: "6px",
                  border: "1px solid transparent",
                  background: "transparent",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                  flexShrink: 0,
                  transition: "all 0.15s",
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLElement).style.color = "var(--color-brand-red)";
                  (e.currentTarget as HTMLElement).style.background = "var(--ring-red)";
                  (e.currentTarget as HTMLElement).style.borderColor = "rgba(220,38,38,0.25)";
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.color = "var(--text-muted)";
                  (e.currentTarget as HTMLElement).style.background = "transparent";
                  (e.currentTarget as HTMLElement).style.borderColor = "transparent";
                }}
                aria-label="Remove"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div style={{
          padding: "24px 16px",
          textAlign: "center",
          border: "1.5px dashed var(--border)",
          borderRadius: "8px",
        }}>
          <Bookmark className="w-6 h-6" style={{ color: "var(--border-strong)", margin: "0 auto 8px" }} />
          <p style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-secondary)", margin: "0 0 2px" }}>
            Wishlist is empty
          </p>
          <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: 0 }}>
            Paste a product URL above to start tracking
          </p>
        </div>
      )}
    </div>
  );
}
