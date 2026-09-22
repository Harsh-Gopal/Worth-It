from typing import Dict, Any, Optional
from app.domain.models.product import PlatformProduct
from app.domain.models.deal import DealCondition, DealEvaluation
from app.domain.models.alert import AlertRule
from app.domain.models.intelligence import DealThresholds, DealLevel


class DealEngine:
    """
    Evaluates Instamart products against user-defined deal conditions or adaptive rules.
    """

    def evaluate(
        self,
        product: PlatformProduct,
        condition: Optional[DealCondition] = None,
        history_context: Optional[Dict[str, Any]] = None,
        rule: Optional[AlertRule] = None
    ) -> DealEvaluation:
        # Discount calculation
        if product.mrp > 0 and 0 < product.price <= product.mrp:
            discount_percent = round(((product.mrp - product.price) / product.mrp) * 100, 1)
        else:
            discount_percent = 0.0

        savings = max(0, product.mrp - product.price)

        history = history_context or {}
        prev_price: Optional[float] = history.get("previous_price")
        price_drop: Optional[float] = history.get("price_drop_percent")
        historical_low: Optional[float] = history.get("historical_low_before_now")
        is_historical_low: bool = history.get("is_historical_low", False)

        # Stock check
        require_in_stock = True
        if condition:
            require_in_stock = getattr(condition, "require_in_stock", True)
        if require_in_stock and not product.stock:
            return self._build_fail(product, discount_percent, history, ["Out of stock"])

        # If we have an adaptive rule, use Deal Intelligence
        if rule and getattr(rule, "adaptive_mode", False):
            return self._evaluate_adaptive(product, rule, discount_percent, savings, history)

        # Legacy / Simple condition evaluation
        if condition is None:
            condition = DealCondition()

        configured_conditions = 0
        met_conditions = 0
        triggers = []

        if condition.max_price is not None:
            configured_conditions += 1
            if product.price <= condition.max_price:
                met_conditions += 1
                triggers.append(f"Price ₹{product.price} ≤ ₹{condition.max_price}")

        if condition.price_drop_pct is not None:
            configured_conditions += 1
            if price_drop is not None and price_drop >= condition.price_drop_pct:
                met_conditions += 1
                triggers.append(f"Price drop {price_drop:.1f}% ≥ {condition.price_drop_pct}%")

        if condition.require_historical_low:
            configured_conditions += 1
            if is_historical_low:
                met_conditions += 1
                triggers.append("Historical low")

        if configured_conditions == 0:
            qualifies = True
            triggers.append("No conditions (discovery mode)")
        elif condition.condition_operator.upper() == "OR":
            qualifies = met_conditions > 0
        else:
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
            deal_level=DealLevel.NORMAL if qualifies else None,
            deal_score=50 if qualifies else 0,
            savings_amount=savings if qualifies else 0,
        )

    def _evaluate_adaptive(
        self, product: PlatformProduct, rule: AlertRule, discount_percent: float, savings: float, history: Dict[str, Any]
    ) -> DealEvaluation:
        # Hierarchy: Product > Keyword > Category > Global
        active_thresholds = None
        applicable_rule_name = "Global Default"

        # 1. Product Rules
        product_id = product.external_product_id
        if product_id and rule.product_rules and product_id in rule.product_rules:
            active_thresholds = DealThresholds(**rule.product_rules[product_id])
            applicable_rule_name = f"Product Rule ({product_id})"
        
        # 2. Keyword Rules
        if not active_thresholds and rule.keyword_rules:
            highest_kw_threshold = None
            best_kw = None
            for kw, thresholds in rule.keyword_rules.items():
                if kw.lower() in product.name.lower():
                    if highest_kw_threshold is None or thresholds.get("min_discount_pct", 0) > highest_kw_threshold.get("min_discount_pct", 0):
                        highest_kw_threshold = thresholds
                        best_kw = kw
            if highest_kw_threshold:
                active_thresholds = DealThresholds(**highest_kw_threshold)
                applicable_rule_name = f"Keyword Rule ({best_kw})"

        # 3. Category Rules
        if not active_thresholds and rule.category_rules and product.category:
            highest_cat_threshold = None
            best_cat = None
            for cat, thresholds in rule.category_rules.items():
                if cat.lower() in product.category.lower():
                    if highest_cat_threshold is None or thresholds.get("min_discount_pct", 0) > highest_cat_threshold.get("min_discount_pct", 0):
                        highest_cat_threshold = thresholds
                        best_cat = cat
            if highest_cat_threshold:
                active_thresholds = DealThresholds(**highest_cat_threshold)
                applicable_rule_name = f"Category Rule ({best_cat})"
        
        # 4. Strict Target Enforcement (No Global Fallback)
        if not active_thresholds:
            return self._build_fail(
                product, discount_percent, history, 
                ["Failed: Product does not match any active category or keyword targets"]
            )
        
        # Evaluate against active thresholds
        if discount_percent < active_thresholds.min_discount_pct:
            return self._build_fail(
                product, discount_percent, history, 
                [f"Failed {applicable_rule_name}: {discount_percent:.1f}% < {active_thresholds.min_discount_pct}%"]
            )
            
        # Optional: Check min savings
        if rule.min_savings is not None and savings < rule.min_savings:
            return self._build_fail(
                product, discount_percent, history, 
                [f"Failed minimum savings: ₹{savings} < ₹{rule.min_savings}"]
            )

        # It qualifies. Determine level and score
        level = active_thresholds.evaluate_level(discount_percent)
        
        # Calculate Deal Score (0-100)
        # Base score on how far past minimum we are
        score_base = 50.0
        spread = discount_percent - active_thresholds.min_discount_pct
        score_base += min(40, spread * 1.5)  # up to +40 for beating discount heavily
        
        if history.get("is_historical_low"):
            score_base += 10
            
        score = min(100.0, score_base)
        
        triggers = [f"Met {applicable_rule_name}: {discount_percent:.1f}% ≥ {active_thresholds.min_discount_pct}%"]
        if history.get("is_historical_low"):
            triggers.append("Historical Low")

        return self._build_success(
            product, discount_percent, savings, history, triggers, applicable_rule_name, level, score
        )

    def _build_fail(self, product: PlatformProduct, discount: float, history: Dict, triggers: list) -> DealEvaluation:
        return DealEvaluation(
            qualifies=False,
            discount_percent=discount,
            price=product.price,
            mrp=product.mrp,
            previous_price=history.get("previous_price"),
            price_drop_percent=history.get("price_drop_percent"),
            historical_low=history.get("historical_low_before_now"),
            is_historical_low=history.get("is_historical_low", False),
            trigger_reasons=triggers,
        )

    def _build_success(self, product: PlatformProduct, discount: float, savings: float, history: Dict, 
                       triggers: list, rule_name: str, level: str, score: float) -> DealEvaluation:
        return DealEvaluation(
            qualifies=True,
            discount_percent=discount,
            price=product.price,
            mrp=product.mrp,
            previous_price=history.get("previous_price"),
            price_drop_percent=history.get("price_drop_percent"),
            historical_low=history.get("historical_low_before_now"),
            is_historical_low=history.get("is_historical_low", False),
            trigger_reasons=triggers,
            deal_level=level,
            deal_score=round(score, 1),
            savings_amount=savings,
            applicable_rule=rule_name,
        )
