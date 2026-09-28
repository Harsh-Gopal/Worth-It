import sys, logging
from app.domain.models.alert import AlertRule, DealThresholds
from app.domain.services.deal_engine import DealEngine
from app.domain.models.events import PlatformProduct

logging.basicConfig(level=logging.DEBUG)

def test_process():
    rule = AlertRule(
        user_id="test",
        pincode="140301",
        keyword_rules={"Oats": {"min_discount_pct": 15}, "Protein": {"min_discount_pct": 15}}
    )

    product = PlatformProduct(
        external_product_id="123",
        name="Saffola Oats 1kg",
        category="unknown",
        url="http://",
        price=100.0,
        mrp=200.0,
        stock=True,
        image_url="",
        canonical_product_id=None
    )
    
    match_keywords = ["Oats", "Protein"]
    
    name_lower = product.name.lower()

    def _kw_matches(kw: str, name: str) -> bool:
        kw_lower = kw.lower()
        if kw_lower in name:
            return True
        if kw_lower.endswith('s') and kw_lower[:-1] in name:
            return True
        return False

    if not any((_kw_matches(mk, name_lower) for mk in match_keywords)):
        print("FILTER[kw]: no match")
        return None
        
    engine = DealEngine(price_history=None)
    
    from app.domain.models.deal import DealCondition
    condition = DealCondition(price_drop_pct=None)
    
    eval_result = engine._evaluate_adaptive(product, condition=condition, rule=rule, store_id="test")
    
    print(f"EVAL RESULT: {eval_result.qualifies}, discount: {eval_result.discount_percent}, trigger: {eval_result.trigger_reasons}")

test_process()
