# Phase 5: Price History, Deal Intelligence & Alert Engine

## Overview

Phase 5 introduces persistent alerting, historical price intelligence, and background execution to `instamart-deal-radar`. The core focus was to evolve the stateless geographic search into a persistent monitor that can detect intelligent price drops, historical lows, and execute notification workflows (like Telegram).

### Key Components

1. **Price History Service**
   - **`PriceHistoryRepository`**: Uses SQLite (WAL mode) to store individual `PriceObservation` records for every product encountered at any store.
   - **`PriceHistoryService`**: Records observations and dynamically computes context such as `previous_price`, `price_drop_percent`, and `historical_low_before_now`.
   - **Integration**: Injected into `DealSearchOrchestrator`. During both local search and geographic expansion, as products are discovered, their prices are recorded and historical context is injected into the evaluation step.

2. **Enhanced Deal Engine**
   - **Composite Logic**: `DealCondition` now supports `AND` / `OR` conditional operators.
   - **History-Aware**: `DealEngine` was extended to accept `history_context` and evaluate `price_drop_pct` and `require_historical_low` conditions.
   - **Ranking Strategy**: A dedicated `DealRanker` with an explicit `DealRankingStrategy` Enum (e.g., `BEST_DISCOUNT`, `NEAREST`, `LOWEST_PRICE`, `LARGEST_PRICE_DROP`) sorts the qualified deals.

3. **Alert Domain & Storage**
   - **`AlertRule`**: Represents a user's persistent alert configuration, including thresholds (min discount, price drops) and execution constraints (radius, expansion strategy).
   - **`AlertEvent`**: Represents a generated notification event. It stores the exact state of the deal that triggered the alert.
   - **`AlertRepository`**: A robust SQLite repository handling the persistence of both rules and events, tracking cooldown periods and preventing duplication.

4. **Alert Engine (Deduplication & Cooldowns)**
   - **`AlertEngine`**: Sits between the search orchestrator and the notification provider. 
   - **Store-Aware Deduplication**: It deduplicates identical deals using a composite key of `(alert_rule_id, instamart_product_id, store_id)`.
   - **Better-Deal Override**: If a deal is found inside a cooldown window, it checks if the deal has *improved* (e.g., price dropped further or discount increased). If so, it overrides the cooldown and triggers immediately.

5. **Notification Provider**
   - **`NotificationProvider` Interface**: An async protocol defining `send_alert(event) -> NotificationResult`.
   - **`TelegramNotificationProvider`**: Native integration to send rich markdown messages with pricing context, strikethrough MRP, trigger reasons, and clickable deep-links to Swiggy Instamart.

6. **Execution Pipeline (`AlertRunner`)**
   - **End-to-End Orchestration**: Converts an `AlertRule` into a `DealCondition`, invokes the `DealSearchOrchestrator`, collects and ranks the resulting deals, runs them through the `AlertEngine` for deduplication, saves generated `AlertEvents`, and coordinates the `NotificationService`.

### Testing

Comprehensive unit and integration testing was added:
- **`test_price_history.py`**: Validates the correct computation of `price_drop_percent` and `historical_low` based on chronological observations.
- **`test_deal_engine_extended.py`**: Ensures that logical `AND/OR` operations combined with historical conditions operate flawlessly.
- **`test_alert_engine.py`**: Tests deduplication logic, verifying that identical deals are ignored, superior deals bypass cooldowns, and store-isolation works.
- **`test_alert_e2e.py`**: A fully mocked pipeline running `AlertRunner` testing the entire database, evaluation, engine, and mocked notification layer.

## Future Phases

With Phase 5 complete, the backend is extremely robust, fully covered by tests, and capable of geographic deal discovery, historical intelligence, and persistent alerting.
The next natural step is to begin development of the **React/TypeScript Frontend** to allow users to create and manage these alerts visually.
