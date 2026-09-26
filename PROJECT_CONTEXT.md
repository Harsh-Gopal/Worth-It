# Project Context

This document serves as the high-level memory and ruleset for anyone (or any agent) working on the Worth-It codebase.

## Project Purpose
Worth-It is a deployable, highly modular quick-commerce deal intelligence and monitoring platform. It automatically scans platforms like Swiggy Instamart and Blinkit to identify extreme discounts (deals) specific to the user's local geography/pincode.

## Current Platform Status
**WORKING & STABLE:**
- Swiggy Instamart
- Blinkit

**IN DEVELOPMENT / EXPERIMENTAL:**
- Zepto
- Flipkart Minutes

**Critical Rule:** Do NOT claim Zepto or Minutes are fully supported or production-ready. They are active development targets being refined for deployment compatibility.

## Important Design Decisions & Rules
1. **Platform Isolation is Mandatory**
   - Do NOT modify a working platform adapter (e.g. Instamart or Blinkit) while attempting to fix another platform (e.g. Zepto), unless the change is rigorously proven to be shared, abstract infrastructure.
   - Platform-specific logic must stay inside `app/platforms/<platform_name>/`.
2. **Normalized Domain Models**
   - The orchestrator and deal engines must only consume the canonical `PlatformProduct` object. Platform adapters are responsible for mapping their raw JSON to this model.
3. **Deployment over Local Scripts**
   - Do not replace the containerized, deployable backend architecture with a developer-machine-only interactive browser workflow.
   - If Playwright/browser automation is required, it must be headless and capable of running entirely inside the Docker container.
4. **Graceful Failures**
   - If a platform is unserviceable at a location or encounters a WAF block, it must gracefully emit a `platform_unavailable` or `platform_error` event and allow the other platforms in the combined scan to finish successfully. A single platform failure must never crash the `AlertRunner`.

## Important Files & Services
- **`backend/app/domain/services/search_orchestrator.py`**: The core multi-platform coordinator.
- **`backend/app/domain/services/alert_runner.py`**: Executes jobs, manages parallel platform tasks, isolates exceptions, and aggregates events.
- **`backend/app/platforms/base.py`**: The `PlatformClient` interface contract that all platforms must fulfill.
- **`frontend/src/store/liveConsoleStore.ts`**: The SSE consumer that formats real-time logs for the UI.
- **`docker-compose.yml` & OS Launchers**: The definitive distribution method for the application.

## Known Limitations
- Quick-commerce APIs are highly volatile and rely on undocumented BFF (Backend-For-Frontend) routes.
- WAF (Web Application Firewall) blocks may occur during rapid polling.
- Store availability strictly depends on the exact latitude/longitude or pincode provided.

## Testing Strategy
- Core shared logic (`DealEngine`, `AlertEngine`, `StoreCache`) is heavily unit tested.
- `AlertRunner` and `DealSearchOrchestrator` regression suites verify location unserviceability handling.
- Use mocked `PlatformClient` implementations for shared architecture tests to avoid brittleness.
