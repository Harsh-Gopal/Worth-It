from app.domain.models.product import InstamartProduct
from app.domain.models.deal import DealCondition
from app.domain.services.deal_engine import DealEngine

def test_deal_engine_discount_calculation():
    engine = DealEngine()
    
    # 2441 vs 3699 -> ~34.009% -> 34.0%
    p = InstamartProduct(
        external_product_id="1", name="Test", url="",
        price=2441.0, mrp=3699.0, stock=True, category="test"
    )
    cond = DealCondition(min_discount_pct=34.0)
    
    res = engine.evaluate(p, cond)
    assert res.discount_percent == 34.0
    assert res.qualifies is True
    
def test_deal_engine_price_higher_than_mrp():
    engine = DealEngine()
    
    p = InstamartProduct(
        external_product_id="1", name="Test", url="",
        price=4000.0, mrp=3699.0, stock=True, category="test"
    )
    cond = DealCondition(min_discount_pct=1.0)
    
    res = engine.evaluate(p, cond)
    assert res.discount_percent == 0.0
    assert res.qualifies is False

def test_deal_engine_missing_mrp():
    engine = DealEngine()
    
    p = InstamartProduct(
        external_product_id="1", name="Test", url="",
        price=4000.0, mrp=0.0, stock=True, category="test"
    )
    cond = DealCondition(min_discount_pct=1.0)
    
    res = engine.evaluate(p, cond)
    assert res.discount_percent == 0.0
    assert res.qualifies is False

def test_deal_engine_max_price_condition():
    engine = DealEngine()
    
    p = InstamartProduct(
        external_product_id="1", name="Test", url="",
        price=99.0, mrp=150.0, stock=True, category="test"
    )
    # Target condition: price must be <= 100 (regardless of discount)
    cond = DealCondition(max_price=100.0)
    
    res = engine.evaluate(p, cond)
    assert res.qualifies is True
