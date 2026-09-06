import { useMemo, useState } from "react";
import { useAlerts } from "../hooks/useAlerts";
import { verifyAlert } from "../api";
import ThreatBadge from "../components/ThreatBadge";

const LEVEL_ORDER = { HIGH: 0, UNCERTAIN: 1, LOW: 2 };

function formatTime(ts) {
  const d = new Date(ts);
  if (isNaN(d)) return "—";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function RPFMobile() {
  const { alerts, connected, applyLocalUpdate } = useAlerts();
  const [officerId, setOfficerId] = useState(
    () => localStorage.getItem("rpf_officer_id") || ""
  );
  const [openAlertId, setOpenAlertId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [actionError, setActionError] = useState(null);

  function saveOfficerId(value) {
    setOfficerId(value);
    localStorage.setItem("rpf_officer_id", value);
  }

  const pending = useMemo(
    () =>
      alerts
        .filter((a) => a.status === "pending_verification")
        .sort((a, b) => {
          const levelDiff = LEVEL_ORDER[a.threat_level] - LEVEL_ORDER[b.threat_level];
          if (levelDiff !== 0) return levelDiff;
          return new Date(b.timestamp) - new Date(a.timestamp);
        }),
    [alerts]
  );

  const openAlert = alerts.find((a) => a.id === openAlertId) || null;

  async function handleVerify(alertId, finalStatus) {
    if (!officerId.trim()) {
      setActionError("Enter your officer ID before verifying.");
      return;
    }
    setSubmitting(true);
    setActionError(null);
    try {
      await verifyAlert(alertId, officerId.trim(), finalStatus);
      applyLocalUpdate(alertId, { status: finalStatus, verified_by: officerId.trim() });
      setOpenAlertId(null);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (openAlert) {
    return (
      <div className="rpf-app">
        <header className="rpf-detail-header">
          <button className="rpf-back" onClick={() => setOpenAlertId(null)}>
            ← Back
          </button>
          <span className={`connection-dot ${connected ? "live" : "offline"}`} />
        </header>

        <div className="rpf-detail-body">
          <ThreatBadge level={openAlert.threat_level} />
          <h1 className="rpf-detail-type">{openAlert.object_type || "Unclassified object"}</h1>
          <div className="rpf-detail-time mono">{formatTime(openAlert.timestamp)}</div>

          <div className="rpf-detail-grid">
            <div className="rpf-detail-field">
              <span className="rpf-field-label">Devices</span>
              <span className="mono">{openAlert.device_ids}</span>
            </div>
            <div className="rpf-detail-field">
              <span className="rpf-field-label">Location</span>
              <span className="mono">
                {openAlert.lat.toFixed(5)}, {openAlert.lng.toFixed(5)}
              </span>
            </div>
            {openAlert.camera_confidence != null && (
              <div className="rpf-detail-field">
                <span className="rpf-field-label">Camera confidence</span>
                <span className="mono">{(openAlert.camera_confidence * 100).toFixed(0)}%</span>
              </div>
            )}
            {openAlert.handheld_reading != null && (
              <div className="rpf-detail-field">
                <span className="rpf-field-label">Handheld reading</span>
                <span className="mono">{openAlert.handheld_reading.toFixed(2)}</span>
              </div>
            )}
          </div>

          <a
            className="rpf-map-link"
            href={`https://www.openstreetmap.org/?mlat=${openAlert.lat}&mlon=${openAlert.lng}#map=17/${openAlert.lat}/${openAlert.lng}`}
            target="_blank"
            rel="noreferrer"
          >
            Open location in maps →
          </a>
        </div>

        {actionError && <div className="rpf-error">{actionError}</div>}

        <div className="rpf-action-bar">
          <button
            className="rpf-btn confirm"
            disabled={submitting}
            onClick={() => handleVerify(openAlert.id, "confirmed_threat")}
          >
            Confirm threat
          </button>
          <button
            className="rpf-btn dismiss"
            disabled={submitting}
            onClick={() => handleVerify(openAlert.id, "false_alarm")}
          >
            False alarm
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rpf-app">
      <header className="rpf-header">
        <span className="rpf-title">RailSentinel — RPF</span>
        <span className={`connection-dot ${connected ? "live" : "offline"}`} />
      </header>

      <div className="rpf-officer-row">
        <label className="rpf-officer-label">Officer ID</label>
        <input
          className="rpf-officer-input"
          value={officerId}
          onChange={(e) => saveOfficerId(e.target.value)}
          placeholder="e.g. RPF-2214"
        />
      </div>

      <div className="rpf-list">
        {pending.length === 0 && (
          <div className="rpf-empty">No alerts waiting on verification.</div>
        )}
        {pending.map((alert) => (
          <button
            key={alert.id}
            className="rpf-list-item"
            onClick={() => setOpenAlertId(alert.id)}
          >
            <ThreatBadge level={alert.threat_level} />
            <div className="rpf-list-item-body">
              <span className="rpf-list-item-type">{alert.object_type || "Unclassified object"}</span>
              <span className="rpf-list-item-meta mono">
                {formatTime(alert.timestamp)} · {alert.device_ids}
              </span>
            </div>
            <span className="rpf-chevron">›</span>
          </button>
        ))}
      </div>
    </div>
  );
}
