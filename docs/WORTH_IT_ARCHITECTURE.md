READ THIS FILE BEFORE MODIFYING TARGET, SEARCH, MONITORING, PLATFORM, DISCOUNT, OR SCHEDULER LOGIC.

# Worth-It Architecture & Implementation Contract

This document is the authoritative implementation contract for the Worth-It project. It defines the core architecture, semantics, product rules, and UI constraints that MUST be followed during any development or refactoring. 

## 1. Project Purpose
Worth-It is a personal/open-source multi-platform quick-commerce deal discovery and monitoring application. It allows a user to monitor dynamic inventory across multiple q-commerce platforms and receive alerts for deals matching specific discount criteria.

## 2. Supported Platforms
- Swiggy Instamart
- Zepto
- Blinkit

## 3. Platform Adapter Architecture
Each platform has its own adapter implementing search and extraction logic. The adapters are strictly responsible for returning normalized product data (price, MRP, stock status, discount percentage). They do not manage scheduling or persistence.

## 4. Orchestration Layer
The orchestration layer sits above the platform adapters. It takes a logical target (e.g. `Whey ≥ 30%`) and fans out execution to the chosen platforms. The orchestrator handles retries, deduplication, and uniform error reporting.

## 5. Keyword Discovery Semantics
A Keyword target is a SEARCH/DISCOVERY target. It instructs the scanner to search the string on the platform and evaluate all returned results. A keyword must NEVER be permanently converted into a specific product ID after discovery, as this prevents new or returning inventory from being found on subsequent scans.

## 6. Category Discovery Semantics
A Category target behaves identically to a keyword discovery target but maps to broader platform-specific category pages or tags (e.g., `Electronics`). Like keywords, it evaluates all available products under the category for deals matching the criteria during every scan.

## 7. Direct Product URL Semantics
Wishlist or Product tracking uses explicit product URLs. This form of tracking IS bound to a specific product ID because the user explicitly provided the canonical item. 

## 8. Why Keyword Searches Must NOT Become Permanent Product-ID Tracking
Inventory, prices, and available deals in q-commerce shift rapidly. If a search for "Atta" yields "Brand A Atta" today, binding to that specific product ID means we would miss "Brand B Atta" becoming cheaper tomorrow. Fresh discovery is mandatory on every cycle for keywords and categories.

## 9. Multi-platform Fan-out
A single frontend target (e.g., `Oats ≥ 20%`) may be evaluated against multiple platforms if the user checked multiple platforms. Do NOT duplicate the target in the frontend state or backend database merely because multiple platforms are selected. The fan-out is a runtime behavior in the orchestrator.

## 10. Target Model
The canonical conceptual representation of an active target is:
```typescript
{
    type: "keyword" | "category" | "product",
    value: string,
    min_discount_percent: number, // Must not be null for an active target
}
```

## 11. Discount Percentage Behavior
Every category and keyword target requires exactly ONE minimum discount value. There is no global "Deal Criteria" section. The discount lives on the specific target.

## 12. Keyword/Category Popup Behavior
Clicking a category chip or entering a keyword opens the unified `DiscountPopover` component. This popover anchors to the target chip and manages the assignment of the minimum discount.

## 13. Preset Discount Behavior
Clicking a preset percentage (e.g. 20%) in the `DiscountPopover` immediately commits the target to the active state and closes the popup. No separate "Apply" button is needed for presets.

## 14. Custom Discount Behavior
Entering a numeric value in the custom input requires the user to click the "Apply" button. The value must be validated (≥0, ≤99, valid format) before committing. 

## 15. Active Target Rules
Only configured targets (those with a valid `min_discount_percent`) are displayed in the Active Targets list. A target in an intermediate unconfigured state (e.g., during discount selection) is a purely visual temporary UI state and must not be injected into the application's core state arrays.

## 16. Exclude Keyword Behavior
Users can specify words (e.g., "Protein Bar") to exclude from discovery matches when monitoring a broader keyword (e.g., "Protein"). This filter is applied globally across the current scan session.

## 17. Current Pincode Only Mode
Restricts location tracking/store assignment strictly to the user's primary/current pincode coordinates.

## 18. Nearby Area Mode
Allows discovery and scanning across multiple adjacent stores or slightly wider geographic areas within the platform's delivery radius.

## 19. Geographic Scanning
The backend handles geographic translation (lat/lng, store IDs).

## 20. Store Deduplication
When scanning multiple stores on a single platform, the system deduplicates identical deals to prevent alert spam, merging them into a unified deal record.

## 21. Map Behavior
Displays scanned stores and deal origins visually, utilizing existing location hooks.

## 22. History Behavior
All executed scans are persisted, allowing users to view historical Deal events.

## 23. Price Observation Behavior
Prices are recorded historically for specific items when deals trigger, building a price history chart over time.

## 24. Deal Detection
Deals are detected dynamically when a scanned product's computed discount meets or exceeds the target's `min_discount_percent`.

## 25. Alert Engine
Generates system notifications/webhooks when a new deal passes the threshold logic.

## 26. Scheduler
Runs background asynchronous loops evaluating active targets at the configured interval.

## 27. Scan Intervals
User-defined frequency (e.g., 15 mins, 30 mins) for the scheduler.

## 28. SSE/Live Monitoring
Server-Sent Events provide real-time console feedback during active scans so the user can watch the search progress.

## 29. Wishlist Behavior
A dedicated UI for pasting direct product URLs to track explicitly.

## 30. Direct Product Tracking
Bypasses discovery, fetching exact item metadata and price repeatedly.

## 31. Frontend State Rules
Component state must strictly distinguish between "draft/pending" UI selections and committed tracking targets. Do NOT use `null` discount values to represent active targets.

## 32. Backend API Contracts
The frontend target model must serialize cleanly to the backend's expected alert schema.

## 33. Important Invariants
- A target is either configured or non-existent.
- Keywords trigger search endpoints, not product endpoints.

## 34. Known Architectural Constraints
- Rate limiting by platforms requires the orchestrator to pace requests.

## 35. Performance Optimizations
- Deduplication prevents repetitive parsing.
- React components should avoid rendering loops caused by unstable effect dependencies.

## 36. Testing Requirements
Any changes to target logic MUST be tested across Categories and Keywords.

## 37. Chrome Agent Verification Procedure
When verifying UI changes, use the Chrome Subagent to execute actual clicks, keystrokes, and mode toggles on `localhost`. Do not rely solely on unit tests for component state flows.

## 38. Common Regressions to Avoid
- Reintroducing the "Set %" intermediate state as an active target.
- Breaking the opacity/readability of the DiscountPopover.
- Duplicating a target when editing its discount percentage.

---

## NON-NEGOTIABLE PRODUCT RULES

- Never introduce a "Set %" state into the active targets array.
- Keyword and category discount selection MUST use the exact same `DiscountPopover` logic.
- Preset percentage selection immediately commits the target without requiring an apply button.
- Custom percentage requires clicking Apply.
- Keyword and Category searches MUST remain discovery searches (evaluating all returned items).
- Never permanently bind a keyword search to the first discovered product ID.
- Direct product URLs may use product-level tracking.
- No duplicate global Deal Criteria section; discount thresholds belong strictly to the individual targets.
- One logical target may fan out across multiple platforms.
- Do NOT duplicate the same target in the frontend state merely because multiple platforms are selected.
