# Worth-It Architecture

Worth-It is designed as a deployable quick-commerce deal intelligence platform. It consists of a decoupled React frontend and a FastAPI Python backend, communicating via REST APIs and Server-Sent Events (SSE).

## System Overview

1. **Frontend (Vercel)**: UI for configuration, live monitoring, and history viewing.
2. **Backend API Layer (Render)**: REST endpoints and background processes.
3. **Orchestration Layer**: Manages parallel discovery across isolated platform adapters.
4. **Platform Adapter Layer**: Isolated scrapers and API clients for quick-commerce vendors.
5. **Deal Evaluation Engine**: Shared domain logic for pricing thresholds and deal validation.
6. **Persistence & Alert Engine**: SQLite history tracking, deduplication, and Telegram notifications.

---

## Frontend Architecture

- **Framework**: React 19 + Vite + TypeScript.
- **Styling**: TailwindCSS V4.
- **State Management**: Zustand for global state and `useSyncExternalStore` for SSE streams.
- **Components**:
  - `LiveConsole`: Consumes `/api/search/stream` SSE endpoints for real-time visibility into active scans.
  - `ProductSearch`: Configuration UI (keywords, wishlists, location modes).
  - `TrackHistory`: Displays locally persisted `AlertEvent` objects.

## Backend Architecture

### API Layer
Located in `app/api/routers/`. Standard FastAPI routes exposing CRUD operations for Monitoring Rules, History, Authentication, and Telegram. All mutation endpoints are secured via the `verify_auth` dependency.

### Orchestration Layer
`DealSearchOrchestrator` (`app/domain/services/search_orchestrator.py`) handles the lifecycle of a scan:
1. Resolves locations and generates scanning footprints (e.g., exact pincode or hex-grid).
2. Executes concurrent product searches on the active platform adapters.
3. Normalizes platform-specific schemas into canonical `PlatformProduct` objects.
4. Invokes the Deal Engine and forwards events to the `AlertRunner`.

### Platform Adapter Layer
Located in `app/platforms/`. Follows the **Adapter Pattern** via the `PlatformClient` interface.
Each integration (`swiggy`, `blinkit`, `zepto`, `flipkart`) is strictly isolated. They encapsulate request structuring, headers, DOM parsing, and bypass logic.

### Deal Evaluation Engine
`DealEngine` (`app/domain/services/deal_engine.py`) takes a `PlatformProduct` and evaluates it against user rules. It verifies discounts, calculates accurate percentages, and scores the deal based on historical norms.

### Price History & Alert Engine
- `PriceHistoryService`: Maintains SQLite records of previously seen items.
- `AlertEngine`: Handles deduplication (e.g., cooldown intervals) and groups identical deals found across multiple nearby stores to prevent alert spam. 

### Scheduler
Uses `APScheduler` (`app/scheduler.py`) to run background jobs at configured intervals.

### Database/Persistence
SQLite3 with WAL mode enabled (`app/persistence/`). Ensures zero-setup persistence for price history and user configurations.

---

## Deployment Architecture

Worth-It is optimized for modern cloud deployments:

### Frontend (Vercel)
A purely static Single Page Application (SPA).
- `vercel.json` provides client-side routing rewrites.
- API requests are prefixed with `VITE_API_URL` allowing full separation from the backend server.

### Backend (Render)
A containerized Python FastAPI service.
- The `backend/Dockerfile` defines the production environment, relying on `uv` for dependency management.
- Persistent disks (Render Volumes) should be mounted to `/app/backend/data` to preserve the SQLite database.
- Telegram Bot polling and background schedulers run natively alongside the web server.

### Security Boundaries
- **Server-side Secrets**: Telegram Bot Tokens and Admin PINs live exclusively on the backend via environment variables. The frontend is never exposed to raw credentials.
- **Authentication**: A stateless PIN-driven authentication model is enforced by FastAPI dependencies, issuing short-lived HttpOnly session cookies.
