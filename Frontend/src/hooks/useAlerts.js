import { useEffect, useRef, useState } from "react";
import { fetchAlerts, WS_URL } from "../api";

/**
 * useAlerts
 * ---------
 * Single source of truth for alert data, shared by the dashboard and
 * the RPF mobile screen. Loads the current list over REST, then patches
 * it live from the /ws/alerts WebSocket (new_alert / alert_updated).
 *
 * Reconnects automatically if the WebSocket drops, with backoff, so a
 * flaky demo network doesn't kill the live feed permanently.
 */
export function useAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const reconnectDelay = useRef(1000);

  useEffect(() => {
    let cancelled = false;

    fetchAlerts()
      .then((data) => {
        if (!cancelled) setAlerts(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    let ws;
    let reconnectTimer;

    function connect() {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        setConnected(true);
        setError(null);
        reconnectDelay.current = 1000;
      };

      ws.onmessage = (event) => {
        let msg;
        try {
          msg = JSON.parse(event.data);
        } catch {
          return;
        }

        if (msg.type === "new_alert") {
          setAlerts((prev) => [msg.alert, ...prev]);
        } else if (msg.type === "alert_updated") {
          setAlerts((prev) =>
            prev.map((a) => (a.id === msg.alert.id ? msg.alert : a))
          );
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (!cancelled) {
          reconnectTimer = setTimeout(connect, reconnectDelay.current);
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, 15000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, []);

  /** Apply a local optimistic update after a successful verify POST. */
  function applyLocalUpdate(alertId, patch) {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, ...patch } : a))
    );
  }

  return { alerts, connected, loading, error, applyLocalUpdate };
}
