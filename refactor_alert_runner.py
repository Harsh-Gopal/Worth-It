import re

with open("backend/app/domain/services/alert_runner.py", "r") as f:
    content = f.read()

# Find the start of the mode check
start_idx = content.find('if getattr(rule, "search_mode", "current_pincode") == "current_pincode":')
# Find the end of the loop
end_idx = content.find('# Finished scanning all platforms', start_idx)

original_block = content[start_idx:end_idx]

# We need to replace it with the new locations loop
new_block = """search_mode = getattr(rule, "search_mode", "current_pincode")
        if search_mode == "nearby_area":
            expansion_radii = [3.0, 5.0, min(rule.radius_km, 20.0)]
            expansion_radii = list(dict.fromkeys(min(r, 20.0) for r in expansion_radii))
        else:
            expansion_radii = []

        locations_to_scan = []
        if search_mode == "multiple_pincodes" and getattr(rule, "pincodes", []):
            from app.api.routers.location import _nom_forward
            for pin in rule.pincodes:
                res = await _nom_forward(pin, limit=1)
                if res and len(res) > 0:
                    locations_to_scan.append({
                        "lat": float(res[0]["lat"]),
                        "lng": float(res[0]["lon"]),
                        "pincode": pin,
                        "store_id": None
                    })
        else:
            locations_to_scan.append({
                "lat": lat,
                "lng": lng,
                "pincode": getattr(rule, "pincode", None),
                "store_id": store_id
            })

        for scan_loc in locations_to_scan:
            current_lat = scan_loc["lat"]
            current_lng = scan_loc["lng"]
            current_store_id = scan_loc["store_id"]
            current_pincode = scan_loc["pincode"]
            
            # Temporary override rule pincode so event records it
            original_rule_pincode = getattr(rule, "pincode", None)
            rule.pincode = current_pincode

"""

# We need to indent the rest of the block (from `for plat_name in platform_order:` down to just before `# Finished`)
plat_loop_idx = original_block.find('for plat_name in platform_order:')
plat_loop_block = original_block[plat_loop_idx:]

# Replace `lat` and `lng` and `store_id` with current_*
plat_loop_block = plat_loop_block.replace("center_lat=lat", "center_lat=current_lat")
plat_loop_block = plat_loop_block.replace("center_lng=lng", "center_lng=current_lng")
plat_loop_block = plat_loop_block.replace("store_id if client.platform_name", "current_store_id if client.platform_name")

indented_plat_loop = "\n".join("    " + line if line else line for line in plat_loop_block.split("\n"))

# And restore the rule pincode at the end of the location loop
indented_plat_loop += "\n            rule.pincode = original_rule_pincode\n"

# The part before the platform loop:
pre_loop_part = original_block[:plat_loop_idx]

# However, pre_loop_part contains the old mode check which we've rewritten in new_block.
# We also have platform_to_urls, platform_order, etc. in pre_loop_part.
# Let's just extract those specific parts.

urls_logic = original_block[original_block.find('from app.links import detect_platform'):plat_loop_idx]

final_replacement = new_block + urls_logic + indented_plat_loop

content = content[:start_idx] + final_replacement + content[end_idx:]

with open("backend/app/domain/services/alert_runner.py", "w") as f:
    f.write(content)
