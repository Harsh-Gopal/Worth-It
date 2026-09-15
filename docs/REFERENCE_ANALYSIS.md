# Reference Analysis

This document analyzes the two reference repositories: `instamart-alerts` and `CartRadar`. It outlines what is reusable, what should be adapted, and what must not be copied, serving as the basis for the architecture of `instamart-deal-radar`.

## 1. What is Reusable from `instamart-alerts`

- **Instamart Session & WAF Architecture**: The robust handling of AWS WAF tokens using Playwright to mint a headless Chromium session (`aws-waf-token`), and the fallback mechanisms (HTTP polling vs. browser transport) are highly valuable and directly applicable.
- **Instamart Location Resolution Flow**: The sequence of endpoints to resolve a location (`/maps/suggestions` → `/maps/address-widgets/v2` → `/home/select-location/v2`) and the extraction of `storeId` from deeplinks is critical Instamart-specific knowledge.
- **Product Search & Pagination**: The understanding of Instamart's `/search/v2` endpoint, including the `pageOffset.nextOffset` cursor, maximum pagination limits, and result parsing logic.
- **Price Calculation**: The parsing of Google Money style pricing (`units` and `nanos`) into float values, and basic MR/Offer price discount calculations.
- **Alert Deduplication (Conceptual)**: Concepts around alerting thresholds and cooldowns (though the implementation needs to be abstracted).

## 2. What is Reusable from `CartRadar`

- **Geographic Grid Engine**: The `hex_grid` generation and Haversine distance calculations are perfect for the geographic expansion phase.
- **Store Cache (SQLite)**: The `store_cache` SQLite implementation storing discovered stores and probed coordinates. This avoids redundant API calls for location checking and enforces radius constraints.
- **Search Orchestration Pattern (SSE)**: The progressive search execution (`run_search` orchestrator) that streams events (e.g., `discovery_start`, `checking`, `store_result`) to the frontend using Server-Sent Events (SSE).
- **Concurrency & Rate Limiting**: The Playwright concurrency limits and bounded execution queues for geographic sweeping.
- **Frontend Map & Architecture**: The React + TypeScript + react-leaflet map that plots stores, current sweep radius, and real-time scanning progress.

## 3. What Should NOT be Copied

- **CartRadar's Exact URL Dependency**: CartRadar relies heavily on providing an exact product URL. The new project must be keyword-first.
- **CartRadar's Multi-Platform Complexity**: CartRadar supports Zepto, Blinkit, BigBasket, etc. This project (V1) is strictly for Swiggy Instamart, though interfaces should allow for future expansion.
- **Instamart-Alerts' Rigid Telegram Coupling**: `instamart-alerts` ties scraping directly to Telegram bots in several places. The new project requires a decoupled NotificationProvider.
- **Instamart-Alerts' Broad Stock Assumption**: The new project requires exact product matching; we cannot assume every search result for a keyword is the target product.

## 4. Where the Two Architectures Overlap

- **Store Resolution**: Both need to translate coordinates into a platform-specific store ID. `instamart-alerts` does this for a single location; `CartRadar` does it systematically over a geographic grid.
- **Product Fetching**: Both fetch product details (price, stock) from a store. `instamart-alerts` uses keyword searches; `CartRadar` uses exact product ID lookups.

## 5. Where They Conflict

- **Search Paradigm**: `instamart-alerts` searches by keyword and looks at all results on a page. `CartRadar` searches by exact product ID. 
  - *Resolution*: The new project will bridge this. It will perform a keyword search at the user's *local* store to discover "Canonical Products" (exact product IDs), and then use those precise IDs for the geographic expansion sweep, avoiding expensive full-text searches across dozens of stores.
- **State Management**: `instamart-alerts` keeps session state for the single bot instance. `CartRadar` orchestrates multiple simultaneous sessions or requests.
  - *Resolution*: A hybrid approach where an `InstamartSessionManager` manages the WAF token globally, but the `DealSearchOrchestrator` runs concurrent geographic HTTP requests.

## 6. What New Components are Required

- **Product Discovery & Matcher Engine**: A deterministic engine to take a broad keyword ("Nutrabay protein") and identify the exact `InstamartProduct` candidates, filtering out unrelated items (e.g., "Nutrabay Shaker").
- **Canonical Product Identity**: A domain model to separate the abstract product from the platform-specific representation, crucial for mapping keyword results to geographic sweep targets.
- **Deal Engine**: A sophisticated evaluator that calculates true discount (MRP vs Price), checks historical lows, evaluates complex user conditions, and ranks deals.
- **Price History Database**: A new SQLite persistence layer to track historical price observations to support "price drop" and "historical low" triggers.

## 7. Data Flow

1. **User Input**: Keyword + Location + Deal Conditions.
2. **Local Resolution**: `InstamartClient` resolves location to `storeId`.
3. **Product Discovery**: `InstamartClient` performs keyword search at the local store.
4. **Matching**: `ProductMatcher` identifies target products.
5. **Local Deal Check**: `DealEngine` evaluates local products. If a match is found -> Stream to UI -> End.
6. **Geographic Expansion**: If no match, `DealSearchOrchestrator` triggers `GeoSearchEngine`.
7. **Grid Sweep**: `StoreDiscovery` probes nearby hex grid points to find new `storeIds`.
8. **Targeted Lookup**: `InstamartClient` queries discovered `storeIds` using the exact product IDs found in step 3.
9. **Deal Evaluation**: `DealEngine` evaluates all geographic results.
10. **Result & Alert**: Stream best deal to UI; optionally trigger `AlertEngine`.

## 8. Dependency Flow

- **Infrastructure Layer** (DB, Cache, SSE, Geo) operates independently.
- **Platform Layer** (Instamart Client, Session) depends on Infrastructure (Cache) for WAF tokens but knows nothing about Deals.
- **Domain Layer** (Matcher, Deal Engine, Orchestrator) depends on Platform Layer interfaces and Infrastructure Layer, managing the business logic.

## 9. Performance Risks

- **Keyword Searching at Scale**: Searching a keyword across 50 stores, traversing 8 pages per store, is extremely slow and will trigger rate limits. 
  - *Mitigation*: The "bridge" approach. Keyword search is *only* done locally. Once the exact product ID is found, geographic expansion uses the much faster/cheaper exact product lookup endpoint.
- **Grid Probing Overhead**: Resolving coordinates to Instamart stores is an expensive API call.
  - *Mitigation*: Aggressive use of the SQLite `StoreCache` to skip probing known areas.

## 10. WAF / Session Risks

- **Token Exhaustion/Blocking**: Instamart's AWS WAF is aggressive. Too many rapid requests or concurrent Playwright sessions will result in IP bans or un-passable CAPTCHAs.
  - *Mitigation*: Centralized WAF token management. Only one headless browser handles the challenge. All geographic sweep tasks use lightweight HTTP clients carrying the centralized `aws-waf-token`.

## 11. Geographic Scanning Risks

- **Over-expansion**: A user might request a 20km radius, which generates hundreds of grid points.
  - *Mitigation*: Progressive expansion. The orchestrator checks 3km first. If a deal is found, it stops. It only proceeds to 5km, 10km, etc., if necessary.
