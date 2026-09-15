import pytest
from app.domain.models.product import InstamartProduct
from app.domain.models.deal import DealCondition
from app.domain.services.deal_engine import DealEngine

def create_product(price: float, mrp: float) -> InstamartProduct:
    return InstamartProduct(
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
        min_discount_pct=50.0,
        max_price=1500.0,
        condition_operator="AND"
    )
    
    res = engine.evaluate(prod, condition)
    assert res.qualifies is True
    
    # Fail one condition
    condition2 = DealCondition(
        min_discount_pct=50.0,
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
        min_discount_pct=50.0, # Fails
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
