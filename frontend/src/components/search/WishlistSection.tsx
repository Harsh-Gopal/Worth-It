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
          <div style={{ 
            display: "flex", 
            gap: "16px", 
            overflowX: "auto", 
            paddingBottom: "8px" 
          }}
            className="custom-scrollbar"
          >
            {items.map(item => {
              const platform = item.url.includes('swiggy.com') || item.url.includes('instamart.in') ? 'INSTAMART' :
                               item.url.includes('blinkit.com') ? 'BLINKIT' :
                               item.url.includes('zeptonow.com') ? 'ZEPTO' :
                               item.url.includes('flipkart') ? 'MINUTES' : 'UNKNOWN';
              
              const platformColor = platform === 'INSTAMART' ? 'var(--platform-swiggy)' :
                                    platform === 'ZEPTO' ? 'var(--platform-zepto)' :
                                    platform === 'BLINKIT' ? 'var(--platform-blinkit)' :
                                    platform === 'MINUTES' ? 'var(--platform-minutes)' : 'var(--text-secondary)';
              
              const discountStr = item.mrp > item.price ? Math.round(((item.mrp - item.price) / item.mrp) * 100) + "% OFF" : null;

              return (
              <div
                key={item.id}
                style={{
                  flex: "0 0 auto",
                  width: "180px",
                  display: "flex",
                  flexDirection: "column",
                  background: item.selected ? "var(--ring-green)" : "var(--bg-card)",
                  border: item.selected
                    ? "1px solid var(--color-brand-green)"
                    : "1px solid var(--border)",
                  borderRadius: "12px",
                  overflow: "hidden",
                  position: "relative",
                  transition: "all 0.2s ease-in-out",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.04)"
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.transform = "translateY(-2px)";
                  e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.08)";
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.04)";
                }}
              >
                {/* Delete Button */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeUrl(item.id);
                  }}
                  aria-label={`Delete ${item.name}`}
                  style={{
                    position: "absolute",
                    top: "8px",
                    right: "8px",
                    zIndex: 10,
                    width: "28px",
                    height: "28px",
                    borderRadius: "6px",
                    background: "var(--bg-card)",
                    border: "1px solid var(--border)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    transition: "all 0.15s"
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.color = "var(--color-brand-red)";
                    e.currentTarget.style.background = "var(--ring-red)";
                    e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.color = "var(--text-muted)";
                    e.currentTarget.style.background = "var(--bg-card)";
                    e.currentTarget.style.borderColor = "var(--border)";
                  }}
                >
                  <Trash2 className="w-4 h-4" />
                </button>

                {/* Checkbox for Selection */}
                <label style={{
                  position: "absolute",
                  top: "12px",
                  left: "12px",
                  zIndex: 10,
                  cursor: "pointer",
                  display: "flex"
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
                    background: item.selected ? "var(--color-brand-green)" : "var(--bg-card)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "all 0.15s",
                  }}>
                    {item.selected && (
                      <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                        <path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                  </div>
                </label>

                {/* Image Section */}
                <div style={{
                  width: "100%",
                  height: "140px",
                  background: "var(--bg-muted)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: "16px",
                  borderBottom: "1px solid var(--border)",
                  position: "relative"
                }}>
                  <ProductImage
                    src={item.image_url}
                    alt={item.name}
                    productName={item.name}
                    style={{ width: "100%", height: "100%", objectFit: "contain" }}
                    fallbackClassName="w-8 h-8 text-[var(--text-muted)]"
                  />
                </div>

                {/* Info Section */}
                <div style={{ padding: "12px", display: "flex", flexDirection: "column", gap: "6px", flex: 1 }}>
                  {/* Platform Badge */}
                  <div style={{
                    fontSize: "10px",
                    fontWeight: 800,
                    letterSpacing: "0.5px",
                    color: platformColor,
                    textTransform: "uppercase"
                  }}>
                    {platform}
                  </div>

                  {/* Product Name */}
                  <div 
                    title={item.name}
                    style={{
                      fontSize: "13px",
                      fontWeight: 600,
                      color: "var(--text-primary)",
                      lineHeight: "1.3",
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      height: "34px",
                    }}
                  >
                    {item.name}
                  </div>

                  <div style={{ flex: 1 }} />

                  {/* Price */}
                  <div style={{ display: "flex", alignItems: "baseline", gap: "6px", flexWrap: "wrap", marginTop: "4px" }}>
                    {item.price > 0 ? (
                      <>
                        <span style={{ fontSize: "16px", fontWeight: 700, color: "var(--text-primary)" }}>₹{item.price}</span>
                        {item.mrp > item.price && (
                          <span style={{ fontSize: "12px", textDecoration: "line-through", color: "var(--text-muted)" }}>₹{item.mrp}</span>
                        )}
                        {discountStr && (
                          <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--color-brand-green)", background: "var(--ring-green)", padding: "2px 6px", borderRadius: "4px" }}>
                            {discountStr}
                          </span>
                        )}
                      </>
                    ) : (
                      <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>Price unknown</span>
                    )}
                  </div>
                </div>
              </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
