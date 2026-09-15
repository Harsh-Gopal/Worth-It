import type { DealResult } from "../../lib/types";
import DealCard from "./DealCard";


interface DealListProps {
  deals: DealResult[];
  onDealHover?: (deal: DealResult) => void;
  onDealClick?: (deal: DealResult) => void;
}

export default function DealList({ deals, onDealHover, onDealClick }: DealListProps) {
  if (deals.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-bold text-sand-900 flex items-center gap-2">
        🔥 Deals Found <span className="text-sm font-medium text-sand-500 bg-sand-100 px-2 py-0.5 rounded-full">{deals.length}</span>
      </h2>
      <div className="flex flex-col gap-4">
        {deals.map((deal) => (
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
