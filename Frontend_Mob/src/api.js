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

/**
 * Officer-raised field report from the RPF app's ALERT button.
 *
 * There is no "manual alert" route on the backend — main.py only exposes
 * /api/camera-detection, /api/handheld-reading, /api/alerts,
 * /api/verify/{id}, and /ws/alerts, and schemas.py has no ManualAlertIn.
 * The old submitManualAlert() here posted to a /api/manual-alert route
 * that never existed, so the button always failed. This submits the
 * officer's report through the real /api/handheld-reading route instead,
 * matching HandheldReadingIn in schemas.py exactly: device_id,
 * reading_type, reading_value, gps: {lat, lng}.
 *
 * reading_type is a free-text field on the backend, so the officer's
 * observation text is carried there. reading_value is a numeric stand-in
 * for the chosen threat level (see THREAT_LEVEL_TO_READING_VALUE in
 * RPFMobile.jsx) — fusion.py's classify() only ever returns "UNCERTAIN" or
 * "LOW" for a lone, unpaired reading, so an officer report can't come out
 * as "HIGH" on its own; it still goes through the same fusion/alert
 * pipeline as a real handheld device.
 */
export async function submitHandheldReading({ deviceId, readingType, readingValue, lat, lng }) {
  const res = await fetch(`${API_BASE}/api/handheld-reading`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      device_id: deviceId,
      reading_type: readingType,
      reading_value: readingValue,
      gps: { lat, lng },
    }),
  });
  if (!res.ok) throw new Error(`Failed to submit reading: ${res.status}`);
  return res.json();
}
