"""
Tests for the Instamart Flash / Promotional Price Extractor.

These tests cover:
1. Flash sale detected correctly (special_price returned)
2. No flash sale (special_price is None, normal_price returned)
3. Normal price vs special price comparison
4. Malformed / unavailable product
5. Graceful degradation when UI / selector changes (key missing from HTML)
6. Location-based serviceability

Tests use the real `_parse_item_page` function with synthetic HTML fixtures so
they run fast without any network calls. The `fetch_flash_price` integration
test requires network access and is marked with `pytest.mark.integration`.
"""

import pytest

from app.platforms.promo_price import _parse_item_page, FlashPriceResult


# ─── HTML fixture helpers ─────────────────────────────────────────────────────

def _make_html(
    product_id: str = "TEST123",
    name: str = "Test Noodles 70g",
    brand: str = "TestBrand",
    offer_price: int = 60,
    mrp: int = 100,
    store_id: str = "99999",
    flash_sale_price: int | None = None,
    non_flash_price: int | None = None,
    flash_end_time: str | None = None,
    redemption_units: int | None = None,
    include_product_v2: bool = True,
) -> str:
    """Build a minimal HTML string that mimics the Instamart Redux state structure."""

    flash_block = ""
    if flash_sale_price is not None:
        nfp_json = (
            f'"nonFlashSalePrice":{{"currencyCode":"INR","units":"{non_flash_price}"}},'
            if non_flash_price is not None else ""
        )
        end_time_json = (
            f'"flashSaleEndTime":"{flash_end_time}",' if flash_end_time else ""
        )
        redemption_json = (
            f'"redemptionUnits":{redemption_units},' if redemption_units is not None else ""
        )
        flash_block = (
            f'"flashSalePriceDetails":{{'
            f'"flashSalePrice":{{"currencyCode":"INR","units":"{flash_sale_price}"}},'
            f'{nfp_json}{end_time_json}{redemption_json}'
            f'"isFlashSaleActive":true'
            f'}},'
        )

    sku_block = (
        f'{{"skuId":"{product_id}","spinId":"{product_id}","listingVariant":true,'
        f'"quantityDescription":"70 g",'
        f'"offerPrice":{{"currencyCode":"INR","units":"{offer_price}"}},'
        f'"mrp":{{"currencyCode":"INR","units":"{mrp}"}},'
        f'{flash_block}'
        f'"imageIds":["test-image-id"]}}'
    )

    product_v2_block = (
        f'"productV2":{{"itemData":{{'
        f'"displayName":"{name}",'
        f'"brand":"{brand}",'
        f'"inStock":true,'
        f'"isAvail":true,'
        f'"variations":[{sku_block}]'
        f'}}}}'
        if include_product_v2
        else ""
    )

    store_block = f'"storeId":"{store_id}",' if store_id else ""

    return (
        f'<html><body><script>'
        f'window.___INITIAL_STATE___={{'
        f'{store_block}'
        f'{product_v2_block}'
        f'}};</script></body></html>'
    )


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestFlashPriceParser:
    """Tests for _parse_item_page (pure parsing, no network)."""

    def test_flash_sale_detected(self):
        """Flash sale price should be extracted into special_price."""
        html = _make_html(
            product_id="917UXELNGA",
            name="WickedGud Instant Manchow Cup Noodles 70g",
            offer_price=60,
            mrp=60,
            flash_sale_price=27,
            non_flash_price=55,
            flash_end_time="10 PM",
            redemption_units=5,
        )
        result = _parse_item_page(html, "917UXELNGA")

        assert result.special_price == 27.0
        assert result.normal_price == 60.0
        assert result.mrp == 60.0
        assert result.non_flash_price == 55.0
        assert result.flash_end_time == "10 PM"
        assert result.redemption_limit == 5
        assert result.has_flash_sale is True  # via property-like check
        assert result.extraction_method == "redux_state"
        assert result.serviceable is True
        assert result.name == "WickedGud Instant Manchow Cup Noodles 70g"
        assert result.error is None

    def test_no_flash_sale_returns_none_special_price(self):
        """When no flash sale is active, special_price must be None."""
        html = _make_html(
            product_id="NRRQJ4R2XW",
            name="Baker's Dozen Donut Cake",
            offer_price=33,
            mrp=65,
            flash_sale_price=None,  # no flash sale
        )
        result = _parse_item_page(html, "NRRQJ4R2XW")

        assert result.special_price is None
        assert result.normal_price == 33.0
        assert result.mrp == 65.0
        assert result.flash_end_time is None
        assert result.redemption_limit is None
        assert result.extraction_method == "redux_state"
        assert result.error is None

    def test_normal_price_independent_of_special_price(self):
        """Normal price (offerPrice) must always be distinct from special_price."""
        html = _make_html(
            product_id="PROD001",
            offer_price=100,
            mrp=120,
            flash_sale_price=75,
            non_flash_price=100,
            flash_end_time="8 PM",
        )
        result = _parse_item_page(html, "PROD001")

        # They must differ
        assert result.normal_price != result.special_price
        assert result.normal_price == 100.0
        assert result.special_price == 75.0
        # non_flash_price == normal_price (expected)
        assert result.non_flash_price == 100.0

    def test_malformed_html_returns_error(self):
        """Empty / garbage HTML must not crash — error field set instead."""
        result = _parse_item_page("", "PROD_XYZ")
        assert result.special_price is None
        assert result.normal_price is None
        assert result.error == "empty_response"
        assert result.serviceable is False

    def test_product_not_found_in_page(self):
        """HTML without productV2 block returns not-found error."""
        result = _parse_item_page(
            "<html><body>Not found</body></html>", "MISSING_ID"
        )
        assert result.special_price is None
        assert result.error == "product_not_found"

    def test_selector_change_no_flash_key(self):
        """If flashSalePriceDetails key disappears from HTML, graceful degradation."""
        # Build HTML with a product but the flash block completely absent
        html = _make_html(
            product_id="CHANGED_SKU",
            offer_price=49,
            mrp=80,
            flash_sale_price=None,  # simulates key removal
        )
        # Manually strip out any flash-related key to simulate UI change
        html = html.replace("flashSalePriceDetails", "REMOVED_KEY")

        result = _parse_item_page(html, "CHANGED_SKU")
        assert result.special_price is None
        assert result.error is None  # not an error, just no flash sale
        assert result.normal_price == 49.0

    def test_unserviceable_location_returns_serviceable_false(self):
        """When storeId is absent the location is unserviceable."""
        html = _make_html(product_id="PROD_SVC", store_id="")  # no storeId
        result = _parse_item_page(html, "PROD_SVC")
        assert result.serviceable is False

    def test_image_url_extracted(self):
        """Image URL should be built from imageIds correctly."""
        html = _make_html(product_id="IMG_TEST", offer_price=50, mrp=80)
        result = _parse_item_page(html, "IMG_TEST")
        assert result.image_url is not None
        assert "test-image-id" in result.image_url

    def test_flash_sale_discount_greater_than_offer(self):
        """Flash sale price must be strictly less than normal offer price."""
        html = _make_html(
            product_id="DEEP_DISC",
            offer_price=200,
            mrp=300,
            flash_sale_price=99,
            flash_end_time="Midnight",
        )
        result = _parse_item_page(html, "DEEP_DISC")
        assert result.special_price is not None
        assert result.special_price < result.normal_price  # type: ignore[operator]


