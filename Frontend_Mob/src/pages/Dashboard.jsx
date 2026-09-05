import { useMemo, useState } from "react";
import { useAlerts } from "../hooks/useAlerts";
import MapView from "../components/MapView";
import AlertList from "../components/AlertList";
import DeviceStatus from "../components/DeviceStatus";

export default function Dashboard() {
  const { alerts, connected, loading, error } = useAlerts();
  const [selectedId, setSelectedId] = useState(null);
  const [filter, setFilter] = useState("ALL");

  const counts = useMemo(() => {
    const c = { HIGH: 0, UNCERTAIN: 0, LOW: 0 };
    for (const a of alerts) {
      if (c[a.threat_level] !== undefined) c[a.threat_level]++;
    }
    return c;
  }, [alerts]);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="brand">
          <span className="brand-mark" />
          <span className="brand-name">RailSentinel AI</span>
          <span className="brand-sub">Control room</span>
        </div>

        <div className="header-counts">
          <span className="count-chip high">{counts.HIGH} high</span>
          <span className="count-chip uncertain">{counts.UNCERTAIN} uncertain</span>
          <span className="count-chip low">{counts.LOW} low</span>
        </div>

        <div className={`connection-indicator ${connected ? "live" : "offline"}`}>
          <span className="dot" />
          {connected ? "Live" : "Reconnecting…"}
        </div>
      </header>

      {error && <div className="dashboard-error">Couldn't reach the backend: {error}</div>}

      <div className="dashboard-body">
        <div className="map-pane">
          <MapView alerts={alerts} selectedId={selectedId} onSelect={setSelectedId} />
        </div>

        <div className="side-pane">
          <AlertList
            alerts={alerts}
            selectedId={selectedId}
            onSelect={setSelectedId}
            filter={filter}
            onFilterChange={setFilter}
          />
          <DeviceStatus alerts={alerts} />
        </div>
      </div>

      {loading && <div className="dashboard-loading">Loading alerts…</div>}
    </div>
  );
}
