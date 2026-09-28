import React, { useState, useRef, useEffect } from "react";
import { Plus, Trash2, Loader2, Bookmark, ChevronLeft, ChevronRight, Check, GripHorizontal, ChevronUp, ChevronDown } from "lucide-react";
import { useWishlist } from "../../hooks/useWishlist";
import { ProductImage } from "../common/ProductImage";
import { useAuthStore } from "../../store/authStore";

export default function WishlistSection() {
  const { items, isLoading, error, resolveUrl, commitProduct, removeUrl, toggleSelection, reorderItems } = useWishlist();
  const [urlInput, setUrlInput] = useState("");
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  const [pendingProduct, setPendingProduct] = useState<any>(null);
  const [discountThreshold, setDiscountThreshold] = useState<string>("15");
  const { requestAuth } = useAuthStore();
  const [expanded, setExpanded] = useState(false);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    requestAuth(async () => {
      const trimmed = urlInput.trim();
      if (!trimmed) return;
      const resolved = await resolveUrl(trimmed);
      if (resolved) {
        setPendingProduct(resolved);
        setDiscountThreshold("15");
      }
    });
  };

  const confirmAdd = () => {
    requestAuth(() => {
      if (pendingProduct) {
        const discount = parseFloat(discountThreshold);
        if (isNaN(discount) || discount < 0 || discount > 100) {
          alert("Please enter a valid percentage between 0 and 100.");
          return;
        }
        commitProduct(pendingProduct, discount);
        setPendingProduct(null);
        setUrlInput("");
      }
    });
  };

  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const checkScroll = () => {
    if (scrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
      setCanScrollLeft(scrollLeft > 2);
      setCanScrollRight(scrollLeft + clientWidth < scrollWidth - 2);
    }
  };

  useEffect(() => {
    checkScroll();
    const currentRef = scrollRef.current;
    if (!currentRef) return;
    
    const resizeObserver = new ResizeObserver(() => checkScroll());
    resizeObserver.observe(currentRef);
    currentRef.addEventListener("scroll", checkScroll, { passive: true });
    
    return () => {
      resizeObserver.disconnect();
      currentRef.removeEventListener("scroll", checkScroll);
    };
  }, [items]);

  const scrollByAmount = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const { clientWidth } = scrollRef.current;
      const scrollAmount = clientWidth * 0.75;
      scrollRef.current.scrollBy({ left: direction === 'left' ? -scrollAmount : scrollAmount, behavior: 'smooth' });
    }
  };

  const selectedCount = items.filter(i => i.selected).length;

  return (
    <div className="card p-4 md:p-6 flex flex-col gap-4 md:gap-5 bg-[var(--bg-card)] border border-[var(--border)] rounded-[12px] w-full">
      {/* Header */}
      <div className="flex justify-between items-start flex-wrap gap-3 cursor-pointer md:cursor-default" onClick={() => { if (window.innerWidth <= 768) setExpanded(!expanded); }}>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <div style={{ padding: "10px", background: "rgba(59, 130, 246, 0.1)", borderRadius: "10px", color: "#3b82f6" }}>
            <Bookmark size={20} strokeWidth={2} />
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <h4 style={{ margin: "0 0 2px 0", fontSize: "15px", fontWeight: 700, color: "var(--text-primary)" }}>Wishlist Tracking</h4>
            <p className="m-0 text-[13px] text-[var(--text-secondary)] hidden md:block">Track specific products from any supported platform using product URLs.</p>
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
            <Plus size={16} strokeWidth={2} />
            Add from URL
          </button>
          <div className="md:hidden text-[var(--text-muted)] flex items-center ml-2">
            {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </div>
        </div>
      </div>

      <div className="h-[1px] bg-[var(--border)] opacity-50 hidden md:block" />

      <div className={`flex-col gap-4 transition-all ${expanded ? 'flex animate-fade-in-fast' : 'hidden md:flex'}`}>
        <div className="h-[1px] bg-[var(--border)] opacity-50 block md:hidden mb-2" />
        
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
              ? <Loader2 size={16} strokeWidth={2} className="animate-spin" />
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
              <Bookmark size={24} strokeWidth={2} />
            </div>
            <div style={{ textAlign: "center" }}>
              <p style={{ margin: "0 0 4px 0", fontSize: "15px", fontWeight: 600, color: "var(--text-primary)" }}>Paste a product URL to track</p>
              <p style={{ margin: 0, fontSize: "13px", color: "var(--text-secondary)" }}>Supports Instamart, Zepto and Blinkit product links</p>
            </div>
          </div>
        ) : (
          <div style={{ position: "relative", width: "100%" }}>
            {canScrollLeft && (
              <button
                type="button"
                onClick={() => scrollByAmount('left')}
                aria-label="Scroll wishlist products left"
                style={{
                  position: "absolute",
                  left: "-16px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  zIndex: 20,
                  width: "36px",
                  height: "36px",
                  borderRadius: "50%",
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-strong)",
                  boxShadow: "var(--shadow-card)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--text-primary)",
                  cursor: "pointer",
                  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)"
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = "var(--bg-surface-hover)";
                  e.currentTarget.style.transform = "translateY(-50%) scale(1.05)";
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = "var(--bg-surface)";
                  e.currentTarget.style.transform = "translateY(-50%) scale(1)";
                }}
              >
                <ChevronLeft size={20} strokeWidth={2} />
              </button>
            )}

            <div 
              ref={scrollRef}
              style={{ 
                display: "flex", 
                gap: "16px", 
                overflowX: "auto", 
                paddingBottom: "8px" 
              }}
              className="hide-scrollbar"
              onDragOver={(e) => {
                e.preventDefault();
              }}
            >
            {items.map((item, index) => {
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
                draggable
                onDragStart={(e) => {
                  setDraggedIndex(index);
                  e.dataTransfer.effectAllowed = "move";
                  e.dataTransfer.setData("text/plain", index.toString());
                }}
                onDragEnter={() => {
                  if (draggedIndex === null || draggedIndex === index) return;
                  setDragOverIndex(index);
                }}
                onDragEnd={() => {
                  setDraggedIndex(null);
                  setDragOverIndex(null);
                }}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.dataTransfer.dropEffect = "move";
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  if (draggedIndex !== null && draggedIndex !== index) {
                    requestAuth(() => reorderItems(draggedIndex, index));
                  }
                  setDraggedIndex(null);
                  setDragOverIndex(null);
                }}
                onClick={() => {
                  window.open(item.url, '_blank', 'noopener,noreferrer');
                }}
                style={{
                  flex: "0 0 auto",
                  width: "180px",
                  display: "flex",
                  flexDirection: "column",
                  background: item.selected ? "var(--ring-green)" : "var(--bg-card)",
                  border: item.selected
                    ? "1px solid var(--color-brand-green)"
                    : dragOverIndex === index
                      ? "2px dashed var(--color-brand-primary)"
                      : "1px solid var(--border)",
                  borderRadius: "12px",
                  overflow: "hidden",
                  position: "relative",
                  transition: "all 0.2s ease-in-out",
                  boxShadow: draggedIndex === index ? "0 8px 24px rgba(0,0,0,0.12)" : "0 2px 8px rgba(0,0,0,0.04)",
                  opacity: draggedIndex === index ? 0.5 : 1,
                  transform: dragOverIndex === index ? "scale(1.02)" : "scale(1)",
                  cursor: draggedIndex !== null ? "grabbing" : "pointer"
                }}
                onMouseEnter={e => {
                  if (draggedIndex !== null) return;
                  e.currentTarget.style.transform = "translateY(-2px)";
                  e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.08)";
                }}
                onMouseLeave={e => {
                  if (draggedIndex !== null) return;
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.04)";
                }}
              >
                {/* Drag Handle */}
                <div style={{
                  position: "absolute",
                  top: "0",
                  left: "0",
                  right: "0",
                  height: "24px",
                  zIndex: 5,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: "linear-gradient(180deg, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0) 100%)",
                  opacity: 0,
                  transition: "opacity 0.2s"
                }}
                className="drag-handle-overlay"
                >
                  <GripHorizontal size={16} strokeWidth={2.5} color="var(--bg-card)" style={{ filter: "drop-shadow(0px 1px 2px rgba(0,0,0,0.5))" }} />
                </div>
                <style>{`
                  div[draggable]:hover .drag-handle-overlay {
                    opacity: 1;
                  }
                `}</style>
                {/* Delete Button */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    requestAuth(() => removeUrl(item.id));
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
                  <Trash2 size={16} strokeWidth={1.75} />
                </button>

                {/* Checkbox for Selection */}
                <label 
                  onClick={(e) => e.stopPropagation()}
                  onDragStart={(e) => { e.preventDefault(); e.stopPropagation(); }}
                  style={{
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
                    onChange={(e) => {
                      e.stopPropagation();
                      requestAuth(() => toggleSelection(item.id));
                    }}
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
                      <Check size={14} strokeWidth={3} color="white" />
                    )}
                  </div>
                </label>

                {/* Image Section */}
                <div style={{
                  width: "100%",
                  height: "140px",
                  background: "#FFFFFF",
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

                  {/* Threshold */}
                  {item.min_discount_pct != null && (
                    <div style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "2px" }}>
                      Deal &ge;{item.min_discount_pct}%
                    </div>
                  )}

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

            {canScrollRight && (
              <button
                type="button"
                onClick={() => scrollByAmount('right')}
                aria-label="Scroll wishlist products right"
                style={{
                  position: "absolute",
                  right: "-16px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  zIndex: 20,
                  width: "36px",
                  height: "36px",
                  borderRadius: "50%",
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-strong)",
                  boxShadow: "var(--shadow-card)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--text-primary)",
                  cursor: "pointer",
                  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)"
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = "var(--bg-surface-hover)";
                  e.currentTarget.style.transform = "translateY(-50%) scale(1.05)";
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = "var(--bg-surface)";
                  e.currentTarget.style.transform = "translateY(-50%) scale(1)";
                }}
              >
                <ChevronRight size={20} strokeWidth={2} />
              </button>
            )}
          </div>
        )}
      </div>

      
      {/* PENDING PRODUCT MODAL */}
      {pendingProduct && (
        <div style={{
          position: "fixed",
          top: 0, left: 0, right: 0, bottom: 0,
          background: "rgba(0,0,0,0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000
        }}>
          <div className="card" style={{
            background: "var(--bg-card)",
            padding: "24px",
            borderRadius: "12px",
            border: "1px solid var(--border)",
            width: "100%",
            maxWidth: "400px",
            display: "flex",
            flexDirection: "column",
            gap: "16px"
          }}>
            <h3 style={{ margin: 0, color: "var(--text-primary)", fontSize: "18px", fontWeight: 600 }}>Add to Wishlist</h3>
            <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
              <ProductImage src={pendingProduct.image_url} alt={pendingProduct.name} style={{ width: "48px", height: "48px", borderRadius: "8px" }} />
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: "14px", fontWeight: 500, color: "var(--text-primary)" }}>{pendingProduct.name}</span>
                <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>{pendingProduct.brand || "Product"}</span>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <label style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-secondary)" }}>Minimum discount (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={discountThreshold}
                onChange={(e) => setDiscountThreshold(e.target.value)}
                style={{
                  background: "var(--bg-input)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  color: "var(--text-primary)",
                  padding: "10px",
                  fontSize: "14px",
                  outline: "none"
                }}
                onKeyDown={(e) => e.key === "Enter" && confirmAdd()}
              />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "8px" }}>
              <button
                type="button"
                onClick={() => setPendingProduct(null)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  background: "transparent",
                  border: "1px solid var(--border)",
                  color: "var(--text-primary)",
                  cursor: "pointer"
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmAdd}
                className="btn-primary"
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  cursor: "pointer"
                }}
              >
                Add Product
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
