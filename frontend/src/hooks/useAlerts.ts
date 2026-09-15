import { useState, useCallback, useEffect } from "react";
import type { AlertRule } from "../lib/types";
import { getAlerts, createAlert as apiCreateAlert, updateAlert as apiUpdateAlert, deleteAlert as apiDeleteAlert, runAlertNow as apiRunAlertNow } from "../lib/api";

export function useAlerts() {
  const [alerts, setAlerts] = useState<AlertRule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getAlerts();
      setAlerts(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

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
    isLoading,
    error,
    createAlert,
    toggleAlert,
    deleteAlert,
    runAlert,
    refreshAlerts: fetchAlerts,
  };
}
