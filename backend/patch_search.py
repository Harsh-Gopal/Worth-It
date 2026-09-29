import re

with open("app/domain/services/search_orchestrator.py", "r") as f:
    content = f.read()

# Add store resolution to run_combined_search if missing
patch = """
        if not self.local_store_id:
            try:
                res = await self.client.resolve_store(self.center_lat, self.center_lng)
                if res and getattr(res, 'serviceable', True) and res.store_id:
                    self.local_store_id = res.store_id
                else:
                    yield create_event({'event': 'platform_unavailable', 'search_id': search_id, 'data': {'message': 'Platform is not available at this location.', 'platform': self.client.platform_name}})
                    return
            except Exception as e:
                log.warning("Could not resolve local store for %s: %s", self.client.platform_name, e)
                yield create_event({'event': 'platform_error', 'search_id': search_id, 'data': {'message': str(e), 'platform': self.client.platform_name}})
                return
"""

# Find the start of run_combined_search
search_str = "        # Store resolution is now handled explicitly in alert_runner.py before executing generators."
if search_str in content:
    content = content.replace(search_str, search_str + "\n" + patch)
    with open("app/domain/services/search_orchestrator.py", "w") as f:
        f.write(content)
    print("Patched search_orchestrator.py")
else:
    print("Could not find insertion point.")
