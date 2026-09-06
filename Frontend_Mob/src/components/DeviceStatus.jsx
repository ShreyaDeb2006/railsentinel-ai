import { useEffect, useState } from "react";

/**
 * The backend doesn't expose a dedicated device-status endpoint yet
 * (see README.MD's endpoint table), so this derives "last seen" per
 * device directly from real alert data — no invented data, just a
 * different view onto what /api/alerts already gives us. Swap this
 * for a real endpoint later if Person 1 adds one.
 */
function timeAgo(ts) {
  const seconds = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.floor(minutes / 60)}h ago`;
}

export default function DeviceStatus({ alerts }) {
  // A device's "online" dot and "time ago" label are derived from
  // Date.now() at render time, but this component only re-renders when
  // `alerts` changes. Without a heartbeat, a device that goes silent
  // would show stale "online"/"Xs ago" forever until the next alert.
  const [, forceTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => forceTick((n) => n + 1), 15000);
    return () => clearInterval(id);
  }, []);

  const devices = new Map();

  for (const alert of alerts) {
    for (const id of (alert.device_ids || "").split(",").map((s) => s.trim()).filter(Boolean)) {
      const existing = devices.get(id);
      if (!existing || new Date(alert.timestamp) > new Date(existing.timestamp)) {
        devices.set(id, { id, timestamp: alert.timestamp });
      }
    }
  }

  const list = Array.from(devices.values()).sort((a, b) =>
    a.id.localeCompare(b.id)
  );

  return (
    <div className="device-status">
      <div className="panel-heading">Devices seen</div>
      {list.length === 0 && <div className="device-empty">No device activity yet.</div>}
      {list.map((d) => {
        const secondsAgo = (Date.now() - new Date(d.timestamp).getTime()) / 1000;
        const online = secondsAgo < 60;
        return (
          <div key={d.id} className="device-row">
            <span className={`device-dot ${online ? "online" : "offline"}`} />
            <span className="mono device-id">{d.id}</span>
            <span className="device-time mono">{timeAgo(d.timestamp)}</span>
          </div>
        );
      })}
    </div>
  );
}
