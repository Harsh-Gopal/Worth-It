# Worth-It Architecture

Worth-It is designed as a standalone, deployable quick-commerce deal intelligence platform. It consists of a decoupled React frontend and a FastAPI Python backend, communicating via REST APIs and Server-Sent Events (SSE).

## System Overview

The system is broken down into the following primary layers:
1. **Frontend**: UI for configuration, monitoring, and history.
2. **Backend API Layer**: REST endpoints for the frontend.
3. **Orchestration Layer**: Manages parallel discovery across isolated platform adapters.
4. **Platform Adapter Layer**: Contains isolated scrapers/API clients for each quick-commerce vendor.
5. **Deal Evaluation Engine**: The shared domain logic for determining if a product is a deal.
6. **Persistence & Alert Engine**: SQLite-backed history tracking, deduplication, and Telegram notifications.

---

## Frontend Architecture

- **Framework**: React + Vite + TypeScript.
- **State Management**: Zustand (for persistence and global state) + React `useSyncExternalStore` for SSE streams.
- **Components**:
  - `LiveConsole`: Consumes the `/api/search/stream` SSE endpoint to provide real-time visibility into the scanning process (which platforms are running, products discovered, deals found, errors).
  - `ProductSearch`: The configuration UI (keywords, categories, pin-code, deal thresholds).
  - `TrackHistory`: Displays locally persisted `AlertEvent` objects.

## Backend Architecture

### API Layer
Located in `app/api/routers/`. Standard FastAPI routes exposing CRUD operations for Alert Rules, History, and Location validation.

### Orchestration Layer
`DealSearchOrchestrator` (`app/domain/services/search_orchestrator.py`) handles the lifecycle of a scan:
1. Resolves the geographic location using the platform adapter's `resolve_store` method.
2. Identifies a central store ID or a grid of nearby stores (hex-grid geographic discovery).
3. Executes concurrent product searches on the active platform adapter.
4. Normalizes platform-specific JSON schemas into canonical `PlatformProduct` objects.
5. Invokes the Deal Engine.
6. Yields events back to the `AlertRunner`.

### Platform Adapter Layer
Located in `app/platforms/`. Heavily relies on the **Adapter Pattern** via the `PlatformClient` abstract base class.
Each platform integration (e.g. `swiggy`, `blinkit`, `zepto`, `flipkart`) is strictly isolated.
- **Rule of Thumb**: A change in `zepto/client.py` must *never* impact `swiggy/client.py`.
- They encapsulate headers, authentication, WAF evasion, request structuring, and DOM parsing.

### Normalized Domain Models
Defined in `app/domain/models/`.
- `PlatformProduct`: The canonical representation of a discovered item (price, MRP, stock status).
- `AlertRule`: The user-configured monitoring criteria.
- `AlertEvent`: A triggered and persisted deal.

### Deal Evaluation Engine
`DealEngine` (`app/domain/services/deal_engine.py`) takes a `PlatformProduct` and evaluates it against an `AlertRule`. It handles edge cases like fake discounts (MRP manipulation), calculates accurate percentages, and scores the deal based on historical norms.

### Price History & Alert Engine
- `PriceHistoryService`: Maintains a record of previously seen deals.
- `AlertEngine`: Handles deduplication (e.g. cooldown intervals) and groups identical deals found across multiple nearby dark stores to prevent alert spam.

### Scheduler
Located in `app/scheduler.py`. Uses `APScheduler` to run background jobs at user-defined intervals (e.g. every 30 minutes). It wakes up, loads enabled `AlertRule`s, and dispatches them to the `AlertRunner`.

### Geographic/Store Discovery
Located in `app/geo/`. 
Provides functions to generate Haversine-based hex-grids around a central latitude/longitude to systematically discover the boundaries of different dark stores. The `StoreCache` persists these boundaries to avoid redundant network requests.

### SSE/Event Streaming
`broadcast.py` utilizes `sse_starlette` to manage a Pub/Sub queue. The `AlertRunner` puts JSON events (`search_started`, `deal_found`, `platform_unavailable`) into the queue, which the frontend receives in real-time.

### Database/Persistence
SQLite3 with WAL mode enabled (`app/persistence/`). Used for zero-setup persistence, optimized for single-writer/multi-reader concurrency.

---

## Deployment Architecture

Worth-It uses a unified Docker Compose architecture optimized for one-click personal deployment:
1. **Frontend Container**: Nginx serving the static React bundle, proxying `/api/` traffic to the backend.
2. **Backend Container**: Python 3.12 running `uvicorn`. Includes Playwright dependencies internally (no reliance on the host OS's Chrome browser).
3. **Data Volume**: A persistent Docker volume (`worth-it-data`) mounts to `/app/data` to ensure SQLite price history and user configurations survive container restarts.

This architecture explicitly forbids dependencies on interactive host browser sessions, making the system viable for cloud VPS deployment out of the box.

---

## Future Platform Integration
When integrating new platforms (e.g. Zepto or Minutes):
1. Create a new package under `app/platforms/`.
2. Implement `PlatformClient`.
3. Prefer reverse-engineered internal APIs (HTTP) over Playwright automation where possible to reduce memory usage.
4. If Playwright is required, use headless automation inside the backend Docker container. Do not rely on local developer profiles.
