from typing import List, Dict, Optional
from datetime import timedelta
from collections import defaultdict

from app.domain.models.alert import AlertEvent, GroupedAlertEvent

class ProductGroupingService:
    @staticmethod
    def group_events(events: List[AlertEvent], tz_offset_mins: int = -330) -> List[GroupedAlertEvent]:
        """
        Group AlertEvents by platform, product_id, and local_date.
        tz_offset_mins: UTC offset in minutes (e.g., -330 for IST = UTC+05:30).
        """
        groups: Dict[str, GroupedAlertEvent] = {}
        
        for event in events:
            # Calculate local date using offset
            # UTC + (offset_mins) = Local Time
            local_dt = event.triggered_at + timedelta(minutes=-tz_offset_mins)
            local_date_str = local_dt.strftime('%Y-%m-%d')
            
            run_id = event.scan_run_id or local_date_str
            group_key = f"{run_id}_{event.platform}_{event.instamart_product_id}"
            
            if group_key not in groups:
                groups[group_key] = GroupedAlertEvent(
                    group_id=group_key,
                    instamart_product_id=event.instamart_product_id,
                    product_name=event.product_name,
                    product_image=event.product_image,
                    platform=event.platform,
                    category=None,
                    best_price=event.price,
                    mrp=event.mrp,
                    best_discount_percent=event.discount_percent,
                    deal_level=event.deal_level,
                    deal_score=event.deal_score,
                    savings_amount=event.savings_amount,
                    trigger_reason=event.trigger_reason,
                    triggered_at=event.triggered_at,
                    local_date=local_date_str,
                    locations_count=0,
                    platforms_count=1,
                    offers=[],
                    scan_run_id=event.scan_run_id
                )
            groups[group_key].offers.append(event)
            
        # Deduplicate and finalize each group
        final_groups = []
        for g in groups.values():
            # Deduplicate offers by (store_id, price), keeping the latest one
            unique_offers = {}
            for o in sorted(g.offers, key=lambda x: x.triggered_at):
                # By iterating sorted by time ascending, the latest one overwrites
                # same store + same price
                unique_offers[(o.store_id, o.price)] = o
                
            deduped = list(unique_offers.values())
            # Sort offers by price ascending (cheapest first), then by time descending
            deduped.sort(key=lambda x: (x.price, -x.triggered_at.timestamp()))
            
            if not deduped:
                continue
                
            best_offer = deduped[0]
            
            g.offers = deduped
            g.locations_count = len(deduped)
            g.best_price = best_offer.price
            g.mrp = best_offer.mrp
            g.best_discount_percent = best_offer.discount_percent
            g.deal_level = best_offer.deal_level
            g.deal_score = best_offer.deal_score
            g.savings_amount = best_offer.savings_amount
            g.trigger_reason = best_offer.trigger_reason
            
            # Group triggered_at is max of all its offers
            g.triggered_at = max(o.triggered_at for o in deduped)
            
            final_groups.append(g)
            
        # Sort groups by latest first, then by best discount
        final_groups.sort(key=lambda g: (g.triggered_at, g.best_discount_percent), reverse=True)
        return final_groups

