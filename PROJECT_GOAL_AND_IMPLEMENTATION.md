# Worth-It

A premium, geocentric "deal intelligence" engine that monitors Swiggy Instamart for hidden hyper-local deals and historically low prices, delivering them via real-time alerts.

## 🎯 Project Goal

The primary objective of **Worth-It** is to answer the question:

> "Can you find this product/deal in my Instamart area? If it isn't available at my local store, how far out do I have to search to find it on a massive discount?"

The system goes beyond a typical web scraper by utilizing **Progressive Geographic Expansion**. It maps the physical world using Haversine distances and hexagonal grids, sweeping outward from the user's location to ping dozens of local micro-fulfillment centers (dark stores) for specific products.

## 🏛 Architecture

### 1. Backend Engine (FastAPI + uv)
The backend is built in modern Python utilizing `uv` for dependency management and FastAPI for high-concurrency API orchestration.

- **Store Discovery (Hex-Grid Probing)**: The engine algorithmically generates a honeycomb grid of geographic coordinates radiating outward from a central lat/lng. By sending probe requests to Instamart from these coordinates, it discovers the hidden internal `store_id`s of nearby dark stores.
- **Search Orchestrator**: Manages the multi-stage search flow. It begins locally, and if no deals are found, progressively expands to 3km, 5km, and up to 20km radii.
- **Concurrency Control**: Geographic probes and targeted product lookups are bounded by `asyncio.Semaphore` to avoid triggering Web Application Firewalls (WAF) or overwhelming the upstream servers.
- **Deal Engine & Price History**: Evaluates products against composite logical AND/OR conditions (e.g. `discount >= 50%` AND `is_historical_low`). SQLite is used to persist historical price observations over time to confidently flag a "Price Drop" or "Historical Low".
- **Background Scheduler (AlertRunner)**: Utilizes `APScheduler` to run saved user alerts on a background loop. When deals meet the strict criteria (and bypass intelligent deduplication and cooldown timers), an alert is formatted.
- **Notification Provider**: Abstractions for notifications allow alerts to be seamlessly broadcasted to Telegram channels via a Bot API integration.
- **Server-Sent Events (SSE)**: The orchestrator yields asynchronous JSON progress events (`radius_scan_started`, `deal_found`, `store_discovered`) which are multiplexed via SSE to the frontend for real-time visual feedback.

### 2. Frontend Application (React + Vite + Tailwind v4)
The frontend serves as the "Radar Console" — a premium, high-tech interface completely detached from standard SaaS dashboards.

- **Dark-Glass Theme**: A custom design system leveraging CSS properties (`var(--color-neon-green)`, `var(--color-radar-bg)`) to simulate a deep space radar system.
- **Real-Time Visualization**: As SSE events arrive, the UI dynamically displays the radius scanning outward and renders deals incrementally without waiting for the full search to conclude.
- **Wishlist & Keyword Targets**: Users can hunt for deals using generic keywords (e.g. "whey protein") or input direct Instamart product URLs for exact targeting.
- **Interactive Configuration**: Sleek location resolvers, Telegram configuration wizards, and complex deal criteria inputs (price drop %, discount %) are all presented intuitively.

## 🚀 Running the Project

The project is packaged with a convenient local launcher that manages both the frontend and backend servers simultaneously.

### Requirements
- `uv` (Fast Python package installer)
- `npm` or `pnpm` (Node package manager)

### Quick Start
1. Ensure you are in the project root (`instamart-deal-radar`).
2. Run the development launcher:
   ```bash
   ./dev.sh
   ```
3. The launcher will:
   - Ensure `node_modules` are installed.
   - Boot up the FastAPI backend on `http://127.0.0.1:8000`
   - Boot up the Vite frontend on `http://localhost:5173`
   - Monitor and gracefully kill both processes on `Ctrl+C`.

4. Navigate to **http://localhost:5173** to access the application.

## 🛠 Local Development Notes

- **Database**: The SQLite database (`instamart_radar.db`) will be automatically created in the `backend/app/persistence/` directory. It manages Alert Rules, Events, Price Histories, and the Store Cache.
- **WAF Safety**: Do not modify the concurrency bounds (`discovery_sem=3`, `product_check_sem=5`) in the `DealSearchOrchestrator`. Raising these aggressively will result in IP bans or CAPTCHA challenges from upstream.
- **Store Cache**: The `store_cache` aggressively caches discovered coordinates to `store_id` mappings, drastically reducing network overhead on subsequent searches.

---
*Built as a premium deal intelligence system by Antigravity.*
