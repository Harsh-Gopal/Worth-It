import pytest
from app.normalization import parse_quantity, calculate_unit_price, NormalizedQuantity

def test_parse_quantity_basic():
    # Basic quantity
    res = parse_quantity("420 g")
    assert res is not None
    assert res.quantity_per_pack == 420.0
    assert res.quantity_unit == "g"
    assert res.pack_count == 1
    assert res.total_quantity == 420.0

def test_parse_quantity_suffix_multiplier():
    # e.g., "70 g x 4"
    res = parse_quantity("70 g x 4")
    assert res is not None
    assert res.quantity_per_pack == 70.0
    assert res.quantity_unit == "g"
    assert res.pack_count == 4
    assert res.total_quantity == 280.0

def test_parse_quantity_prefix_multiplier():
    # e.g., "4 x 70 g"
    res = parse_quantity("4 x 70 g")
    assert res is not None
    assert res.quantity_per_pack == 70.0
    assert res.quantity_unit == "g"
    assert res.pack_count == 4
    assert res.total_quantity == 280.0

def test_parse_quantity_pack_of():
    res = parse_quantity("Nutrabay Whey Protein 1 kg (Pack of 2)")
    assert res is not None
    assert res.quantity_per_pack == 1.0
    assert res.quantity_unit == "kg"
    assert res.pack_count == 2
    assert res.total_quantity == 2.0

def test_parse_quantity_count_only():
    res = parse_quantity("60 tablets")
    assert res is not None
    assert res.quantity_per_pack == 60.0
    assert res.quantity_unit == "tablet"
    assert res.pack_count == 1

def test_calculate_unit_price():
    nq = NormalizedQuantity(
        pack_count=1,
        quantity_per_pack=400.0,
        quantity_unit="g",
        total_quantity=400.0,
        total_quantity_unit="g",
        confidence="HIGH",
        raw_variant="400 g"
    )
    unit_price = calculate_unit_price(800.0, nq)
    assert unit_price == 2.0  # 800 / 400
