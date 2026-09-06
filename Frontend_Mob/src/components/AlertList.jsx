import ThreatBadge from "./ThreatBadge";

const FILTERS = ["ALL", "HIGH", "UNCERTAIN", "LOW"];

function formatTime(ts) {
  const d = new Date(ts);
  if (isNaN(d)) return "—";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function StatusTag({ status }) {
  const label = {
    pending_verification: "Pending",
    confirmed_threat: "Confirmed",
    false_alarm: "False alarm",
  }[status] || status;
  return <span className="status-tag">{label}</span>;
}

export default function AlertList({ alerts, selectedId, onSelect, filter, onFilterChange }) {
  const filtered =
    filter === "ALL" ? alerts : alerts.filter((a) => a.threat_level === filter);

  return (
    <div className="alert-list">
      <div className="alert-list-filters">
        {FILTERS.map((f) => (
          <button
            key={f}
            className={`filter-chip ${filter === f ? "active" : ""}`}
            onClick={() => onFilterChange(f)}
          >
            {f === "ALL" ? "All" : f.charAt(0) + f.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      <div className="alert-list-scroll">
        {filtered.length === 0 && (
          <div className="alert-list-empty">No alerts in this category.</div>
        )}
        {filtered.map((alert) => (
          <button
            key={alert.id}
            className={`alert-card ${selectedId === alert.id ? "selected" : ""}`}
            onClick={() => onSelect(alert.id)}
          >
            <div className="alert-card-top">
              <ThreatBadge level={alert.threat_level} />
              <span className="mono alert-card-time">{formatTime(alert.timestamp)}</span>
            </div>
            <div className="alert-card-type">{alert.object_type || alert.reading_type || "Unclassified object"}</div>
            <div className="alert-card-meta mono">
              {alert.device_ids} · {alert.lat.toFixed(4)}, {alert.lng.toFixed(4)}
            </div>
            <StatusTag status={alert.status} />
          </button>
        ))}
      </div>
    </div>
  );
}