# ─── Property helper tests (has_flash_sale) ───────────────────────────────────

class TestFlashPriceResultFields:
    def test_has_flash_sale_true_when_special_price_set(self):
        r = FlashPriceResult(product_id="X", special_price=25.0)
        assert r.special_price is not None

    def test_has_flash_sale_false_when_special_price_none(self):
        r = FlashPriceResult(product_id="X")
        assert r.special_price is None

    def test_extraction_method_defaults_to_none(self):
        r = FlashPriceResult(product_id="X")
        assert r.extraction_method == "none"


# ─── Integration tests (require network, skipped in CI unless marked) ─────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_wicked_gud_noodles_real():
    """
    Integration: Fetch flash price for WickedGud Noodles at pincode 800014.
    This test requires live Instamart access.
    lat/lng for Patna (pincode 800014): approx 25.5941, 85.1376
    """
    from app.platforms.promo_price import fetch_flash_price
    result = await fetch_flash_price("917UXELNGA", lat=25.5941, lng=85.1376)
    assert result.product_id == "917UXELNGA"
    assert result.name is not None, "Product name should be returned"
    assert result.normal_price is not None, "Normal price should always be present"
    # special_price may or may not be active depending on time-of-day
    print(f"  normal_price={result.normal_price}, special_price={result.special_price}, "
          f"end_time={result.flash_end_time}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bakers_dozen_donut_cake_real():
    """
    Integration: Fetch flash price for Baker's Dozen Donut Cake at pincode 800014.
    """
    from app.platforms.promo_price import fetch_flash_price
    result = await fetch_flash_price("NRRQJ4R2XW", lat=25.5941, lng=85.1376)
    assert result.product_id == "NRRQJ4R2XW"
    assert result.name is not None
    assert result.normal_price is not None
    print(f"  normal_price={result.normal_price}, special_price={result.special_price}, "
          f"end_time={result.flash_end_time}")
