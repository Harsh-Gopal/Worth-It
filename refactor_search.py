import sys

def main():
    path = "backend/app/api/routers/search.py"
    with open(path, "r") as f:
        content = f.read()

    # 1. Add pincodes to parameters
    content = content.replace(
        'search_mode: str = Query("current_pincode", description="current_pincode or nearby_area"),',
        'search_mode: str = Query("current_pincode", description="current_pincode or nearby_area"),\n    pincodes: Optional[str] = Query(None, description="Comma-separated pincodes"),'
    )

    # 2. Extract location logic
    start_locs = content.find('try:', content.find('watcher = asyncio.create_task(_watch_disconnect())'))
    
    locations_logic = """        try:
            clients = get_clients(plat_list)
            if not clients:
                yield {"event": "search_error", "data": json.dumps({"message": "No valid platforms selected."})}
                return
            queue = asyncio.Queue()

            pin_list = [p.strip() for p in pincodes.split(",")] if pincodes else []
            locations_to_scan = []
            
            if search_mode == "multiple_pincodes" and pin_list:
                from app.api.routers.location import _nom_forward
                for pin in pin_list:
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
                    "lat": effective_lat,
                    "lng": effective_lng,
                    "pincode": getattr(store_cache, "pincode", None),
                    "store_id": effective_store_id
                })

            async def _run_orch(client, lat, lng, store_id):
                try:
                    orchestrator = DealSearchOrchestrator(
                        client=client,
                        store_cache=store_cache,
                        center_lat=lat,
                        center_lng=lng,
                        local_store_id=store_id if client.platform_name == "swiggy" else None,
                        price_history_service=price_history,
                    )
                    async for event in orchestrator.run_combined_search(
                        search_id=search_id,
                        keyword=" ".join(all_targets) if all_targets else "",
                        product_urls=url_list,
                        match_keywords=all_targets if all_targets else None,
                        exclude_keywords=excl_list or None,
                        condition=condition,
                        expansion_radii_km=expansion_radii,
                        strategy=expansion_strategy,
                        cancel_event=cancel_event,
                    ):
                        if hasattr(event, "event"):
                            event._platform_name = client.platform_name
                        elif isinstance(event, dict):
                            event["_platform_name"] = client.platform_name
                        await queue.put(event)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    import logging
                    logging.error(f"Error in orchestrator for {client.platform_name}: {e}", exc_info=True)
                    from app.domain.models.events import create_event
                    await queue.put(create_event({
                        "event": "platform_error", 
                        "search_id": search_id, 
                        "data": {"message": str(e), "platform": client.platform_name}
                    }))

            async def _run_all_locations():
                try:
                    for scan_loc in locations_to_scan:
                        if cancel_event.is_set():
                            break
                        
                        current_lat = scan_loc["lat"]
                        current_lng = scan_loc["lng"]
                        current_store_id = scan_loc["store_id"]
                        
                        loc_tasks = []
                        for c in clients:
                            t = asyncio.create_task(_run_orch(c, current_lat, current_lng, current_store_id))
                            loc_tasks.append(t)
                        
                        await asyncio.gather(*loc_tasks, return_exceptions=True)
                finally:
                    await queue.put(None)

            waiter = asyncio.create_task(_run_all_locations())"""
    
    # Replace from `try:` to `waiter = asyncio.create_task(_wait_and_close())`
    waiter_idx = content.find('waiter = asyncio.create_task(_wait_and_close())', start_locs)
    end_of_waiter = content.find('\n', waiter_idx)
    
    content = content[:start_locs] + locations_logic + content[end_of_waiter:]
    
    with open(path, "w") as f:
        f.write(content)

if __name__ == "__main__":
    main()
