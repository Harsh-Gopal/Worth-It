import pytest
from datetime import datetime, timezone, timedelta
from app.domain.models.price_observation import PriceObservation
from app.domain.models.product import InstamartProduct
from app.persistence.database import Database
from app.persistence.repositories.price_history_repo import PriceHistoryRepository
from app.domain.services.price_history_service import PriceHistoryService

@pytest.fixture
def memory_db(tmp_path):
    # Use temp file for DB for tests so connections share the same DB
    return Database(tmp_path / "test.db")

@pytest.fixture
def history_service(memory_db):
    repo = PriceHistoryRepository(memory_db)
    return PriceHistoryService(repo)

def create_product(price: float, mrp: float = 2000.0) -> InstamartProduct:
    return InstamartProduct(
        external_product_id="test_prod_1",
        name="Test Product",
        url="http://test",
        price=price,
        mrp=mrp,
        stock=True,
        category="Test"
    )

def test_price_history_first_observation(history_service):
    prod = create_product(price=1800.0)
    
    # Check context before recording
    context = history_service.get_history_context(prod, "store_1", PriceObservation(
        instamart_product_id="test_prod_1", store_id="store_1", observed_price=1800.0, mrp=2000.0, discount_percent=10.0, in_stock=True
    ))
    assert context["previous_price"] is None
    assert context["price_drop_percent"] is None
    assert context["historical_low_before_now"] is None
    assert context["is_historical_low"] is False # no history to beat

    # Record it
    obs1 = history_service.record_observation(prod, "store_1")
    assert obs1.discount_percent == 10.0

def test_price_history_subsequent_observation(history_service):
    prod = create_product(price=2000.0)
    obs1 = history_service.record_observation(prod, "store_1")

    # Second observation: Price drop
    prod2 = create_product(price=1800.0)
    obs2 = PriceObservation(
        instamart_product_id=prod2.external_product_id,
        store_id="store_1",
        observed_price=prod2.price,
        mrp=prod2.mrp,
        discount_percent=10.0,
        in_stock=prod2.stock,
        timestamp=obs1.timestamp + timedelta(hours=1)
    )
    
    context = history_service.get_history_context(prod2, "store_1", obs2)
    assert context["previous_price"] == 2000.0
    assert context["price_drop_percent"] == 10.0
    assert context["historical_low_before_now"] == 2000.0

    # Record it
    # Need to simulate the repo saving the new obs so it affects overall historical low correctly
    history_service.repo.record_observation(obs2)
    
    # Fetch context again (is_historical_low calculates using overall_low)
    # Actually wait, is_historical_low requires the current obs to exist if overall_low includes it. 
    # Our get_history_context calculates based on the current_obs passed in.
    context = history_service.get_history_context(prod2, "store_1", obs2)
    assert context["is_historical_low"] is True

def test_price_increase(history_service):
    history_service.record_observation(create_product(price=1800.0), "store_1")
    
    import time
    time.sleep(0.01) # ensure strict timestamp ordering
    
    obs2 = history_service.record_observation(create_product(price=1900.0), "store_1")
    
    context = history_service.get_history_context(create_product(price=1900.0), "store_1", obs2)
    
    assert context["previous_price"] == 1800.0
    assert context["price_drop_percent"] is None # price increased
    assert context["historical_low_before_now"] == 1800.0
    assert context["is_historical_low"] is False
