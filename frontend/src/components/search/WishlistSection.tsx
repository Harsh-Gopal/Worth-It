import React, { useState } from "react";
import { Plus, Trash2, Loader2, Link2 } from "lucide-react";
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
    <div className="card" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px", background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "12px", width: "100%" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <div style={{ padding: "10px", background: "rgba(59, 130, 246, 0.1)", borderRadius: "10px", color: "#3b82f6" }}>
            <Link2 className="w-6 h-6" />
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <h4 style={{ margin: "0 0 2px 0", fontSize: "15px", fontWeight: 700, color: "var(--text-primary)" }}>Wishlist Tracking</h4>
            <p style={{ margin: 0, fontSize: "13px", color: "var(--text-secondary)" }}>Track specific products from any supported platform using product URLs.</p>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{ fontSize: "13px", color: "var(--text-secondary)", fontWeight: 500 }}>
            {selectedCount > 0 ? `${selectedCount}/${items.length} active` : `${items.length} items`}
          </div>
          <button
            type="button"
            onClick={() => document.getElementById("wishlist-url-input")?.focus()}
            style={{ 
              background: "transparent", 
              border: "1px solid var(--border)", 
              color: "var(--text-primary)", 
              padding: "6px 12px", 
              borderRadius: "8px", 
              fontSize: "13px", 
              fontWeight: 500,
              display: "flex", 
              alignItems: "center", 
              gap: "6px",
              cursor: "pointer",
              transition: "background 0.2s"
            }}
            onMouseEnter={e => e.currentTarget.style.background = "var(--bg-input)"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <Plus className="w-4 h-4" />
            Add from URL
          </button>
        </div>
      </div>

      <div style={{ width: "100%", height: "1px", background: "var(--border)", opacity: 0.5 }} />

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        <form onSubmit={handleAdd} style={{ display: "flex", gap: "8px" }}>
          <input
            id="wishlist-url-input"
            type="url"
            placeholder="Paste a product URL to track (Instamart, Zepto, Blinkit)..."
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
              padding: "10px 14px",
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
            style={{ padding: "10px 20px", flexShrink: 0, fontSize: "13px", borderRadius: "8px" }}
          >
            {isLoading
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : "Add"
            }
          </button>
        </form>

        {error && (
          <div style={{
            padding: "10px 14px",
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.2)",
            borderRadius: "8px",
            fontSize: "13px",
            color: "var(--color-brand-red)",
            display: "flex",
            alignItems: "center",
            gap: "8px"
          }}>
            {error}
          </div>
        )}

        {items.length === 0 ? (
          <div style={{ 
            display: "flex", 
            flexDirection: "column", 
            alignItems: "center", 
            justifyContent: "center", 
            padding: "40px",
            background: "var(--bg-input)",
            borderRadius: "12px",
            border: "1px dashed var(--border)",
            gap: "16px"
          }}>
            <div style={{ padding: "12px", background: "var(--bg-card)", borderRadius: "50%", color: "var(--text-muted)", border: "1px solid var(--border)" }}>
              <Link2 className="w-6 h-6" />
            </div>
            <div style={{ textAlign: "center" }}>
              <p style={{ margin: "0 0 4px 0", fontSize: "15px", fontWeight: 600, color: "var(--text-primary)" }}>Paste a product URL to track</p>
              <p style={{ margin: 0, fontSize: "13px", color: "var(--text-secondary)" }}>Supports Instamart, Zepto and Blinkit product links</p>
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "300px", overflowY: "auto" }}
            className="custom-scrollbar"
          >
            {items.map(item => (
              <div
                key={item.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "14px",
                  padding: "14px",
                  background: item.selected ? "var(--ring-green)" : "var(--bg-muted)",
                  border: item.selected
                    ? "1px solid rgba(34, 197, 94, 0.3)"
                    : "1px solid var(--border)",
                  borderRadius: "10px",
                  transition: "all 0.15s",
                }}
              >
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
                    width: "20px",
                    height: "20px",
                    borderRadius: "6px",
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
                      <svg width="12" height="10" viewBox="0 0 10 8" fill="none">
                        <path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                  </div>
                </label>
  
                <div style={{
                  width: "56px",
                  height: "56px",
                  borderRadius: "8px",
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
                    style={{ width: "100%", height: "100%", objectFit: "contain", padding: "4px" }}
                    fallbackClassName="w-6 h-6 text-[var(--text-muted)]"
                  />
                </div>
  
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{
                    fontSize: "15px",
                    fontWeight: 600,
                    color: "var(--text-primary)",
                    margin: 0,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}>
                    {item.name}
                  </p>
                  <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px", display: "flex", gap: "8px" }}>
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
  
                <button
                  type="button"
                  onClick={() => removeUrl(item.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    width: "36px",
                    height: "36px",
                    borderRadius: "8px",
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
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
