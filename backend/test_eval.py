from app.domain.services.deal_engine import DealEngine
from app.domain.models.deal import DealCondition
from app.domain.models.product import InstamartProduct

engine = DealEngine()
prod = InstamartProduct(external_product_id="123", name="Nutrabay", url="", price=800, mrp=1000, stock=True, category="")
cond = DealCondition(min_discount_pct=50.0)

print(engine.evaluate(prod, cond))
