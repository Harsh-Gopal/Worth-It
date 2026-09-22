# Worth-It — History, Deal Threshold & Tracking Fixes

## Project Context

This is the implementation specification for the current Worth-It project.

Worth-It is a persistent deal-discovery and monitoring application evolved from the earlier CartRadar / Instamart-Alerts architecture. It scans quick-commerce products and surfaces deals based on categories, keywords, location, discount thresholds, price conditions, and historical pricing.

Current work covers:

1. History page redesign and correctness
2. Duplicate-product grouping across stores/locations
3. Category-aware and keyword-aware minimum discount tracking
4. Discount-selector popover positioning
5. Backend persistence, deletion, deduplication, APIs, and tests

IMPORTANT:
- Do not make superficial frontend-only patches.
- Inspect frontend, backend, database/persistence, API contracts, models, services, and tests first.
- The feature is complete only when frontend + backend + persistence + tests work together.
- Preserve existing working functionality.
- Do not hardcode fake history/store/location data.
- Reuse existing product, platform, location, map-link, scanner, and TargetRule logic wherever possible.

---

# 1. HISTORY PAGE — REQUIRED BEHAVIOR

## Current Problem

The History page currently displays the same product multiple times when the scanner discovers it at multiple stores/locations.

Example:

- Product: Elvan Assorted Chocolate Pack Imported
- Store A: ₹99, 72% discount
- Store B: ₹105, 70% discount
- Store C: ₹99, 72% discount
- Store D: ₹110, 68% discount

The History page must NOT render four separate top-level cards.

Instead render ONE product-level entry:

```text
Elvan Assorted Chocolate Pack Imported
INSTAMART

Best price ₹99
72% OFF

Available at 4 nearby stores
[Check prices at other stores]
```

Expanding it should reveal every store/location:

```text
Available at 4 nearby stores

Store / Location 1
₹99
72% OFF
PIN: 800001
[Open in Maps]
[Open Product]

Store / Location 2
₹105
70% OFF
PIN: 800002
[Open in Maps]
[Open Product]
```

The top-level card represents the product; the expanded section represents location-level observations.

---

# 2. PRODUCT DEDUPLICATION / GROUPING

Group duplicate observations of the same product within the same history/discovery context.

Prefer this identity order:

1. Platform product ID
2. Canonical product URL
3. Normalized product URL
4. Normalized product name + platform as fallback

Do NOT group products using only price, discount, or a loose name match.

For example, different pack sizes/products must remain separate even if names are similar.

The grouping should preferably happen in the backend/domain layer so the frontend receives clean product groups instead of reconstructing everything from duplicated raw observations.

---

# 3. TOP-LEVEL HISTORY CARD

Each product gets ONE top-level history card.

Show:

### Product information
- Product image
- Category-specific SVG fallback if image is unavailable
- Product name
- Platform badge
- Discovery time
- Deal/discount badge

### Deal information
- Best current price
- MRP
- Discount percentage
- Best-price indicator
- Number of locations

Example:

```text
Elvan Assorted Chocolate Pack Imported

INSTAMART

₹99
₹349 MRP
72% OFF

Best price across locations
Available at 4 locations
```

Actions:
- Open Product
- Check prices at other locations
- Open Maps where relevant
- Expand/collapse

Do not overload the top-level card with every store.

---

# 4. LOCATION / STORE EXPANSION

Clicking `Available at N locations` or `Check prices at other locations` should expand inline.

Each location should contain:

- Store/platform name
- Product price
- MRP
- Discount %
- Pincode
- Nearby address if available
- Coordinates if available
- Product availability
- Product URL
- Google Maps/location link

If coordinates exist, prefer a Maps link generated from coordinates. If not, use the best available address/pincode information. Never invent location data.

Sort locations by:

1. Cheapest price
2. Highest discount when prices tie
3. More precise location information
4. Stable fallback ordering

Mark the cheapest result clearly as `BEST PRICE`. If prices tie, do not falsely select one as cheaper.

---

# 5. HISTORY DATE STRUCTURE

History should behave similarly to Chrome history.

## Today

Today is expanded by default:

```text
TODAY     50 discoveries     7 products
```

Products are visible.

## Previous days

Previous dates are collapsed:

```text
YESTERDAY     50 discoveries     7 products     ▾
```

Clicking the date expands it.

Date summaries may include:
- discovery count
- unique product count
- platform count
- unique location count

Do not count duplicate store observations as separate products.

---

# 6. HISTORY RETENTION — LAST 7 CALENDAR DAYS

History must retain only the latest 7 calendar days.

Keep:
- Today
- Previous 6 calendar days

