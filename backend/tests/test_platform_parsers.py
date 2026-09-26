import pytest
import json
from app.platforms.zepto.client import _parse_search_response, _parse_product_result
from app.domain.models.product import PlatformProduct

def test_zepto_parser_normalization():
    mock_json = {
        "layout": [
            {
                "widgetName": "SEARCHED_PRODUCTS",
                "data": {
                    "resolver": {
                        "data": {
                            "items": [
                                {
                                    "productResponse": {
                                        "product": {
                                            "name": "Whey Protein",
                                            "brand": "Nutrabay"
                                        },
                                        "productVariant": {
                                            "id": "zepto_pid_1",
                                            "formattedPacksize": "1 kg"
                                        },
                                        "mrp": 299900,
                                        "sellingPrice": 149900,
                                        "outOfStock": False,
                                        "availableQuantity": 10
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        ]
    }
    
    # Parse search response
    results = _parse_search_response(mock_json)
    assert len(results) == 1
    
    product = results[0]
    assert product.name == "Whey Protein"
    assert product.brand == "Nutrabay"
    assert product.mrp == 2999.0
    assert product.price == 1499.0
    
    # Normalization check
    assert product.total_quantity == 1.0
    assert product.total_quantity_unit == "kg"
    assert product.status == "in_stock"

def test_zepto_deal_rules():
    from app.domain.services.deal_engine import DealEngine
    from app.domain.models.deal import DealCondition
    
    mock_json = {
        "product": {
            "name": "Creatine Monohydrate",
            "brand": "Optimum Nutrition"
        },
        "productVariant": {
            "id": "zepto_pid_2",
            "formattedPacksize": "400 g"
        },
        "mrp": 150000,
        "discountedSellingPrice": 75000,
        "outOfStock": False,
        "availableQuantity": 5
    }
    
    result = _parse_product_result(mock_json)
    
    p = PlatformProduct(
        external_product_id="zepto_pid_2",
        name=result.name,
        url="http://dummy",
        price=result.price,
        mrp=result.mrp,
        stock=True,
        category="supplements"
    )
    
    engine = DealEngine()
    cond = DealCondition(max_price=800.0)
    
    eval_res = engine.evaluate(p, cond)
    assert eval_res.qualifies is True
    
    cond_fail = DealCondition(max_price=500.0)
    eval_res_fail = engine.evaluate(p, cond_fail)
    assert eval_res_fail.qualifies is False
    assert eval_res.discount_percent == 50.0

def test_zepto_parse_out_of_stock():
    mock_json = {
        "product": {
            "name": "Whey Isolate",
            "brand": "MyProtein"
        },
        "productVariant": {
            "id": "zepto_pid_3",
            "formattedPacksize": "2.5 kg"
        },
        "mrp": 700000,
        "sellingPrice": 600000,
        "outOfStock": True,
        "availableQuantity": 0
    }
    result = _parse_product_result(mock_json)
    assert result.status == "out_of_stock"

def test_blinkit_parser():
    from app.platforms.blinkit import _parse_snippets
    
    snippets = [
        {
            "data": {
                "identity": {"id": "blinkit_123"},
                "inventory": 5,
                "is_sold_out": False,
                "atc_actions_v2": {
                    "default": [
                        {
                            "add_to_cart": {
                                "cart_item": {
                                    "product_name": "Peanut Butter 1kg",
                                    "brand": "Pintola",
                                    "price": 100.0,
                                    "mrp": 200.0
                                }
                            }
                        }
                    ]
                }
            }
        }
    ]
    
    res = _parse_snippets(snippets, "blinkit_123")
    assert res.name == "Peanut Butter 1kg"
    assert res.price == 100.0
    assert res.mrp == 200.0
    assert res.status == "in_stock"
    
def test_swiggy_parser():
    from app.platforms.swiggy import _parse_search_response
    
    mock_json = {
        "data": {
            "cards": [
                {
                    "card": {
                        "card": {
                            "gridElements": {
                                "infoWithStyle": {
                                    "items": [
                                        {
                                            "displayName": "Oats 1kg",
                                            "inStock": True,
                                            "variations": [
                                                {
                                                    "skuId": "123",
                                                    "displayName": "Oats 1kg",
                                                    "price": {
                                                        "mrp": {"units": 100},
                                                        "offerPrice": {"units": 50}
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            ]
        }
    }
    
    results = _parse_search_response(mock_json)
    assert len(results) == 1
    assert results[0].name == "Oats 1kg"
    assert results[0].price == 50.0
    assert results[0].mrp == 100.0
    assert results[0].status == "in_stock"
