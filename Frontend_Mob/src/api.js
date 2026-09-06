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

/**
 * final_status should be "confirmed_threat" or "false_alarm"
 * (matches VerifyIn in schemas.py).
 */
export async function verifyAlert(alertId, verifiedBy, finalStatus) {
  const res = await fetch(`${API_BASE}/api/verify/${alertId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      verified_by: verifiedBy,
      final_status: finalStatus,
    }),
  });
  if (!res.ok) throw new Error(`Failed to verify alert: ${res.status}`);
  return res.json();
}
