# Platform Integrations

This document tracks the architecture, limitations, and current implementation status for each quick-commerce platform supported (or in development) for Worth-It.

## Abstract Architecture
All platforms MUST extend the `PlatformClient` base class (`app/platforms/base.py`). The adapter is responsible for:
1. `resolve_store(lat, lng)`: Converting geographic coordinates to a local warehouse/store ID.
2. `search(query, store_id, lat, lng)`: Scraping or querying the platform and mapping results to canonical `PlatformProduct` domain objects.

---

## 1. Swiggy Instamart
**Status:** `WORKING`

### Implementation
- Directly interacts with the Instamart GraphQL/REST API.
- Converts coordinates into `storeId` effectively using the store resolution endpoints.
- Normalizes API responses accurately for prices, MRPs, and stock status.
- Implements `resolve_share_link()` to convert mobile-app share URLs into canonical product IDs.

### Known Limitations
- Aggressive IP rate-limiting can occur. Worth-It respects standard retry delays, but bulk scheduling across massive radii should be spaced out.

---

## 2. Blinkit
**Status:** `WORKING`

### Implementation
- Leverages Blinkit's public/BFF API endpoints.
- Store resolution heavily depends on the provided latitude and longitude.

### Known Limitations
- WAF (Web Application Firewall) blocks may occasionally occur. The orchestrator is designed to catch these as `platform_error` events and continue gracefully.

---

## 3. Zepto
**Status:** `IN DEVELOPMENT`

### Implementation
- The integration is currently experimental and undergoing heavy iteration.
- We are actively testing HTTP implementations (`test_zepto_curl.py`, `test_zepto_mobile_api.py`) to bypass rigid security headers without requiring heavy browser automation.
- **Goal**: Final architecture must not depend on a local developer Chrome profile.

### Known Limitations
- Highly aggressive Cloudflare/WAF protection. 
- Do **NOT** assume the integration is completely stable.
- If Playwright automation is eventually deemed necessary, it will be strictly isolated inside the Docker container.

---

## 4. Flipkart Minutes
**Status:** `IN DEVELOPMENT`

### Implementation
- Currently investigating DOM parsing versus raw API interception.
- Store availability mapping requires precise area metadata.

### Known Limitations
- Page structures change frequently. API interception is highly preferred but requires complex header forgery.
- Not production-ready.
