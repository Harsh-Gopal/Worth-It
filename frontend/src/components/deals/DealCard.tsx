import type { DealResult } from "../../lib/types";
import { ExternalLink, MapPin, Activity, Bookmark } from "lucide-react";
import { ProductImage } from "../common/ProductImage";

interface DealCardProps {
  deal: DealResult & { source?: string };
  onHover?: () => void;
  onClick?: () => void;
}

export default function DealCard({ deal, onHover, onClick }: DealCardProps) {
  const {
    product,
    store,
    discount_percent,
    historical_low_before_now,
    price_drop_percent,
    is_historical_low,
    source,
  } = deal;

  const isHistLow = is_historical_low || historical_low_before_now;
  const isWishlist = source === "wishlist";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        padding: "14px",
        background: "var(--bg-surface)",
        border: isWishlist
          ? "1px solid rgba(22,163,74,0.35)"
          : "1px solid var(--border)",
        borderRadius: "10px",
        cursor: "pointer",
        transition: "border-color 0.15s, background 0.15s",
        position: "relative",
        overflow: "hidden",
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLElement).style.background = "var(--bg-surface-hover)";
        onHover?.();
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.background = "var(--bg-surface)";
      }}
      onClick={onClick}
    >
      {/* Wishlist accent */}
      {isWishlist && (
        <div style={{
          position: "absolute",
          top: 0,
          left: 0,
          bottom: 0,
          width: "3px",
          background: "var(--color-brand-green)",
          borderRadius: "10px 0 0 10px",
        }} />
      )}

      <div style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
        {/* Product image */}
        <div style={{
          width: "56px",
          height: "56px",
          borderRadius: "8px",
          background: "var(--bg-muted)",
          border: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          overflow: "hidden",
        }}>
          <ProductImage
            src={product.image_url}
            alt={product.name}
            productName={product.name}
            category={(product as any).category}
            style={{ width: "100%", height: "100%", objectFit: "contain", padding: "2px" }}
            fallbackClassName="w-6 h-6 text-[var(--text-muted)]"
          />
        </div>

        {/* Name + price */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={{
            fontSize: "13px",
            fontWeight: 600,
            color: "var(--text-primary)",
            margin: "0 0 2px",
            overflow: "hidden",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            lineHeight: 1.4,
          }}>
            {product.name}
          </h3>
          {(product.brand || product.size) && (
            <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: 0 }}>
              {product.brand}
              {product.brand && product.size && " · "}
              {product.size}
            </p>
          )}
        </div>

        {/* Price */}
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <div style={{ fontSize: "15px", fontWeight: 700, color: "var(--text-primary)" }}>
            ₹{product.price}
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", textDecoration: "line-through" }}>
            ₹{product.mrp}
          </div>
        </div>
      </div>

      {/* Badges */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", alignItems: "center" }}>
        {isWishlist && (
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "3px",
            fontSize: "10px",
            fontWeight: 700,
            color: "var(--color-brand-green)",
            background: "var(--ring-green)",
            border: "1px solid rgba(22,163,74,0.3)",
            borderRadius: "4px",
            padding: "2px 6px",
          }}>
            <Bookmark className="w-2.5 h-2.5" fill="currentColor" /> Tracked
          </span>
        )}
        <span style={{
          display: "inline-flex",
          alignItems: "center",
          fontSize: "10px",
          fontWeight: 700,
          color: "var(--color-brand-red)",
          background: "var(--ring-red)",
          border: "1px solid rgba(220,38,38,0.3)",
          borderRadius: "4px",
          padding: "2px 6px",
        }}>
          {discount_percent.toFixed(0)}% OFF
        </span>
        {isHistLow && (
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            fontSize: "10px",
            fontWeight: 700,
            color: "var(--color-brand-green)",
            background: "var(--ring-green)",
            border: "1px solid rgba(22,163,74,0.3)",
            borderRadius: "4px",
            padding: "2px 6px",
          }}>
            📉 Hist. Low
          </span>
        )}
        {price_drop_percent && price_drop_percent > 0 && (
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "2px",
            fontSize: "10px",
            fontWeight: 700,
            color: "#0891b2",
            background: "rgba(8,145,178,0.1)",
            border: "1px solid rgba(8,145,178,0.25)",
            borderRadius: "4px",
            padding: "2px 6px",
          }}>
            <Activity className="w-2.5 h-2.5" /> {price_drop_percent.toFixed(1)}% drop
          </span>
        )}
      </div>

      {/* Footer */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        paddingTop: "10px",
        borderTop: "1px solid var(--border)",
        gap: "8px",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
          <MapPin className="w-3 h-3" style={{ color: "var(--color-brand-green)", flexShrink: 0 }} />
          <span style={{ fontSize: "12px", fontWeight: 500, color: "var(--text-secondary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {store.name}
          </span>
          {store.distance_km !== undefined && store.distance_km !== null && (
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              · {store.distance_km.toFixed(1)} km
            </span>
          )}
        </div>

        {product.product_url && (
          <a
            href={product.product_url}
            target="_blank"
            rel="noreferrer"
            onClick={e => e.stopPropagation()}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              fontSize: "11px",
              fontWeight: 600,
              color: "#fff",
              background: "var(--color-brand-green)",
              borderRadius: "5px",
              padding: "4px 10px",
              textDecoration: "none",
              flexShrink: 0,
              whiteSpace: "nowrap",
            }}
          >
            Buy <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>
    </div>
  );
}
