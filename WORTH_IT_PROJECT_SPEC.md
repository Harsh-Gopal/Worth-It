# Worth-It Project Specification

## 1. Project Purpose
Worth-It is a multi-platform quick-commerce deal discovery and monitoring application. It allows users to track keywords, categories, and explicit product links across multiple fast-delivery platforms (like Swiggy Instamart, Zepto, and Blinkit) to find the best deals and discounts.

## 2. Product Philosophy
The project is primarily intended for personal use and open-source deployment, where each user can deploy their own instance. The system monitors targets continuously and dynamically to discover the best deals as they become available.

## 3. Supported Platforms
- Swiggy Instamart
- Zepto
- Blinkit

## 4. Tracking Modes
- Keyword tracking
- Category tracking
- Explicit product-link tracking

## 5. Critical Tracking Rule
A keyword/category monitor must NEVER silently become product-ID tracking. For example, if a user tracks "Whey >= 30%", on every future scan, the system must search the platforms for the keyword/category dynamically again. It must NOT search once, pick the first discovered product, save that product ID, and track only that product forever. A different product matching "Whey" may become the best deal later while the previously discovered product becomes unavailable/out of stock. Only explicit product-link tracking should directly track a specific product.

## 6. Monitor Configuration Model
Platform selection: User can select one or more supported platforms.
Location: User selects a pincode/store location.
Area mode: Current Pincode Only or Nearby Area.
Targets: Keywords, Categories, Minimum discount per target.
Scan interval: Frequency of scans.
Wishlist/product links: Specific product URLs.

## 7. Keyword Discount UX
- User types keyword and confirms.
- Discount popup opens immediately.
- User selects a predefined percentage or enters a custom percentage and applies.
- Keyword becomes active target (e.g., "Whey >=30%").
- "Set %" is NEVER persisted as an active target.
- Cancellation closes the popup and no target is created.
- Editing an existing target reopens the popup with the current percentage preselected.

## 8. Category Discount UX
- Same rules as Keyword Discount UX. The category selector triggers the discount popup to set the minimum discount threshold.

## 9. Removed Features
The old global Deal Criteria panel (Max Price, Price Drop %, Historical Low) was intentionally removed. Do not reintroduce it unless explicitly requested. Minimum discounts are configured per target.

## 10. Location Architecture
- Current Pincode Only: Default mode. Scans only the store/location associated with the selected pincode. Does NOT generate hex grid, nearby coordinates, or geographic expansion.
- Nearby Area: Optional advanced mode for geographic expansion.
- Saved pincode: Preserves pincode, platform/store information, latitude, longitude, and location identity.
- Map behavior: Map markers use actual available coordinates from the platform. Stores with identical coordinates are grouped into a single marker.

## 11. Platform Orchestration
One monitor configuration becomes platform-specific scan jobs. The orchestrator delegates searches across selected platforms without duplicating work.

## 12. Deduplication
- Target normalization prevents duplicate searches (e.g., "Whey >=30%" and "Whey >=40%" for the same platform are evaluated in a single search for "Whey").
- Duplicate prevention ensures no duplicate search requests within one scan cycle.

## 13. CartRadar Reuse
CartRadar architecture/code is reused where appropriate for platform abstraction, browser automation, location handling, store discovery, product normalization, caching, rate limiting, retry logic, and platform-specific adapters.

## 14. Scan Lifecycle
Start -> immediate scan -> progress -> results -> history -> next interval -> repeat.
The initial scan begins immediately when a monitor starts, regardless of the configured interval.

## 15. SSE / Live Console
Live events are streamed via Server-Sent Events (SSE). The frontend parses events according to the SSE protocol and extracts JSON only from the event data field.

## 16. History Semantics
Every scan instance is an observation, even if the price or discount is unchanged. History records temporal observations.

## 17. Deal Engine
Evaluates minimum discounts and determines if an item qualifies as a deal based on configured thresholds.

## 18. Alert Engine
Handles deduplication, cooldowns, better-deal overrides, and failure isolation.

## 19. Frontend State Architecture
Monitor configuration, targets, scan state, live events, and history are managed in the frontend with a single source of truth.

## 20. Backend Architecture
Includes FastAPI routers, domain services (orchestrator, runner), domain models (alert, search), platform adapters (Instamart, Zepto, Blinkit), scheduler, SQLite persistence, and caching.

## 21. Error Handling
- JSON errors: Backend returns valid JSON for API endpoints. Frontend properly handles text/event-stream vs application/json.
- Platform failures: Handled gracefully without crashing the entire scan.

## 22. Performance Rules
- No unnecessary product tracking.
- Deduplicate work.
- Controlled concurrency.
- Rate limiting and task cleanup.

## 23. Testing Requirements
- Unit tests, integration tests, API tests.
- Browser/E2E tests using Chrome automation.

## 24. Known Platform Limitations
- Zepto and Blinkit often require fallback coordinates when precise geolocation is unavailable.
- Anti-bot measures (WAF) may necessitate headless browser automation.

## 25. Do Not Break These Rules
- NEVER convert a keyword/category search into a static product ID search.
- NEVER persist an incomplete target without a discount (e.g., "Set %").
- NEVER delay the initial scan when starting a monitor.
- ALWAYS use the most specific tool for tasks.
