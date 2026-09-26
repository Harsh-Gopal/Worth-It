import json

with open("flipkart_fetch_response.json") as f:
    d = json.load(f)

resp = d.get("RESPONSE", {})
slots = resp.get("slots", [])
for idx, slot in enumerate(slots):
    widget = slot.get("widget", {})
    if widget.get("type") == "PRODUCT_SUMMARY_EXTENDED":
        for prod in widget.get("data", {}).get("products", []):
            product_info = prod.get("productInfo", {}).get("value", {})
            name = product_info.get("titles", {}).get("title")
            
            pricing = product_info.get("pricing", {})
            prices = pricing.get("prices", [])
            # prices array usually has multiple objects like:
            # {'name': 'Selling Price', 'value': 299, 'currency': 'INR'}
            # {'name': 'Maximum Retail Price', 'value': 399, 'currency': 'INR'}
            
            final_price = pricing.get("finalPrice", {}).get("value")
            
            mrp = None
            sp = None
            for p in prices:
                if p.get("priceType") == "MRP" or p.get("name") == "Maximum Retail Price":
                    mrp = p.get("value")
                elif p.get("priceType") == "FSP" or p.get("name") == "Selling Price":
                    sp = p.get("value")
            
            # Inventory / stock
            inventory = product_info.get("inventory", {})
            in_stock = inventory.get("inStock", True)
            
            print(f"- {name} (Final: {final_price}, SP: {sp}, MRP: {mrp}, InStock: {in_stock})")
