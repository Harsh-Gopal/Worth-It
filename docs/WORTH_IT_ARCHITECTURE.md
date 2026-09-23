# Worth-It Architecture Guidelines

## Core Principles
1. **Platform Independence**: Platform adapters (`app/platforms/`) must be isolated from the search orchestration engine and frontend logic.
2. **Domain Driven Design**: Internal services communicate using Domain Event Objects, not raw JSON dictionaries.
3. **Resilience over Purity**: The failure of one platform (or a single store scan within a platform) must NEVER cause the entire orchestration engine to halt.

## The DealSearchOrchestrator
The `DealSearchOrchestrator` is the core engine responsible for scanning locations and checking products. 
- It MUST yield explicitly typed Domain Events from `app/domain/models/events.py` (e.g. `DealFoundEvent`, `SearchStartedEvent`, `PlatformErrorEvent`).
- It MUST perform location resolution pre-flights natively (e.g., automatically calling `resolve_store` if `local_store_id` is missing) to prevent STAGE 1 bypasses.
- Any platform-level exception during a scan must be caught natively within the orchestrator and yielded as a `SearchErrorEvent` to prevent generator death.

## Platform Adapters
Platform clients (Instamart, Zepto, Blinkit) are ONLY responsible for translating HTTP requests to Domain Models.
- **NEVER** use visual properties (like `widget_type`) to filter valid products. Scraping logic should be robust enough to handle UI variations.
- Platform clients MUST return `CanonicalProduct` or `PlatformProduct` objects.
- Platform clients MUST NOT return dictionaries that leak external API implementations.

## Event Consumption
- The `search.py` SSE endpoint is responsible for translating the yielded Domain Events into JSON strings for frontend consumption.
- The `alert_runner.py` service consumes Domain Events as typed Python objects directly. It must not rely on parsing `["data"]["_flat"]` string payloads.
