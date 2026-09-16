import type { DealResult } from "../../lib/types";
import DealCard from "./DealCard";

interface DealListProps {
  deals: DealResult[];
  onDealHover?: (deal: DealResult) => void;
  onDealClick?: (deal: DealResult) => void;
}

export default function DealList({ deals, onDealHover, onDealClick }: DealListProps) {
  if (deals.length === 0) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <h2 style={{
        fontSize: "14px",
        fontWeight: 600,
        color: "var(--text-primary)",
        margin: 0,
        display: "flex",
        alignItems: "center",
        gap: "8px",
      }}>
        Deals Found
        <span style={{
          fontSize: "12px",
          fontWeight: 700,
          color: "var(--color-brand-green)",
          background: "var(--ring-green)",
          border: "1px solid rgba(22,163,74,0.3)",
          borderRadius: "12px",
          padding: "1px 8px",
        }}>
          {deals.length}
        </span>
      </h2>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {deals.map(deal => (
          <DealCard
            key={deal.deal_id}
            deal={deal}
            onHover={() => onDealHover?.(deal)}
            onClick={() => onDealClick?.(deal)}
          />
        ))}
      </div>
    </div>
  );
}
