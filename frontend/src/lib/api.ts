import type { AlertRule, AlertEvent, PriceObservation } from "./types";

const API_BASE = "/api";

export const api = {
  get: async (endpoint: string) => {
    const res = await fetch(`${API_BASE}${endpoint}`);
    if (!res.ok) {
      let err;
      try { err = await res.json(); } catch(e) {}
      throw new Error(err?.detail || err?.message || `Error ${res.status}`);
    }
    return res.json();
  },
  post: async (endpoint: string, data: any) => {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      let err;
      try { err = await res.json(); } catch(e) {}
      throw new Error(err?.detail || err?.message || `Error ${res.status}`);
    }
    return res.json();
  },
  delete: async (endpoint: string) => {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "DELETE"
    });
    if (!res.ok) {
      let err;
      try { err = await res.json(); } catch(e) {}
      throw new Error(err?.detail || err?.message || `Error ${res.status}`);
    }
    return res.json();
  }
};
export const getAlerts = async (): Promise<AlertRule[]> => {
  const res = await fetch(`${API_BASE}/alerts`);
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
};

export const createAlert = async (rule: Partial<AlertRule>): Promise<AlertRule> => {
  const res = await fetch(`${API_BASE}/alerts/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rule),
  });
  if (!res.ok) throw new Error("Failed to create alert");
  return res.json();
};

export const updateAlert = async (id: string, enabled: boolean): Promise<AlertRule> => {
  const res = await fetch(`${API_BASE}/alerts/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!res.ok) throw new Error("Failed to update alert");
  return res.json();
};

export const deleteAlert = async (id: string): Promise<void> => {
  const res = await fetch(`${API_BASE}/alerts/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete alert");
};

export const runAlertNow = async (id: string): Promise<AlertEvent[]> => {
  const res = await fetch(`${API_BASE}/alerts/${id}/run`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to run alert");
  return res.json();
};

export const getPriceHistory = async (instamartProductId: string): Promise<PriceObservation[]> => {
  const res = await fetch(`${API_BASE}/history/${instamartProductId}`);
  if (!res.ok) throw new Error("Failed to fetch price history");
  return res.json();
};
