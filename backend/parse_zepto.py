import json

with open("zepto_search_response.json") as f:
    d = json.load(f)

items = d["layout"][2]["data"]["resolver"]["data"]["items"]
print(json.dumps(items[0], indent=2))