Older records must actually be deleted from backend persistence.

Do not merely hide old records in the frontend.

Cleanup should run automatically through the backend startup/scheduler/background mechanism and use server/database time plus the application's intended timezone.

Do NOT implement this as `now - 7*24 hours` if the requirement is seven calendar days.

---

# 7. MANUAL DELETE HISTORY

Each date section should have a delete action.

Example:

```text
YESTERDAY                                      🗑
```

Clicking delete should show confirmation:

```text
Delete Yesterday's History?

This will permanently remove 50 deal discoveries from yesterday.

Cancel
Delete History
```

After confirmation:

1. Frontend calls backend DELETE endpoint.
2. Backend validates the date.
3. Backend deletes persisted records belonging to that calendar date.
4. Backend returns success/failure and deleted count.
5. Frontend refreshes from backend.
6. Deleted date disappears.

IMPORTANT:
The current behavior appears to be frontend-only in some cases. Fix the actual persistence operation. Refreshing the browser must NOT restore deleted records.

---

# 8. DELETE API

Inspect existing routing conventions and add an appropriate endpoint, conceptually:

```text
DELETE /history/date/{date}
```

Backend must:
- validate date
- safely handle nonexistent dates
- delete persistent records
- return deleted count
- report database errors correctly
- never return success if deletion failed

Conceptual response:

```json
{
  "success": true,
  "date": "2026-09-20",
  "deleted_count": 50
}
```

Adapt to existing project response conventions.

---

# 9. HISTORY PRICE BUG

There is currently a problem where History sometimes displays:

```text
₹
Price detected
```

instead of the actual price.

Trace the complete lifecycle:

```text
scanner
→ deal/product model
→ database/persistence
→ history API
→ frontend transformation
→ history card
```

Fix the root cause.

History records should contain, where available:

- current price
- MRP
- discount %
- product identity
- product name
- product URL
- platform
- location/pincode
- coordinates/address
- discovery timestamp

Verify the API field names match frontend expectations.

If price is genuinely unavailable, display:

```text
Price unavailable
```

not a misleading currency symbol.

---

# 10. RECOMMENDED HISTORY DATA MODEL

Keep product identity separate from store observations.

Conceptually:

```text
HistoryProductGroup
    product_identity
    product_name
    platform
    product_image
    category
    discovered_at
    best_price
    best_mrp
    best_discount
    location_count
    locations[]

HistoryLocationObservation
    product_identity
    platform
    store_id
    store_name
    price
    mrp
    discount_percent
    pincode
    latitude
    longitude
    address
    product_url
    availability
    observed_at
```

Do not necessarily create these exact classes/tables if existing models can support the behavior. Extend the current architecture cleanly.

---

# 11. CATEGORY-AWARE MINIMUM DISCOUNT SYSTEM

A single global minimum discount is insufficient because different categories have different typical discount patterns.

For example:
- Milk may be meaningful even around 5%.
- Chocolate may need a substantially larger discount before being considered especially notable.
- Electronics may have different discount expectations.

These examples are illustrative. The important requirement is user-configurable category thresholds.

---

# 12. CATEGORY DISCOUNT UX

Clicking a category such as:

```text
Sports & Fitness
```

must open a compact contextual discount selector attached to that category.

It must NOT appear at the bottom of the page.

It must NOT create a second global minimum-discount card.

Use a popover/dropdown with an arrow/tail pointing to the clicked category.

Example:

```text
Sports & Fitness
        ↓
 ┌─────────────────────┐
 │ Minimum discount    │
 │                     │
 │ Custom [ 15 ] %     │
 │ [Apply]             │
 │                     │
 │ 10% 15% 20% 30%     │
 │ 40% 50% 60% 70%     │
 │ 80% 85% 90% 95%     │
 │       99%            │
 └─────────────────────┘
```

Presets:

```text
10%, 15%, 20%, 30%, 40%, 50%, 60%, 70%, 80%, 85%, 90%, 95%, 99%
```

Also support a custom percentage.

Popover requirements:
- attached to actual clicked element
- viewport-aware
- flips above/below/left/right when necessary
- click-outside closes it
- Escape closes it
- no detached bottom-of-page panel
- no unnecessary layout shift
- current value visibly selected

---

# 13. UNIFIED MINIMUM DISCOUNT CONTROL

Remove duplicate minimum-discount controls.

Use one source of truth.

Support:

```text
Category rule:
Sports & Fitness ≥15%

Keyword rule:
Whey Protein ≥20%

Global fallback:
used only when no more specific rule applies
```

The UI must clearly distinguish category/keyword thresholds from any global fallback.

---

# 14. CATEGORY BADGES

