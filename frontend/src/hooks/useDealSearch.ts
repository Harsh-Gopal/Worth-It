import { useState, useRef, useCallback } from "react";
import type { SearchRequest, SearchEvent, SearchEventType, DealResult, Store } from "../lib/types";

export type SearchStatus = 
  | "IDLE" 
  | "STARTING" 
  | "LOCAL_SEARCH" 
  | "EXPANDING_RADIUS" 
  | "SCANNING_STORES" 
  | "DEAL_FOUND" 
  | "COMPLETED" 
  | "WAITING_FOR_NEXT_SCAN"
  | "CANCELLED" 
  | "ERROR";

export interface SearchMetrics {
  storesDiscovered: number;
  storesScanned: number;
  productsFound: number;
  dealsFound: number;
  currentRadiusKm: number;
  elapsedTimeMs?: number;
}

export interface UseDealSearchOptions {
  isContinuous?: boolean;
  continuousIntervalMs?: number;
}

export function useDealSearch({ isContinuous = true, continuousIntervalMs = 60000 }: UseDealSearchOptions = {}) {
  const [status, setStatus] = useState<SearchStatus>("IDLE");
  const [events, setEvents] = useState<SearchEvent[]>([]);
  const [stores, setStores] = useState<Record<string, Store>>({});
  const [deals, setDeals] = useState<DealResult[]>([]);
  const [metrics, setMetrics] = useState<SearchMetrics>({
    storesDiscovered: 0,
    storesScanned: 0,
    productsFound: 0,
    dealsFound: 0,
    currentRadiusKm: 0,
  });
  const [error, setError] = useState<string | null>(null);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const currentRequestRef = useRef<SearchRequest | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const startSearch = useCallback((request: SearchRequest, isRestart = false) => {
    // Cleanup previous
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    currentRequestRef.current = request;
    
    setStatus("STARTING");
    if (!isRestart) {
      setEvents([]);
      setStores({});
      setDeals([]);
      setMetrics({
        storesDiscovered: 0,
        storesScanned: 0,
        productsFound: 0,
        dealsFound: 0,
        currentRadiusKm: 0,
      });
    }
    setError(null);

    // Build query params
    const params = new URLSearchParams();
    
    if (request.categories?.length > 0) params.append("categories", request.categories.join(","));
    if (request.keywords?.length > 0) params.append("keywords", request.keywords.join(","));
    if (request.exclude_keywords?.length > 0) params.append("exclude_keywords", request.exclude_keywords.join(","));
    
    if (request.min_discount_pct) params.append("min_discount_pct", request.min_discount_pct.toString());
    if (request.max_price) params.append("max_price", request.max_price.toString());
    if (request.min_price_drop_pct) params.append("min_price_drop_pct", request.min_price_drop_pct.toString());
    params.append("require_historical_low", request.require_historical_low ? "true" : "false");
    params.append("condition_operator", request.condition_operator || "AND");
    if (request.radius_km) params.append("radius_km", request.radius_km.toString());
    if (request.expansion_strategy) params.append("expansion_strategy", request.expansion_strategy);
    
    if (request.product_urls && request.product_urls.length > 0) {
      params.append("product_urls", request.product_urls.join(","));
    }
    
    // Add location parameters if present
    const anyReq = request as any;
    if (anyReq.lat) params.append("lat", anyReq.lat.toString());
    if (anyReq.lng) params.append("lng", anyReq.lng.toString());
    if (anyReq.local_store_id) params.append("local_store_id", anyReq.local_store_id);

    const endpoint = `/api/search/stream?${params.toString()}`;

    const es = new EventSource(endpoint);
    eventSourceRef.current = es;

    const handleEvent = (eventType: string, e: MessageEvent) => {
      try {
        const payload = e.data ? JSON.parse(e.data) : {};
        setEvents((prev) => [...prev, { event: eventType as SearchEventType, data: payload }]);

        switch (eventType) {
          case "search_started":
            setStatus("STARTING");
            break;
          case "local_search_started":
            setStatus("LOCAL_SEARCH");
            break;
          case "radius_expansion_started":
            setStatus("EXPANDING_RADIUS");
            if (payload.radii && payload.radii.length > 0) {
              setMetrics((m) => ({ ...m, currentRadiusKm: payload.radii[0] }));
            }
            break;
          case "radius_scan_started":
            setStatus("EXPANDING_RADIUS");
            setMetrics((m) => ({ ...m, currentRadiusKm: payload.radius_km }));
            break;
          case "store_scan_started":
            setStatus("SCANNING_STORES");
            break;
          case "store_discovered":
            setStores((prev) => ({ ...prev, [payload.store_id]: payload }));
            setMetrics((m) => ({ ...m, storesDiscovered: m.storesDiscovered + 1 }));
            break;
          case "store_scan_completed":
          case "product_check_completed":
            setMetrics((m) => ({ ...m, storesScanned: m.storesScanned + 1 }));
            break;
          case "product_discovered":
            setMetrics((m) => ({ ...m, productsFound: m.productsFound + 1 }));
            break;
          case "deal_found":
            setStatus("DEAL_FOUND");
            setDeals((prev) => {
              // Deduplicate deals by product ID + store ID to prevent UI flashing
              const existingIndex = prev.findIndex(
                (d) => d.product.external_product_id === payload.product.external_product_id && d.store.id === payload.store.id
              );
              if (existingIndex >= 0) {
                return prev;
              }
              
              // Try firing browser notification for truly new deals
              try {
                if (window.Notification && Notification.permission === "granted") {
                  new Notification(`Deal Found: ${payload.product.name}`, {
                    body: `₹${payload.product.price} (${payload.discount_percent}% OFF) at ${payload.store.name || payload.store.id}`,
                    icon: payload.product.image_url || undefined,
                  });
                }
              } catch (e) {
                console.error("Browser notification failed", e);
              }
              
              return [...prev, payload];
            });
            setMetrics((m) => ({ ...m, dealsFound: m.dealsFound + 1 }));
            break;
          case "search_completed":
            if (payload.total_deals !== undefined) {
              setMetrics((m) => ({ ...m, dealsFound: payload.total_deals }));
            }
            es.close();
            
            if (isContinuous && currentRequestRef.current) {
              setStatus("WAITING_FOR_NEXT_SCAN");
              timeoutRef.current = setTimeout(() => {
                if (currentRequestRef.current) {
                  startSearch(currentRequestRef.current, true);
                }
              }, continuousIntervalMs);
            } else {
              setStatus("COMPLETED");
            }
            break;
          case "search_cancelled":
            setStatus("CANCELLED");
            es.close();
            break;
          case "search_error":
            setStatus("ERROR");
            setError(payload.message || "An unknown error occurred.");
            es.close();
            break;
        }
      } catch (err) {
        console.error(`Failed to parse SSE message for event ${eventType}`, err);
      }
    };

    const eventTypes = [
      "search_started", "local_search_started", "radius_expansion_started",
      "radius_scan_started", "store_scan_started", "store_discovered",
      "store_scan_completed", "product_check_completed", "product_discovered",
      "deal_found", "search_completed", "search_cancelled", "search_error",
      "probe_started", "probe_completed", "product_check_started"
    ];

    eventTypes.forEach(type => {
      es.addEventListener(type, (e) => handleEvent(type, e));
    });

    es.onerror = () => {
      // SSE auto-reconnects, but if we want to stop on error:
      setStatus("ERROR");
      setError("Connection to server lost.");
      es.close();
    };

  }, []);

  const cancelSearch = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      setStatus("CANCELLED");
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    currentRequestRef.current = null;
  }, []);

  return {
    startSearch,
    cancelSearch,
    status,
    events,
    stores,
    deals,
    metrics,
    error,
  };
}
