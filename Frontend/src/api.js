/**
 * api.js
 * ------
 * Talks to Person 1's FastAPI backend. Field names here match
 * schemas.py / main.py exactly — if the backend contract changes,
 * this is the only file that should need updating.
 */

export const API_BASE = "http://localhost:8000";
export const WS_URL = "ws://localhost:8000/ws/alerts";

export async function fetchAlerts() {
  const res = await fetch(`${API_BASE}/api/alerts`);
  if (!res.ok) throw new Error(`Failed to fetch alerts: ${res.status}`);
  return res.json();
}
