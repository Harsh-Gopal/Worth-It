import { useSyncExternalStore } from "react";

export interface LogEvent {
  id: string;
  time: string;
  level: "INFO" | "WARN" | "ERROR" | "DEAL" | "FILTER";
  message: string;
  raw?: any;
}

class LiveConsoleStore {
  private logs: LogEvent[] = [];
  private listeners: Set<() => void> = new Set();
  private eventSource: EventSource | null = null;
  private currentUrl: string | null = null;
  private retryCount = 0;
  private reconnectTimeoutId: ReturnType<typeof setTimeout> | null = null;
  private readonly MAX_RETRIES = 5;
  private readonly INITIAL_BACKOFF_MS = 1000;

  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };

  private notify() {
    this.listeners.forEach((listener) => listener());
  }

  getLogs = () => {
    return this.logs;
  };

  addLog = (level: LogEvent["level"], message: string, raw?: any) => {
    const newLog = {
      id: Math.random().toString(36).substring(7),
      time: new Date().toLocaleTimeString([], { hour12: false }),
      level,
      message,
      raw,
    };
    this.logs = [...this.logs, newLog].slice(-1000); // Keep max 1000
    this.notify();
  };

  clearLogs = () => {
    this.logs = [];
    this.notify();
  };

  private triggerNotification(title: string, body: string) {
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(title, { body });
    }
  }

  connect = (url: string) => {
    if (this.currentUrl === url && this.eventSource) {
      return; // Already connected to this URL
    }

    this.disconnect();
    this.currentUrl = url;
    
    if (!this.logs.length) {
      this.addLog("INFO", "Connecting to live console stream...");
    }

    const es = new EventSource(url);
    this.eventSource = es;

    es.onopen = () => {
      this.retryCount = 0;
      this.addLog("INFO", "Connected to live event stream.");
    };

    es.addEventListener("search_started", (e) => {
      const data = JSON.parse(e.data);
      this.addLog("INFO", `Scan started. Type: ${data.type}`);
    });

    es.addEventListener("location_resolved", (e) => {
      const data = JSON.parse(e.data);
      this.addLog("INFO", `Location resolved -> Store: ${data.store_id}`);
    });

    es.addEventListener("store_search_started", (e) => {
      const data = JSON.parse(e.data);
      this.addLog("INFO", `Scanning store ${data.store_index}/${data.total_stores}`);
    });
    
    es.addEventListener("products_discovered", (e) => {
      const data = JSON.parse(e.data);
      this.addLog("INFO", `${data.count} products discovered from store.`);
    });
    
    es.addEventListener("filter_stats", (e) => {
      const data = JSON.parse(e.data);
      this.addLog("FILTER", `${data.total} total → ${data.category_matches} category matches → ${data.keyword_matches} keyword matches → ${data.deals} deals`);
    });

    es.addEventListener("deal_found", (e) => {
      const data = JSON.parse(e.data);
      const flat = data._flat || {};
      const name = data.product?.name || flat.product_name || "Unknown";
      const price = data.product?.price || flat.price || 0;
      const discount = flat.discount_percent || 0;
      this.addLog("DEAL", `${name} ₹${price} · ${discount}% OFF`, data);
      this.triggerNotification("Worth-It Deal Found", `${name} — ₹${price}\n${discount}% off`);
    });
    
    es.addEventListener("alert_persisted", (e) => {
       const data = JSON.parse(e.data);
       this.addLog("INFO", `Alert persisted: ${data.product_name} at ₹${data.price}`);
    });

    es.addEventListener("search_error", (e) => {
      const data = JSON.parse(e.data);
      this.addLog("ERROR", `Error during scan: ${data.message}`);
      es.close();
    });
    
    es.addEventListener("search_completed", (e) => {
      const data = JSON.parse(e.data);
      this.addLog("INFO", `Scan complete. Found ${data.total_deals || 0} deals. Triggered ${data.new_events || 0} new alerts.`);
      es.close();
    });
    
    es.addEventListener("search_cancelled", (e) => {
      const data = JSON.parse(e.data);
      this.addLog("INFO", `Scan cancelled: ${data.message}`);
      es.close();
    });

    es.addEventListener("watch_deleted", () => {
      this.addLog("WARN", "Watch deleted. Disconnecting stream.");
      this.disconnect();
    });

    es.onerror = () => {
      es.close();
      
      if (this.retryCount < this.MAX_RETRIES) {
        const backoff = this.INITIAL_BACKOFF_MS * Math.pow(2, this.retryCount);
        this.addLog("WARN", `Connection lost. Reconnecting in ${backoff / 1000}s...`);
        this.retryCount++;
        this.reconnectTimeoutId = setTimeout(() => this.connect(url), backoff);
      } else {
        this.addLog("ERROR", "Connection lost. Max retries exceeded.");
        this.disconnect();
      }
    };
  };

  disconnect = () => {
    if (this.reconnectTimeoutId) clearTimeout(this.reconnectTimeoutId);
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    this.currentUrl = null;
  };
}

export const liveConsoleStore = new LiveConsoleStore();

export function useLiveConsole() {
  const logs = useSyncExternalStore(
    liveConsoleStore.subscribe,
    liveConsoleStore.getLogs
  );
  return {
    logs,
    connect: liveConsoleStore.connect,
    disconnect: liveConsoleStore.disconnect,
    clearLogs: liveConsoleStore.clearLogs,
    addLog: liveConsoleStore.addLog,
  };
}
