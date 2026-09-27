import pytest
from app.domain.models.product import PlatformProduct
from app.domain.models.deal import DealCondition
from app.domain.models.alert import AlertRule
from app.domain.services.deal_engine import DealEngine

def create_product(price: float, mrp: float) -> PlatformProduct:
    return PlatformProduct(
        external_product_id="prod1",
        name="Test",
        url="http",
        price=price,
        mrp=mrp,
        stock=True,
        category="Test"
    )

def test_deal_engine_and_conditions():
    engine = DealEngine()
    prod = create_product(price=1499.0, mrp=3000.0) # 50% discount
    
    # discount >= 50 AND price <= 1500
    condition = DealCondition(
        max_price=1500.0,
        condition_operator="AND"
    )
    
    res = engine.evaluate(prod, condition)
    assert res.qualifies is True
    
    # Fail one condition
    condition2 = DealCondition(
        max_price=1400.0, # Fails
        condition_operator="AND"
    )
    res2 = engine.evaluate(prod, condition2)
    assert res2.qualifies is False

def test_deal_engine_or_conditions():
    engine = DealEngine()
    prod = create_product(price=1499.0, mrp=2500.0) # 40% discount
    
    # discount >= 50 OR price <= 1500
    condition = DealCondition(
        # Fails
        max_price=1500.0,      # Passes
        condition_operator="OR"
    )
    
    res = engine.evaluate(prod, condition)
    assert res.qualifies is True
    
def test_deal_engine_price_drop():
    engine = DealEngine()
    prod = create_product(price=1499.0, mrp=2000.0)
    
    condition = DealCondition(
        price_drop_pct=20.0
    )
    
    # 1. No history provided -> Fails because requirement not met
    res = engine.evaluate(prod, condition, history_context={})
    assert res.qualifies is False
    
    # 2. History provided, drop = 25%
    res2 = engine.evaluate(prod, condition, history_context={"price_drop_percent": 25.0})
    assert res2.qualifies is True
    assert "Price drop 25.0% ≥ 20.0%" in res2.trigger_reasons
    
def test_deal_engine_historical_low():
    engine = DealEngine()
    prod = create_product(price=1499.0, mrp=2000.0)
    
    condition = DealCondition(
        require_historical_low=True
    )
    
    res = engine.evaluate(prod, condition, history_context={"is_historical_low": True})
    assert res.qualifies is True
    assert "Historical low" in res.trigger_reasons
    
    res2 = engine.evaluate(prod, condition, history_context={"is_historical_low": False})
    assert res2.qualifies is False

def test_wishlist_thresholds():
    engine = DealEngine()
    
    # URL 1: Requires 15%
    rule = AlertRule(
        id="rule1",
        product_urls=["http://product1"],
        product_rules={"http://product1": {"min_discount_pct": 15.0}},
        adaptive_mode=True
    )
    
    # Below threshold (14%)
    prod1 = PlatformProduct(
        external_product_id="prod1",
        name="Test",
        url="http://product1",
        price=86.0,
        mrp=100.0,
        stock=True,
        category="Test"
    )
    res = engine.evaluate(prod1, rule=rule, history_context={})
    assert res.qualifies is False
    
    # Exactly threshold (15%)
    prod2 = PlatformProduct(
        external_product_id="prod1",
        name="Test",
        url="http://product1",
        price=85.0,
        mrp=100.0,
        stock=True,
        category="Test"
    )
    res2 = engine.evaluate(prod2, rule=rule, history_context={})
    assert res2.qualifies is True
    
    # Above threshold (20%)
    prod3 = PlatformProduct(
        external_product_id="prod1",
        name="Test",
        url="http://product1",
        price=80.0,
        mrp=100.0,
        stock=True,
        category="Test"
    )
    res3 = engine.evaluate(prod3, rule=rule, history_context={})
    assert res3.qualifies is True
    
    # Legacy product without product_rules -> defaults to 15%
    rule_legacy = AlertRule(
        id="rule_leg",
        product_urls=["http://product2"],
        adaptive_mode=True
    )
    prod_legacy_14 = PlatformProduct(
        external_product_id="prod2",
        name="Test",
        url="http://product2",
        price=86.0,
        mrp=100.0,
        stock=True,
        category="Test"
    )
    res_leg = engine.evaluate(prod_legacy_14, rule=rule_legacy, history_context={})
    assert res_leg.qualifies is False
    
    prod_legacy_20 = PlatformProduct(
        external_product_id="prod2",
        name="Test",
        url="http://product2",
        price=80.0,
        mrp=100.0,
        stock=True,
        category="Test"
    )
    res_leg2 = engine.evaluate(prod_legacy_20, rule=rule_legacy, history_context={})
    assert res_leg2.qualifies is True
