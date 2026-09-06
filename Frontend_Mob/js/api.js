/**
 * api.js
 * ------
 * Talks to the FastAPI backend. Field names here match
 * backend/schemas.py and backend/main.py exactly — mirrors
 * Frontend_Mob/src/api.js so both apps hit the same contract.
 * If the backend's host/port or shape changes, this is the
 * only file that should need updating.
 */

export const API_BASE = "http://localhost:8000";
export const WS_URL = "ws://localhost:8000/ws/alerts";

export async function fetchAlerts() {
  const res = await fetch(`${API_BASE}/api/alerts`);
  if (!res.ok) throw new Error(`Failed to fetch alerts: ${res.status}`);
  return res.json();
}

/**
 * Officer-raised field report from the "ALERT!" button.
 *
 * There is no ManualAlertIn in schemas.py — the backend's HandheldReadingIn
 * only has device_id, reading_type, reading_value, gps: {lat, lng}. The
 * previous version of this function sent reading_value as the <select>'s
 * raw string value and also sent a "notes" field the backend doesn't
 * define, so the notes were silently dropped on every submission.
 *
 * reading_type is the only free-text field the backend accepts, so the
 * officer's description and notes are combined into it. reading_value is
 * coerced to a real number before sending.
 */
export async function submitHandheldReading({ readingValue, description, notes, deviceId, lat, lng }) {
  const res = await fetch(`${API_BASE}/api/handheld-reading`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      reading_value: Number(readingValue),
      reading_type: notes ? `${description} — ${notes}` : description,
      device_id: deviceId,
      gps: { lat, lng },
    }),
  });
  if (!res.ok) throw new Error(`Failed to submit alert: ${res.status}`);
  return res.json();
}
