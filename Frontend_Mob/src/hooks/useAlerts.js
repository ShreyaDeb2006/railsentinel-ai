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
 *
 * Two safeguards on top of the original version:
 *  - MAX_ALERTS caps how much history we keep in memory, so a long
 *    shift doesn't turn every WS update / render into an ever-growing
 *    array scan.
 *  - WS messages that arrive before the initial REST fetch resolves are
 *    buffered and merged in afterwards, instead of being silently
 *    clobbered by the REST response.
 */
const MAX_ALERTS = 500;

function applyPatch(list, msg) {
  if (msg.type === "new_alert") {
    return [msg.alert, ...list].slice(0, MAX_ALERTS);
  }
  if (msg.type === "alert_updated") {
    return list.map((a) => (a.id === msg.alert.id ? msg.alert : a));
  }
  return list;
}

export function useAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const reconnectDelay = useRef(1000);

  useEffect(() => {
    let cancelled = false;
    let initialLoadDone = false;
    const pendingMessages = [];

    fetchAlerts()
      .then((data) => {
        if (cancelled) return;
        // Fold in anything that arrived over the socket while we were
        // still waiting on the REST response, instead of dropping it.
        let merged = data.slice(0, MAX_ALERTS);
        for (const msg of pendingMessages) {
          merged = applyPatch(merged, msg);
        }
        setAlerts(merged);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) {
          initialLoadDone = true;
          setLoading(false);
        }
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

        if (!initialLoadDone) {
          // Hold onto it — the REST fetch above will merge this in once
          // it resolves, so we never lose an alert that arrived early.
          pendingMessages.push(msg);
          return;
        }

        setAlerts((prev) => applyPatch(prev, msg));
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
