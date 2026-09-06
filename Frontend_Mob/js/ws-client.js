/**
 * ws-client.js
 * ------------
 * Wraps the /ws/alerts WebSocket: connects, auto-reconnects on drop,
 * and forwards "new_alert" / "alert_updated" frames to a callback.
 * Doesn't know about the DOM or app state — just plumbing.
 */
import { WS_URL } from "./api.js";

/**
 * @param {(alert: object) => void} onAlert - called with the alert
 *   payload whenever a new_alert or alert_updated frame arrives.
 * @param {(isLive: boolean) => void} onConnectionChange - called
 *   whenever the socket opens or closes.
 */
export function connectAlertsSocket(onAlert, onConnectionChange) {
  let ws;

  function connect() {
    try {
      ws = new WebSocket(WS_URL);
    } catch (err) {
      onConnectionChange(false);
      return;
    }

    ws.onopen = () => onConnectionChange(true);

    ws.onclose = () => {
      onConnectionChange(false);
      setTimeout(connect, 3000); // auto-reconnect
    };

    ws.onerror = () => onConnectionChange(false);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if ((msg.type === "new_alert" || msg.type === "alert_updated") && msg.alert) {
          onAlert(msg.alert);
        }
      } catch (err) {
        /* ignore malformed frames */
      }
    };
  }

  connect();
}
