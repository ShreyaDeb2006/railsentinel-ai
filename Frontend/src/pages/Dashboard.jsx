import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, AlertTriangle, HelpCircle, ShieldCheck, Maximize2, Minimize2 } from "lucide-react";
import { useAlertsContext } from "../context/AlertsContext";
import MapView from "../components/MapView";
import ThreatBadge from "../components/ThreatBadge";
import SummaryTile from "../components/SummaryTile";
import DonutChart from "../components/DonutChart";
import PlaceholderPanel from "../components/PlaceholderPanel";

function isToday(ts) {
  const d = new Date(ts);
  const now = new Date();
  return d.toDateString() === now.toDateString();
}

function formatTime(ts) {
  const d = new Date(ts);
  if (isNaN(d)) return "—";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function Dashboard() {
  const { alerts, loading, error } = useAlertsContext();
  const navigate = useNavigate();
  const [mapExpanded, setMapExpanded] = useState(false);

  // Let Escape collapse the enlarged map, same as clicking the backdrop.
  useEffect(() => {
    if (!mapExpanded) return;
    function onKeyDown(e) {
      if (e.key === "Escape") setMapExpanded(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mapExpanded]);

  const counts = {
    HIGH: alerts.filter((a) => a.threat_level === "HIGH").length,
    UNCERTAIN: alerts.filter((a) => a.threat_level === "UNCERTAIN").length,
    LOW: alerts.filter((a) => a.threat_level === "LOW").length,
  };

  const today = alerts.filter((a) => isToday(a.timestamp));
  const todayCounts = {
    high: today.filter((a) => a.threat_level === "HIGH").length,
    uncertain: today.filter((a) => a.threat_level === "UNCERTAIN").length,
    low: today.filter((a) => a.threat_level === "LOW").length,
  };

  const recent = [...alerts]
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .slice(0, 4);

  // Clicking a tile jumps to /alerts with that threat level pre-filtered.
  // "ALL" (the Total Alerts tile) goes to /alerts with no filter param,
  // which the Alerts page treats as its default "All" state.
  function goToAlerts(filterValue) {
    navigate(filterValue === "ALL" ? "/alerts" : `/alerts?filter=${filterValue}`);
  }

  return (
    <div className="dashboard-page">
      <div className="summary-row">
        <SummaryTile
          label="Total alerts"
          count={alerts.length}
          icon={<Bell size={18} />}
          tone="neutral"
          onClick={() => goToAlerts("ALL")}
        />
        <SummaryTile
          label="High risk"
          count={counts.HIGH}
          icon={<AlertTriangle size={18} />}
          tone="high"
          onClick={() => goToAlerts("HIGH")}
        />
        <SummaryTile
          label="Uncertain"
          count={counts.UNCERTAIN}
          icon={<HelpCircle size={18} />}
          tone="uncertain"
          onClick={() => goToAlerts("UNCERTAIN")}
        />
        <SummaryTile
          label="Low risk"
          count={counts.LOW}
          icon={<ShieldCheck size={18} />}
          tone="low"
          onClick={() => goToAlerts("LOW")}
        />
      </div>

      {error && <div className="dashboard-error">Couldn't reach the backend: {error}</div>}

      <div className="dashboard-grid-top">
        {mapExpanded && (
          <div className="map-panel-backdrop" onClick={() => setMapExpanded(false)} />
        )}
        <div className={`panel map-panel ${mapExpanded ? "map-panel-expanded" : ""}`}>
          <div className="panel-heading-row">
            <span className="panel-heading">Live threat map</span>
            <button
              className="icon-btn"
              onClick={() => setMapExpanded((v) => !v)}
              title={mapExpanded ? "Shrink map" : "Enlarge map"}
              aria-label={mapExpanded ? "Shrink map" : "Enlarge map"}
            >
              {mapExpanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
            </button>
          </div>
          <div className="map-panel-body">
            <MapView alerts={alerts} selectedId={null} onSelect={() => {}} expanded={mapExpanded} />
          </div>
        </div>

        <div className="panel recent-panel">
          <div className="panel-heading">Recent alerts</div>
          <div className="recent-list">
            {recent.length === 0 && <div className="alert-list-empty">No alerts yet.</div>}
            {recent.map((a) => (
              <div key={a.id} className="recent-item">
                <ThreatBadge level={a.threat_level} />
                <div className="recent-item-body">
                  <span className="recent-item-type">{a.object_type || a.reading_type || "Unclassified object"}</span>
                  <span className="recent-item-meta mono">{a.device_ids}</span>
                </div>
                <span className="recent-item-time mono">{formatTime(a.timestamp)}</span>
              </div>
            ))}
          </div>
          <button className="view-all-btn" onClick={() => goToAlerts("ALL")}>
            View all
          </button>
        </div>
      </div>

      <div className="dashboard-grid-bottom">
        <PlaceholderPanel
          title="Device status"
          note="Device health tracking isn't wired up yet — coming soon."
        />
        <div className="panel donut-panel">
          <div className="panel-heading">Threat assessment (today)</div>
          <DonutChart high={todayCounts.high} uncertain={todayCounts.uncertain} low={todayCounts.low} />
        </div>
      </div>

      {loading && <div className="dashboard-loading">Loading alerts…</div>}
    </div>
  );
}
