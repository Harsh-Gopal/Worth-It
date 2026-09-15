# Worth-It

A premium, geocentric "deal intelligence" engine that monitors Swiggy Instamart for hidden hyper-local deals and historically low prices, delivering them via real-time alerts.

## 1. Project Goal
The primary objective of **Worth-It** is to answer the question:
> "Can you find this product/deal in my Instamart area? If it isn't available at my local store, how far out do I have to search to find it on a massive discount?"

## 2. Product Philosophy
"Find the price worth buying." 
Worth-It utilizes a clean, premium, minimalistic interface that focuses entirely on practical utility. It abandons flashy "AI-generated" designs in favor of high readability and efficient scanning.

## 3. Core User Flows
- **Search & Discovery**: Define targets via Categories, Keywords, or Wishlist URLs.
- **Geographic Sweep**: Engine scans local store -> expands radius -> reports deals in real time.
- **Background Alerts**: User configures Telegram to receive automatic drops.

## 4. Search Architecture
The system supports a **Combined Search Mode**. Users can query categories/keywords while simultaneously checking direct Wishlist URLs. The backend `DealSearchOrchestrator` merges these streams concurrently.

## 5. Wishlist Architecture
Users can build a local wishlist directly on the Search page by pasting specific `instamart/item/` URLs. 
- **Storage**: The wishlist state is persisted using browser `localStorage` (`worth_it_wishlist`) to provide a seamless local desktop app experience without requiring heavy backend schemas.
- **Enrichment**: Adding a URL automatically fetches the product's name, brand, image, and current baseline price.
- **Priority**: Selected wishlist items are evaluated with highest priority and labeled as "Tracked" in the frontend results, alongside any generic keyword discovery results.

## 6. Category/Keyword Architecture
Provides broad discovery matching against Instamart's taxonomy and product titles. Exclusion keywords filter out noise.

## 7. Combined Search Behavior
The orchestrator deduplicates overlapping deals between Wishlist and Keyword searches, ensuring the UI receives a pristine stream of prioritized matches.

## 8. Geographic Search Architecture
Uses a hex-grid algorithm to generate lat/lng probes. Probes resolve to physical Instamart dark stores. Stores are scanned sequentially outward up to a 20km limit.

## 9. Deal Filtering
Client-side criteria (min discount, price drop %, max price) are evaluated server-side against live and historical price data before a deal event is emitted.

## 10. Ranking/Prioritization
Deals are implicitly ranked by proximity and source (Wishlist > Keyword).

## 11. Deduplication
Server-side `seen_deals` set prevents a product from being emitted twice from overlapping search modes.

## 12. Telegram Architecture
Users register their Bot Token (from BotFather) and Chat ID. The backend verifies the token and securely dispatches background notifications.

## 13. Frontend Architecture
Vite + React + TailwindCSS. Uses SSE (Server-Sent Events) to stream geographic progress and deal matches dynamically without polling.

## 14. Theme System
Implemented a pure CSS-variable driven Light and Dark mode synced with system preferences, built natively onto Tailwind `dark:` mode.

## 15. Logo System
A dynamic SVG logo responsive to `currentColor`, representing downward price drops (green V's) and value spikes (red caret).

## 16. Local Development
Run `./dev.sh` to spin up both FastAPI and Vite servers automatically.

## 17. Environment Variables
Stored in `backend/.env`. Includes `TELEGRAM_BOT_TOKEN` and testing coordinates.

## 18. Testing Performed
- 29/29 Pytest suites passing (Alerts, Geography, Orchestrator, Matchers).
- Vite frontend build (`tsc -b && vite build`) passing.
- Manual E2E validation of combined searches and theming.

## 19. Known Limitations
- Hard 20km limit enforced server-side.
- Cloudflare/WAF may occasionally block rapid sequential searches.

## 20. Future Improvements
- Multi-platform support (Zepto, Blinkit).
- Time-series price history graphs in UI.