After selecting a threshold, the category itself displays the value:

```text
Sports & Fitness ≥15%
```

Clicking it again reopens the selector.

The current value is selected.

The user can change it or remove the rule with `×`.

Removing it must:
- remove active category state
- remove/disable the backend category rule
- restore unconfigured category appearance
- not affect other rules

---

# 15. KEYWORD-AWARE THRESHOLDS

Keywords use the same mechanism.

Example:

```text
Whey Protein ≥15% ×
```

A keyword should store:
- keyword
- minimum discount threshold
- enabled state

The keyword chip must support:
- click to edit threshold
- `×` to remove
- visible threshold
- persistence after reload

Do not treat configured keywords as plain text-only search terms.

---

# 16. RULE PRECEDENCE

Implement deterministic backend precedence:

```text
Specific keyword rule
        ↓
Category rule
        ↓
Global minimum discount
        ↓
No minimum discount
```

If multiple matching keyword rules exist, use the strictest applicable threshold unless the existing domain model explicitly requires another deterministic strategy.

Example:

```text
Sports & Fitness ≥15%
Whey Protein ≥25%
```

A Whey Protein item in Sports & Fitness must use:

```text
≥25%
```

This logic belongs in the backend/domain layer, not only React.

---

# 17. TARGET RULE ARCHITECTURE

Inspect and reuse the existing TargetRule/alert-rule architecture.

Conceptually:

```text
target_type:
    category | keyword

target_value:
    Sports & Fitness
    Whey Protein

min_discount_percent:
    15

enabled:
    true
```

Do not create a parallel rules system if the existing architecture can be extended cleanly.

---

# 18. FRONTEND ↔ BACKEND SYNCHRONIZATION

When the user selects a threshold:

1. frontend sends the selected target + threshold
2. backend validates it
3. backend persists it
4. backend returns saved server state
5. frontend updates from server response

If safe optimistic updates already exist, they may be used, but important tracking configuration must not exist only in React state/localStorage.

Reloading the Monitor page must restore saved rules.

---

# 19. ACTIVE TARGET SUMMARY

Show a compact summary of active targets:

```text
Active targets

Sports & Fitness ≥15%
Whey Protein ≥20%
Home & Kitchen ≥10%
```

Keep this modern and compact.

Do not duplicate the same threshold information in another large Minimum Discount panel.

---

# 20. DEAL EVALUATION

For each scanned product:

1. identify product
2. identify category
3. identify matching keywords
4. resolve applicable TargetRules
5. calculate effective minimum discount
6. compare actual discount
7. determine qualification
8. persist history/deal information according to existing semantics

Examples:

```text
Category ≥15%
Actual discount = 12%
→ does not qualify
```

```text
Category ≥15%
Keyword ≥25%
Actual discount = 30%
→ qualifies using keyword rule
```

Backend is the source of truth.

---

# 21. HISTORY + RULE CONTEXT

Where useful, preserve discovery context in history:

```text
matched_rule_type
matched_rule_value
effective_min_discount
actual_discount
```

This allows history to explain:

```text
30% OFF ≥ 25% target
```

rather than only showing `30% OFF`.

Historical records should remain understandable even after the user changes current tracking rules.

---

# 22. CATEGORY-SPECIFIC IMAGE FALLBACKS

When product images fail or are missing, never show a blank space.

Use category-specific SVG fallbacks.

Examples:

```text
Chocolate / Snacks → snack/chocolate SVG
Milk / Dairy → dairy SVG
Sports & Fitness → fitness SVG
Beauty → beauty SVG
Electronics → electronics SVG
Home & Kitchen → home SVG
Baby Care → baby SVG
Pet Care → pet SVG
Daily Essentials → essentials SVG
Unknown → generic product SVG
```

Fallback order:

```text
valid product image
    ↓
category SVG
    ↓
generic SVG
```

Handle broken image URLs with an image error handler.

The SVGs should visually match Worth-It.

---

# 23. HISTORY PERFORMANCE

Use:

```text
Date
  ↓
Product groups
  ↓
Best-price summary
  ↓
Expandable location observations
```

Do not render every location as a top-level card.

If needed, lazy-render location details only when expanded.

Avoid repeatedly fetching the same data.

---

# 24. HISTORY API

Inspect existing endpoints before adding new ones.

Conceptually support:

```text
GET history
GET history?date=YYYY-MM-DD
DELETE history/date/YYYY-MM-DD
```

Adapt to the project's actual routing conventions.

GET should provide enough information for:
- date groups
- product groups
- best price
- best discount
- product metadata
- location count
- nested location observations

