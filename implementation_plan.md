# Implementation Plan: Worth-It Functional Fixes

## 1. Wishlist URL Detection
- **Root Cause**: The regex `_ITEM_ID_RE` in `product_url.py` only matches `/instamart/item/<id>`, failing for `instamart.in/item/<id>` and general `swiggy.com` URLs without `/instamart/`. 
- **Fix**: Update regex to `r"(?:/instamart/item/|/item/)([a-zA-Z0-9_-]+)"`. Handle URL parsing gracefully in both `product_url.py` and `useWishlist.ts`, distinguishing between "Not Found" and "Invalid URL".

## 2. Wishlist Parallel with Category Search
- **Root Cause**: The frontend `useDealSearch.ts` branches to a separate `/api/product/wishlist/stream` endpoint if `product_urls` are present, completely skipping category search.
- **Fix**: Make frontend ALWAYS call `/api/search/stream`. The backend `DealSearchOrchestrator` already supports combining `keyword` and `product_urls` in `run_combined_search`.

## 3. Wishlist UI
- **Fix**: Update `WishlistSection.tsx` to render rich wishlist items (Image, Name, Price, "Track" Checkbox, Remove button). Unchecked items remain in state but are not sent in the search request.

## 4 & 5. Keyword Picker UI & Category-Specific Data
- **Fix**: Create a `categoryKeywords.ts` mapping. Convert `KeywordInput.tsx` into a dropdown picker that suggests keywords based on selected categories. Allow typing manual keywords (appending on Enter). Ensure case-insensitive deduplication.

## 6 & 7. Continuous Scanning & UI
- **Root Cause**: The SSE stream simply completes after one sweep, and the frontend marks it as `COMPLETED`.
- **Fix**: Implement a controlled loop in the frontend `useDealSearch.ts` governed by a `isContinuous` state (default true). When a scan finishes, it transitions to `WAITING_FOR_NEXT_SCAN` (e.g. waiting 3 minutes), then automatically restarts. The user can explicitly stop it. This respects rate limits and keeps connections fresh.

## 8, 9, 10, 11, 12. Alerts, Telegram Decoupling, and Browser Notifications
- **Root Cause**: Alert background jobs currently rely heavily on Telegram, and Deal Radar live scans do not persist alerts. 
- **Fix**: 
  - Update `search.py` to route all discovered deals through the `AlertEngine` using a dynamic "Live Radar" rule. This automatically persists them to the database and handles deduplication (cooldown, better price checks) based on the existing logic.
  - Implement standard HTML5 `Notification` API in the frontend `useDealSearch.ts` or `App.tsx` for deals found. Add a "Browser Notifications" toggle in Settings.
  - Ensure `AlertRunner` executes and persists alerts even if Telegram is unconfigured. Telegram will simply be an optional delivery channel in `NotificationService`.

## Verification Plan
- Build frontend (`npm run build`) and run backend tests (`pytest`).
- Start dev servers and manually verify:
  - Valid and invalid Swiggy Instamart URLs.
  - Keyword picker dropdown based on categories.
  - Continuous scanning automatically entering "WAITING_FOR_NEXT_SCAN" and restarting.
  - Persistent alerts appearing on the Alerts page without Telegram configured.
  - Browser notifications triggering on new deals.
