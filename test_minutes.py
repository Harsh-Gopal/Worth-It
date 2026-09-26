import requests
import json
import time

rule = {
  "name": "Minutes Test",
  "pincode": "800014",
  "keywords": [{"term": "FIAMA Patchouli & Macadamia Body Wash (250 ml)", "min_discount": 0}],
  "categories": [],
  "exclude_keywords": [],
  "product_urls": [],
  "platforms": ["minutes"],
  "lat": 25.5941,
  "lng": 85.1376
}

# create
r = requests.post("http://127.0.0.1:8000/api/alerts/primary", json=rule)
print("Create:", r.status_code, r.text)

# run
r2 = requests.post("http://127.0.0.1:8000/api/alerts/primary_monitor/run")
print("Run:", r2.status_code, r2.text)
