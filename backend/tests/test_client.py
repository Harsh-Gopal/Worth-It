from app.platforms.instamart.client import _money
from app.domain.models.product import InstamartProduct

def test_money_parsing():
    assert _money({"units": "100", "nanos": 500000000}) == 100.5
    assert _money({"units": "2441"}) == 2441.0
    assert _money(None) is None
    assert _money({}) is None

def test_instamart_product_creation():
    p = InstamartProduct(
        external_product_id="123",
        name="Test Item",
        url="https://test",
        price=10.0,
        mrp=20.0,
        stock=True,
        category="Test"
    )
    assert p.external_product_id == "123"
    assert p.stock is True
