import { useState, useCallback, useEffect } from "react";
import type { AlertRule } from "../lib/types";
import { getAlerts, createAlert as apiCreateAlert, updateAlert as apiUpdateAlert, deleteAlert as apiDeleteAlert, runAlertNow as apiRunAlertNow } from "../lib/api";

export function useAlerts() {
  const [alerts, setAlerts] = useState<AlertRule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async (silent = false) => {
    if (!silent) setIsLoading(true);
    try {
      const data = await getAlerts();
      setAlerts(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      if (!silent) setIsLoading(false);
    }
  }, []);

  const [events, setEvents] = useState<any[]>([]);
  
  const fetchEvents = useCallback(async () => {
    try {
      const res = await fetch("/api/alerts/events");
      if (res.ok) {
        const data = await res.json();
        setEvents(data);
        return data;
      }
    } catch (err) {
      console.error("Failed to fetch events", err);
    }
    return null;
  }, []);

  const [, setSeenEventIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    // Initial fetch
    fetchAlerts();
    fetchEvents().then(events => {
      if (events) {
        setSeenEventIds(new Set(events.map((e: any) => e.id)));
      }
    });

    // 30s polling
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchAlerts(true);
        fetchEvents().then(latestEvents => {
          if (!latestEvents) return;
          
          setSeenEventIds(prevSeen => {
            const newSeen = new Set(prevSeen);
            let hasNew = false;
            
            for (const event of latestEvents) {
              if (!prevSeen.has(event.id)) {
                hasNew = true;
                newSeen.add(event.id);
                
                // Fire notification for new event
                if ("Notification" in window && Notification.permission === "granted") {
                  new Notification("Worth-It Deal Found", { 
                    body: `${event.product_name} — ₹${event.price}\n${event.discount_percent}% off`,
                  });
                }
              }
            }
            return hasNew ? newSeen : prevSeen;
          });
        });
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchAlerts, fetchEvents]);

  const createAlert = async (rule: Partial<AlertRule>) => {
    const newAlert = await apiCreateAlert(rule);
    setAlerts((prev) => [newAlert, ...prev]);
    return newAlert;
  };

  const toggleAlert = async (id: string, enabled: boolean) => {
    const updated = await apiUpdateAlert(id, enabled);
    setAlerts((prev) => prev.map((a) => (a.id === id ? updated : a)));
  };

  const deleteAlert = async (id: string) => {
    await apiDeleteAlert(id);
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  const runAlert = async (id: string) => {
    return await apiRunAlertNow(id);
  };

  return {
    alerts,
    events,
    isLoading,
    error,
    createAlert,
    toggleAlert,
    deleteAlert,
    runAlert,
    refreshAlerts: fetchAlerts,
    refreshEvents: fetchEvents,
  };
}
