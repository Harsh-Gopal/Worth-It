# Search Flow

This document details the exact lifecycle of a Deal Search, highlighting how a keyword search transitions into precise geographic product discovery.

## The Two-Stage Strategy

The flow is designed to minimize expensive keyword searches and API calls to Instamart, prioritizing local results before expanding outward.

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant Instamart Client
    participant Matcher
    participant Geo Engine
    participant Deal Engine

    User->>Orchestrator: Search("Nutrabay protein", Min Discount 50%, Radius 10km)
    
    %% Stage 1: Local Search
    Note over Orchestrator, Instamart Client: STAGE 1: LOCAL SEARCH
    Orchestrator->>Instamart Client: Resolve User Location (lat/lng) -> storeId
    Instamart Client-->>Orchestrator: local_storeId
    
    Orchestrator->>Instamart Client: Keyword Search("Nutrabay protein", store=local_storeId)
    Instamart Client-->>Orchestrator: Paginated Results (Products)
    
    Orchestrator->>Matcher: Filter & Normalize Candidates
    Matcher-->>Orchestrator: Target Canonical Product IDs (e.g., ID_A, ID_B)
    
    Orchestrator->>Deal Engine: Evaluate Target Products (local_storeId)
    Deal Engine-->>Orchestrator: Deal Results
    
    alt Qualifying Deal Found Locally
        Orchestrator->>User: Stream Result (SSE: deal_found)
        Orchestrator->>User: Stream Result (SSE: search_completed)
        Note over Orchestrator: STOP EXECUTION EARLY
    end

    %% Stage 2: Geographic Expansion
    Note over Orchestrator, Geo Engine: STAGE 2: GEOGRAPHIC EXPANSION
    
    loop For radius in [3km, 5km, 10km]
        Orchestrator->>User: Stream Result (SSE: radius_expanded, radius)
        
        Orchestrator->>Geo Engine: Get Stores in Radius
        Geo Engine->>Geo Engine: Check Store Cache
        Geo Engine->>Instamart Client: Probe unknown hex grid coordinates
        Geo Engine-->>Orchestrator: List of Store IDs (storeId_X, storeId_Y)
        
        loop For each Store ID
            Note over Orchestrator, Instamart Client: EXACT LOOKUP, NOT KEYWORD SEARCH
            Orchestrator->>Instamart Client: Fetch exact Product IDs (ID_A, ID_B) at storeId_X
            Instamart Client-->>Orchestrator: Product Availability & Price
            
            Orchestrator->>Deal Engine: Evaluate Deal Conditions
            Deal Engine-->>Orchestrator: Deal Result
            
            alt Qualifying Deal Found
                Orchestrator->>User: Stream Result (SSE: deal_found, best deal)
            end
        end
        
        alt Deal Found in this Radius Tier
            Note over Orchestrator: STOP EXECUTION. Do not expand to next radius.
            break
        end
    end
    
    Orchestrator->>User: Stream Result (SSE: search_completed)
```

## Key Optimization: The "Bridge"

The transition between Stage 1 and Stage 2 contains the most important optimization in the system:

1. **Keyword Discovery**: The system *must* do a broad, paginated keyword search at the first location to figure out what "Nutrabay protein" actually maps to in Instamart's database (e.g., Product ID `12345` for 1kg Chocolate, `67890` for 2kg Vanilla).
2. **Exact Target Lock-on**: Once `12345` and `67890` are identified as valid matches by the `ProductMatcher`, the broad keyword string is discarded.
3. **Targeted Geographic Checks**: When sweeping a 10km radius involving 15 dark stores, the system does **not** search "Nutrabay protein" 15 times. It explicitly checks stock for IDs `12345` and `67890` at those 15 stores. This is orders of magnitude faster, avoids pagination logic on geographic sweeps, and reduces WAF blocking risk.

## Cancellation

At any point during the loop, if the user disconnects, the SSE stream will throw an exception. The Orchestrator intercepts this, cancels all `asyncio.Task` execution, and gracefully terminates the geographic probe to save resources.
