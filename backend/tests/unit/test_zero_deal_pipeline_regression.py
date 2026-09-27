"""
Regression tests for the 0-deal pipeline bug.

These tests verify:
1. DealEngine with adaptive_mode=True and empty keyword_rules uses the default 15% threshold
   instead of failing all products (the root cause of the 0-deal bug).
2. DealEngine with keyword_rules configured correctly applies per-keyword thresholds.
3. DealEngine with non-matching keyword_rules correctly rejects mismatched products.
4. Products with discount >= threshold qualify; below threshold do not.
"""

import pytest
from app.domain.models.product import PlatformProduct
from app.domain.models.alert import AlertRule
from app.domain.models.deal import DealCondition
from app.domain.services.deal_engine import DealEngine


def _make_product(name: str, price: float, mrp: float, category: str = "groceries", stock: bool = True) -> PlatformProduct:
    return PlatformProduct(
        external_product_id=f"test_{name.replace(' ', '_')}",
        name=name,
        category=category,
        url=f"https://example.com/{name}",
        price=price,
        mrp=mrp,
        stock=stock,
        image_url=None,
        canonical_product_id=None,
    )


def _make_rule(keyword_rules=None, category_rules=None, product_rules=None, adaptive_mode=True) -> AlertRule:
    return AlertRule(
        id="test_rule",
        keyword_rules=keyword_rules or {},
        category_rules=category_rules or {},
        product_rules=product_rules or {},
        adaptive_mode=adaptive_mode,
    )


class TestDealEngineAdaptiveMode:
    """Tests for adaptive mode deal evaluation (the primary scan mode)."""

    def setup_method(self):
        self.engine = DealEngine()

    def test_empty_rules_uses_default_15_pct_threshold(self):
        """BUG FIX: With adaptive_mode=True and no keyword/category rules,
        products with >=15% discount should qualify (not fail with 'no target match')."""
        product = _make_product("Saffola Oats 500g", price=85.0, mrp=100.0)  # 15% discount
        rule = _make_rule()  # Empty rules, adaptive_mode=True

        result = self.engine.evaluate(product, rule=rule)

        assert result.qualifies, f"Expected qualification with default 15% threshold, got: {result.trigger_reasons}"
        assert "Default" in result.applicable_rule, f"Expected 'Default' in rule name, got: {result.applicable_rule}"

    def test_empty_rules_rejects_below_15_pct(self):
        """Products below 15% discount should NOT qualify when using default threshold."""
        product = _make_product("Saffola Oats 500g", price=92.0, mrp=100.0)  # 8% discount
        rule = _make_rule()

        result = self.engine.evaluate(product, rule=rule)

        assert not result.qualifies, f"Expected rejection below 15% threshold, got qualifies=True"

    def test_keyword_rule_matching_product_name(self):
        """Keyword 'Oats' with 15% min threshold: matching product with >=15% qualifies."""
        product = _make_product("Saffola Oats 500g", price=80.0, mrp=100.0)  # 20% discount
        rule = _make_rule(keyword_rules={"Oats": {"min_discount_pct": 15.0}})

        result = self.engine.evaluate(product, rule=rule)

        assert result.qualifies, f"Expected qualification with Oats rule 15%, got: {result.trigger_reasons}"
        assert "Keyword Rule" in result.applicable_rule

    def test_keyword_rule_matching_product_below_threshold(self):
        """Keyword 'Oats' with 15% min threshold: matching product with <15% does NOT qualify."""
        product = _make_product("Saffola Oats 500g", price=93.0, mrp=100.0)  # 7% discount
        rule = _make_rule(keyword_rules={"Oats": {"min_discount_pct": 15.0}})

        result = self.engine.evaluate(product, rule=rule)

        assert not result.qualifies, f"Expected rejection below 15% keyword threshold"

    def test_keyword_rule_configured_but_product_does_not_match(self):
        """When keyword_rules are configured but the product's name doesn't match ANY key,
        the product should be rejected (strict mode, not fallback to default)."""
        product = _make_product("Tropicana Orange Juice 1L", price=80.0, mrp=100.0)  # 20% discount
        rule = _make_rule(keyword_rules={"Oats": {"min_discount_pct": 15.0}})

        result = self.engine.evaluate(product, rule=rule)

        assert not result.qualifies, "Product not matching configured keyword rule should be rejected in strict mode"

    def test_category_rule_matching(self):
        """Category 'Cereals' with 20% threshold: product with category 'Cereals' qualifies."""
        product = _make_product("Kellogg's Cornflakes 1kg", price=70.0, mrp=100.0, category="Cereals")  # 30% off
        rule = _make_rule(category_rules={"Cereals": {"min_discount_pct": 20.0}})

        result = self.engine.evaluate(product, rule=rule)

        assert result.qualifies, f"Expected qualification with Cereals 20% rule, got: {result.trigger_reasons}"
        assert "Category Rule" in result.applicable_rule

    def test_category_rule_below_threshold_rejected(self):
        """Category match but discount < threshold → reject."""
        product = _make_product("Kellogg's Cornflakes 1kg", price=88.0, mrp=100.0, category="Cereals")  # 12% off
        rule = _make_rule(category_rules={"Cereals": {"min_discount_pct": 20.0}})

        result = self.engine.evaluate(product, rule=rule)

        assert not result.qualifies

    def test_empty_threshold_dict_uses_default_15_pct(self):
        """Frontend sends category_rules={'Oats': {}} for a category with no explicit discount.
        Empty threshold dict {} should use DealThresholds defaults (15%)."""
        product = _make_product("Saffola Oats 500g", price=82.0, mrp=100.0, category="Oats")  # 18% off
        # Note: keyword check uses product name, category check uses product.category
        rule = _make_rule(category_rules={"Oats": {}})  # Empty dict = use defaults

        result = self.engine.evaluate(product, rule=rule)

        assert result.qualifies, f"Empty threshold dict should use default 15%, got: {result.trigger_reasons}"

    def test_out_of_stock_never_qualifies(self):
        """Out-of-stock products should always fail regardless of discount."""
        product = _make_product("Saffola Oats 500g", price=50.0, mrp=100.0, stock=False)  # 50% off but OOS
        rule = _make_rule()

        result = self.engine.evaluate(product, rule=rule)

        assert not result.qualifies, "Out-of-stock product should not qualify"
        assert "Out of stock" in result.trigger_reasons[0]

    def test_no_mrp_discount_is_zero(self):
        """Product with price == mrp has 0% discount and should not qualify at 15% threshold."""
        product = _make_product("Plain Product", price=100.0, mrp=100.0)  # 0% discount
        rule = _make_rule()

        result = self.engine.evaluate(product, rule=rule)

        assert not result.qualifies
        assert result.discount_percent == 0.0

    def test_adaptive_mode_false_no_conditions_qualifies(self):
        """When adaptive_mode=False and no DealCondition is set, all in-stock products qualify."""
        product = _make_product("Some Product", price=100.0, mrp=100.0)  # 0% off
        rule = _make_rule(adaptive_mode=False)

        # Must also pass adaptive_mode=False by passing rule with adaptive_mode=False
        # and a None condition (discovery mode)
        result = self.engine.evaluate(product, condition=None, rule=rule)

        # rule.adaptive_mode=False, so goes to legacy path, condition=None → qualifies
        assert result.qualifies, "Discovery mode (no conditions) should qualify all products"
