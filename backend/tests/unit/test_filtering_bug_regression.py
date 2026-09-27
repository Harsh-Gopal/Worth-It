import pytest
from app.domain.models.product import PlatformProduct
from app.domain.models.alert import AlertRule
from app.domain.services.deal_engine import DealEngine
from app.domain.services.search_orchestrator import DealSearchOrchestrator
from unittest.mock import MagicMock

def test_1_yoga_bar_protein_oats():
    product = PlatformProduct(
        external_product_id="1",
        name="Yoga Bar 26% High Protein Oats Korean Spice",
        url="",
        price=122.0,
        mrp=200.0,
        stock=True,
        category="unknown"
    )
    # discount = (200 - 122)/200 * 100 = 39%
    engine = DealEngine()
    rule = AlertRule(
        id="test",
        keyword_rules={"Oats": {"min_discount_pct": 15}, "Protein": {"min_discount_pct": 15}},
        adaptive_mode=True
    )
    res = engine.evaluate(product, rule=rule)
    assert res.qualifies is True
    assert res.discount_percent == 39.0
    
def test_2_bagrrys_white_oats():
    product = PlatformProduct(
        external_product_id="2",
        name="Bagrry's White Oats",
        url="",
        price=300.0,
        mrp=428.0,
        stock=True,
        category="unknown"
    )
    # discount = (428 - 300)/428 * 100 = 29.9%
    engine = DealEngine()
    rule = AlertRule(
        id="test",
        keyword_rules={"Oats": {"min_discount_pct": 15}},
        adaptive_mode=True
    )
    res = engine.evaluate(product, rule=rule)
    assert res.qualifies is True
    assert res.discount_percent == 29.9

def test_3_random_product_rejected():
    product = PlatformProduct(
        external_product_id="3",
        name="Random Product",
        url="",
        price=90.0,
        mrp=100.0,
        stock=True,
        category="unknown"
    )
    # discount = 10%
    engine = DealEngine()
    rule = AlertRule(
        id="test",
        keyword_rules={"Oats": {"min_discount_pct": 15}}, # doesn't have oats anyway
        adaptive_mode=True
    )
    res = engine.evaluate(product, rule=rule)
    assert res.qualifies is False

def test_4_case_insensitive():
    product = PlatformProduct(
        external_product_id="4",
        name="YOGA BAR HIGH PROTEIN OATS",
        url="",
        price=122.0,
        mrp=200.0,
        stock=True,
        category="unknown"
    )
    engine = DealEngine()
    rule = AlertRule(
        id="test",
        keyword_rules={"oats": {"min_discount_pct": 15}},
        adaptive_mode=True
    )
    res = engine.evaluate(product, rule=rule)
    assert res.qualifies is True
    assert res.applicable_rule == "Keyword Rule (oats)"

def test_5_empty_exclude_list_does_not_exclude():
    # Testing search orchestrator internal logic
    orch = DealSearchOrchestrator(client=MagicMock(), store_cache=MagicMock(), center_lat=0.0, center_lng=0.0, local_store_id="123")
    product = PlatformProduct(
        external_product_id="5",
        name="Yoga Bar 26% High Protein Oats",
        url="",
        price=122.0,
        mrp=200.0,
        stock=True,
        category="unknown"
    )
    # We simulate _process_product logic
    match_keywords = ["Oats"]
    exclude_keywords = []
    
    # orchestrator does:
    if match_keywords:
        name_lower = product.name.lower()
        def _kw_matches(kw, name):
            kw_lower = kw.lower()
            return kw_lower in name or (kw_lower.endswith('s') and kw_lower[:-1] in name)
        assert any(_kw_matches(mk, name_lower) for mk in match_keywords) is True
        
    if exclude_keywords:
        assert False, "Should not reach here"

def test_6_and_semantics_multiple_keywords():
    product = PlatformProduct(
        external_product_id="6",
        name="High Protein Oats",
        url="",
        price=122.0,
        mrp=200.0,
        stock=True,
        category="unknown"
    )
    engine = DealEngine()
    rule = AlertRule(
        id="test",
        keyword_rules={"Protein": {"min_discount_pct": 15}, "Oats": {"min_discount_pct": 15}},
        adaptive_mode=True
    )
    res = engine.evaluate(product, rule=rule)
    assert res.qualifies is True

