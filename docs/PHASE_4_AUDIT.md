# Phase 4 Audit: Current Implementation State

## 1. What Already Works
- **WAF Session Bootstrap**: `session.py` correctly handles Playwright logic for Instamart's challenge.
- **ProductDiscoveryEngine**: Broad keyword searching properly interfaces with `search`.
- **ProductMatcher**: Deterministic matching logic works correctly on mocked products.
- **DealEngine**: True discount calculations verified via extensive tests.
- **Geographic Store Cache**: Deduplication, non-drifting coordinates, and exact haversine bounding box are functional (`StoreCache`).
- **Hex Grid Generator**: Deterministic coordinate probing covering specific radii.
- **Orchestrator State Machine**: `NEARBY_FIRST` early stopping and SSE-style event emitting exist in `DealSearchOrchestrator`.

## 2. What is Mocked
- `pytest` suite heavily relies on mocked classes for `StoreDiscoveryService`, `product_at_store`, and `ProductDiscoveryEngine`. 
- Real network responses (e.g., malformed JSON, actual product schema variations) are currently mocked ideally.

## 3. What is Live
- Currently, NO live code automatically runs during automated tests, fulfilling the strict safety requirements.
- The dedicated `smoke_instamart.py` script attempts a live run, but lacks comprehensive geographic store discovery integration (it only tests a single local search and a single targeted fetch).

## 4. Missing Integration Points
- **Live Geographic Orchestration Smoke Test**: We need a script or modification to `smoke_instamart.py` that fully connects the Orchestrator with live stores (expanding radius to 3km, discovering stores, caching, and running targeted product checks).
- **Concurrency Integration Checks**: Ensure `asyncio.Semaphore` actually behaves correctly under live load without deadlocks or WAF blocking.
- **Robustness in Orchestrator**: The current `DealSearchOrchestrator` doesn't explicitly handle `search_cancelled` events or capture exceptions per store gracefully enough (it uses `return_exceptions=True` but doesn't emit structured error SSEs for individual store failures).

## 5. Assumptions
- Assume Instamart's `external_product_id` is stable across dark stores within a single city (e.g., Nutrabay Protein has the same ID across stores 2km apart). If this is false, the targeted `product_at_store` check will fail geographically.
- Assume Instamart's `select-location` API allows bounding-box or arbitrary Lat/Lng probing to return a valid store ID without blocking based on frequency.

## 6. API Fields that Still Need Verification
- `price` vs `mrp` format when discounts don't exist.
- Whether a targeted product search API (`/search/v2`) returns `inventory.inStock: False` definitively for out of stock, or simply omits the item.

## 7. Potential Bugs
- The orchestrator uses `asyncio.to_thread` for `product_at_store`. If an HTTP error occurs, it's swallowed silently instead of emitting a `store_scan_failed` SSE event.
- The `smoke_instamart.py` script does not test the Orchestrator, it tests components manually.
