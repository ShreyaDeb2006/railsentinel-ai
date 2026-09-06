import { useMemo, useState } from "react";
import { useAlerts } from "../hooks/useAlerts";
import { verifyAlert, submitHandheldReading } from "../api";
import ThreatBadge from "../components/ThreatBadge";

const LEVEL_ORDER = { HIGH: 0, UNCERTAIN: 1, LOW: 2 };

// /api/handheld-reading only carries a numeric reading_value, so the
// officer's LOW/UNCERTAIN/HIGH pick has to become a number before it's
// sent. These sit either side of fusion.py's single-sensor threshold
// (0.7) so LOW clears as "LOW" and UNCERTAIN/HIGH both clear as
// "UNCERTAIN" — the most severe outcome a lone reading can reach without
// a matching camera detection.
const THREAT_LEVEL_TO_READING_VALUE = { LOW: 0.2, UNCERTAIN: 0.75, HIGH: 0.95 };

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

  // Manual "Report Alert" modal state
  const [reportOpen, setReportOpen] = useState(false);
  const [reportForm, setReportForm] = useState({
    threatLevel: "UNCERTAIN",
    description: "",
    lat: "",
    lng: "",
    notes: "",
  });
  const [reportSubmitting, setReportSubmitting] = useState(false);
  const [reportError, setReportError] = useState(null);

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

  function updateReportField(field, value) {
    setReportForm((prev) => ({ ...prev, [field]: value }));
  }

  function openReportModal() {
    setReportError(null);
    setReportForm({
      threatLevel: "UNCERTAIN",
      description: "",
      lat: "",
      lng: "",
      notes: "",
    });
    setReportOpen(true);
  }

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setReportError("Location isn't available on this device.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        updateReportField("lat", pos.coords.latitude.toFixed(6));
        updateReportField("lng", pos.coords.longitude.toFixed(6));
      },
      () => setReportError("Couldn't get your location — enter it manually.")
    );
  }

  async function handleSubmitReport() {
    if (!officerId.trim()) {
      setReportError("Enter your officer ID at the top before reporting.");
      return;
    }
    if (!reportForm.description.trim()) {
      setReportError("Describe what you observed.");
      return;
    }
    const lat = parseFloat(reportForm.lat);
    const lng = parseFloat(reportForm.lng);
    if (Number.isNaN(lat) || Number.isNaN(lng)) {
      setReportError("Enter a valid GPS location, or tap \"Use current location\".");
      return;
    }

    setReportSubmitting(true);
    setReportError(null);
    try {
      const description = reportForm.description.trim();
      const notes = reportForm.notes.trim();
      await submitHandheldReading({
        deviceId: `rpf-${officerId.trim()}`,
        readingType: notes ? `${description} — ${notes}` : description,
        readingValue: THREAT_LEVEL_TO_READING_VALUE[reportForm.threatLevel],
        lat,
        lng,
      });
      setReportOpen(false);
    } catch (err) {
      setReportError(err.message);
    } finally {
      setReportSubmitting(false);
    }
  }

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
          <h1 className="rpf-detail-type">{openAlert.object_type || openAlert.reading_type || "Unclassified object"}</h1>
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
              <span className="rpf-list-item-type">{alert.object_type || alert.reading_type || "Unclassified object"}</span>
              <span className="rpf-list-item-meta mono">
                {formatTime(alert.timestamp)} · {alert.device_ids}
              </span>
            </div>
            <span className="rpf-chevron">›</span>
          </button>
        ))}
      </div>

      <button className="alert-fab" onClick={openReportModal} aria-label="Report Alert">
        ALERT
      </button>

      {reportOpen && (
        <div className="rpf-modal-overlay" onClick={() => !reportSubmitting && setReportOpen(false)}>
          <div className="rpf-modal" onClick={(e) => e.stopPropagation()}>
            <h2 className="rpf-modal-title">Report Alert</h2>

            <div className="rpf-form-field">
              <label>Threat level</label>
              <select
                value={reportForm.threatLevel}
                onChange={(e) => updateReportField("threatLevel", e.target.value)}
              >
                <option value="LOW">Low</option>
                <option value="UNCERTAIN">Uncertain</option>
                <option value="HIGH">High</option>
              </select>
            </div>

            <div className="rpf-form-field">
              <label>What did you observe?</label>
              <input
                value={reportForm.description}
                onChange={(e) => updateReportField("description", e.target.value)}
                placeholder="e.g. Unattended bag near Platform 3"
              />
            </div>

            <div className="rpf-gps-row">
              <div className="rpf-form-field">
                <label>Latitude</label>
                <input
                  value={reportForm.lat}
                  onChange={(e) => updateReportField("lat", e.target.value)}
                  placeholder="e.g. 27.4728"
                  inputMode="decimal"
                />
              </div>
              <div className="rpf-form-field">
                <label>Longitude</label>
                <input
                  value={reportForm.lng}
                  onChange={(e) => updateReportField("lng", e.target.value)}
                  placeholder="e.g. 94.9120"
                  inputMode="decimal"
                />
              </div>
            </div>
            <button className="rpf-btn locate" type="button" onClick={useCurrentLocation}>
              Use current location
            </button>

            <div className="rpf-form-field">
              <label>Notes (optional)</label>
              <textarea
                value={reportForm.notes}
                onChange={(e) => updateReportField("notes", e.target.value)}
                placeholder="Any extra detail worth passing along"
              />
            </div>

            {reportError && <div className="rpf-error">{reportError}</div>}

            <div className="rpf-modal-actions">
              <button
                className="rpf-btn confirm"
                disabled={reportSubmitting}
                onClick={handleSubmitReport}
              >
                {reportSubmitting ? "Sending…" : "Send report"}
              </button>
              <button
                className="rpf-btn cancel"
                disabled={reportSubmitting}
                onClick={() => setReportOpen(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
