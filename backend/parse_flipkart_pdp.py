import json

with open("flipkart_pdp_4.json") as f:
    d = json.load(f)

resp = d.get("RESPONSE", {})
slots = resp.get("slots", [])
for idx, slot in enumerate(slots):
    widget = slot.get("widget", {})
    w_type = widget.get("type", "")
    print(f"Widget {idx}: {w_type}")