Prefer backend grouping rather than sending raw duplicate observations for the frontend to deduplicate.

---

# 25. DATABASE / PERSISTENCE

Inspect the current persistence layer.

Ensure persistence supports:

- timestamps
- price
- MRP
- discount
- product identity
- platform
- pincode
- coordinates/address
- product URL
- deletion by calendar date

Add appropriate indexes around timestamp/date and product identity if necessary.

Avoid unnecessary migrations if existing schema can safely be extended.

---

# 26. AUTOMATIC RETENTION CLEANUP

Implement backend cleanup that calculates the calendar-day retention boundary.

Keep exactly seven calendar days:

```text
today + previous 6 days
```

Delete older records.

Make the calculation testable.

Run cleanup at application startup and/or using the existing background scheduler.

---

# 27. TESTING REQUIREMENTS

## Backend tests

History grouping:
- same product at multiple stores → one product group
- different products → separate groups
- same name but different IDs → separate groups
- multiple prices → correct best price

Best price:
- cheapest store selected
- equal prices handled
- discount tie-breaker deterministic

Deletion:
- delete specific date
- records actually removed from persistence
- nonexistent date handled safely
- re-query confirms deletion

Retention:
- records inside seven calendar days remain
- older records removed
- date boundary behavior correct

Price:
- scanner → database → API → history preserves price

Discount rules:
- category rule
- keyword rule
- keyword precedence
- global fallback
- removal
- persistence after reload

## Frontend/manual verification

History:
- today expanded
- older dates collapsed
- date toggle works
- duplicate product appears once
- location expansion works
- location price/pincode/map link visible
- actual price visible
- delete confirmation works
- deletion persists after browser refresh

Monitor:
- category click opens contextual popover
- popover has arrow/tail
- viewport-aware positioning
- 15% selection displays `Category ≥15%`
- clicking again reopens selector
- editing threshold works
- `×` removes rule
- keyword behaves identically
- multiple targets coexist
- duplicate global minimum discount control removed
- rules persist after reload

---

# 28. IMPLEMENTATION WORKFLOW

Before editing:

1. Inspect History frontend components.
2. Inspect History API routes.
3. Inspect database/persistence models.
4. Inspect deal/product models.
5. Inspect TargetRule implementation.
6. Inspect current category/keyword state.
7. Inspect current discount popover implementation.
8. Inspect related tests.

Then implement root-cause fixes.

Do not rewrite unrelated application areas.

After implementation:

1. Run backend tests.
2. Run frontend lint/type checks/build.
3. Run relevant integration tests.
4. Exercise History.
5. Exercise category thresholds.
6. Exercise keyword thresholds.
7. Test real persisted deletion.
8. Refresh and verify deletion remains deleted.
9. Verify duplicate products are grouped.
10. Verify price is actually displayed.

---

# 29. DEFINITION OF DONE

- [ ] One top-level History card per unique product/discovery group.
- [ ] Multiple store/location observations grouped under the product.
- [ ] Cheapest price shown prominently.
- [ ] Other store prices available through expansion.
- [ ] Store rows show price, discount, pincode, and map access.
- [ ] History product price is correctly persisted and displayed.
- [ ] Today expanded by default.
- [ ] Previous dates collapsible.
- [ ] Only latest seven calendar days retained.
- [ ] Older history automatically deleted server-side.
- [ ] User can delete a specific date.
- [ ] Date deletion actually removes persistent records.
- [ ] Deleted history does not return after refresh.
- [ ] Category-specific thresholds work.
- [ ] Keyword-specific thresholds work.
- [ ] Keyword rules have deterministic precedence.
- [ ] Active targets show thresholds.
- [ ] Category/keyword selector is a contextual popover.
- [ ] Popover attaches to clicked target and stays in viewport.
- [ ] Duplicate global minimum-discount UI removed.
- [ ] Rules persist after reload.
- [ ] Broken/missing product images use category SVG fallbacks.
- [ ] Backend and frontend tests pass.
- [ ] Existing functionality remains intact.

## Final Instruction to the IDE Agent

Treat this as a real end-to-end feature implementation, not a UI mockup.

Trace:

```text
scanner
→ deal evaluation
→ TargetRule resolution
→ persistence
→ history grouping
→ API
→ frontend
```

and:

```text
user interaction
→ category/keyword threshold
→ API
→ backend rule persistence
→ scanner/deal engine
```

and:

```text
history delete
→ confirmation
→ DELETE API
→ database deletion
→ refreshed GET
→ UI
```

Fix root causes rather than masking symptoms.

Reuse existing Worth-It architecture, keep the implementation maintainable, and verify actual persisted behavior before declaring completion.
