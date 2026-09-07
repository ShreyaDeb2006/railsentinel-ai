import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAlertsContext } from "../context/AlertsContext";
import ThreatBadge from "../components/ThreatBadge";

const FILTERS = ["ALL", "HIGH", "UNCERTAIN", "LOW"];

function formatTime(ts) {
  const d = new Date(ts);
  if (isNaN(d)) return "—";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function dateLabel(ts) {
  const d = new Date(ts);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  if (d.toDateString() === today.toDateString()) return "Today";
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return d.toLocaleDateString([], { day: "numeric", month: "short", year: "numeric" });
}

function StatusTag({ status }) {
  const label =
    { pending_verification: "Pending", confirmed_threat: "Confirmed", false_alarm: "False alarm" }[
      status
    ] || status;
  return <span className="status-tag">{label}</span>;
}

export default function Alerts() {
  const { alerts } = useAlertsContext();
  const [searchParams, setSearchParams] = useSearchParams();
  const urlFilter = searchParams.get("filter");
  const [filter, setFilter] = useState(FILTERS.includes(urlFilter) ? urlFilter : "ALL");

  // Keeps the filter in sync if this page is reached via a dashboard tile
  // link (e.g. /alerts?filter=HIGH) after the page is already mounted.
  useEffect(() => {
    if (urlFilter && FILTERS.includes(urlFilter)) {
      setFilter(urlFilter);
    } else if (!urlFilter) {
      setFilter("ALL");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlFilter]);

  function changeFilter(next) {
    setFilter(next);
    setSearchParams(next === "ALL" ? {} : { filter: next });
  }

  const filtered = filter === "ALL" ? alerts : alerts.filter((a) => a.threat_level === filter);
  const sorted = [...filtered].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  const groups = [];
  for (const alert of sorted) {
    const label = dateLabel(alert.timestamp);
    let group = groups.find((g) => g.label === label);
    if (!group) {
      group = { label, items: [] };
      groups.push(group);
    }
    group.items.push(alert);
  }

  return (
    <div className="alerts-page">
      <div className="alerts-page-header">
        <h1>Alerts</h1>
        <div className="alert-list-filters">
          {FILTERS.map((f) => (
            <button
              key={f}
              className={`filter-chip ${filter === f ? "active" : ""}`}
              onClick={() => changeFilter(f)}
            >
              {f === "ALL" ? "All" : f.charAt(0) + f.slice(1).toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {groups.length === 0 && <div className="alert-list-empty">No alerts in this category.</div>}

      {groups.map((group) => (
        <div key={group.label} className="alert-date-group">
          <div className="alert-date-heading">{group.label}</div>
          <div className="alert-date-items">
            {group.items.map((alert) => (
              <div key={alert.id} className="alert-card wide">
                <div className="alert-card-top">
                  <ThreatBadge level={alert.threat_level} />
                  <span className="mono alert-card-time">{formatTime(alert.timestamp)}</span>
                </div>
                <div className="alert-card-type">{alert.object_type || alert.reading_type || "Unclassified object"}</div>
                <div className="alert-card-meta mono">
                  {alert.device_ids} · {alert.lat.toFixed(4)}, {alert.lng.toFixed(4)}
                </div>
                <StatusTag status={alert.status} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
