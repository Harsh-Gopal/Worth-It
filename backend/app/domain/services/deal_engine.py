from typing import Dict, Any, Optional
from app.domain.models.product import InstamartProduct
from app.domain.models.deal import DealCondition, DealEvaluation


class DealEngine:
    """
    Evaluates Instamart products against user-defined deal conditions.

    Logic:
    - Each configured condition contributes to a pool of "met" vs "configured" conditions.
    - AND mode: ALL configured conditions must be met.
    - OR mode: ANY one configured condition must be met.
    - If NO conditions are configured, every in-stock product qualifies (discovery mode).
    - Out-of-stock products never qualify.
    """

    def evaluate(
        self,
        product: InstamartProduct,
        condition: Optional[DealCondition],
        history_context: Optional[Dict[str, Any]] = None,
    ) -> DealEvaluation:
        # Normalise condition
        if condition is None:
            condition = DealCondition()

        # Discount calculation
        if product.mrp > 0 and 0 < product.price <= product.mrp:
            discount_percent = round(((product.mrp - product.price) / product.mrp) * 100, 1)
        else:
            discount_percent = 0.0

        history = history_context or {}
        prev_price: Optional[float] = history.get("previous_price")
        price_drop: Optional[float] = history.get("price_drop_percent")
        historical_low: Optional[float] = history.get("historical_low_before_now")
        is_historical_low: bool = history.get("is_historical_low", False)

        # Stock check — always required unless caller explicitly opts out
        require_in_stock = getattr(condition, "require_in_stock", True)
        if require_in_stock and not product.stock:
            return DealEvaluation(
                qualifies=False,
                discount_percent=discount_percent,
                price=product.price,
                mrp=product.mrp,
                previous_price=prev_price,
                price_drop_percent=price_drop,
                historical_low=historical_low,
                is_historical_low=is_historical_low,
                trigger_reasons=["Out of stock"],
            )

        configured_conditions = 0
        met_conditions = 0
        triggers = []

        # 1. Minimum discount
        if condition.min_discount_pct is not None:
            configured_conditions += 1
            if discount_percent >= condition.min_discount_pct:
                met_conditions += 1
                triggers.append(f"Discount {discount_percent:.1f}% ≥ {condition.min_discount_pct}%")

        # 2. Maximum price
        if condition.max_price is not None:
            configured_conditions += 1
            if product.price <= condition.max_price:
                met_conditions += 1
                triggers.append(f"Price ₹{product.price} ≤ ₹{condition.max_price}")

        # 3. Price drop
        if condition.price_drop_pct is not None:
            configured_conditions += 1
            if price_drop is not None and price_drop >= condition.price_drop_pct:
                met_conditions += 1
                triggers.append(f"Price drop {price_drop:.1f}% ≥ {condition.price_drop_pct}%")

        # 4. Historical low requirement
        if condition.require_historical_low:
            configured_conditions += 1
            if is_historical_low:
                met_conditions += 1
                triggers.append("Historical low")

        # Evaluate
        if configured_conditions == 0:
            qualifies = True
            triggers.append("No conditions (discovery mode)")
        elif condition.condition_operator.upper() == "OR":
            qualifies = met_conditions > 0
        else:  # AND
            qualifies = met_conditions == configured_conditions

        return DealEvaluation(
            qualifies=qualifies,
            discount_percent=discount_percent,
            price=product.price,
            mrp=product.mrp,
            previous_price=prev_price,
            price_drop_percent=price_drop,
            historical_low=historical_low,
            is_historical_low=is_historical_low,
            trigger_reasons=triggers,
        )
