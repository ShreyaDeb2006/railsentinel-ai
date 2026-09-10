/**
 * alerts-view.js
 * --------------
 * Everything for the "Alert Notifications" screen: holding the
 * current list + filter, fetching from the backend, merging in
 * live WebSocket updates, and rendering the cards.
 */
import { fetchAlerts as apiFetchAlerts, verifyAlert } from "./api.js";
import { formatTime, statusLabel, threatLabel, escapeHtml } from "./format.js";

let alerts = [];
let currentFilter = "ALL";

// Alert ids currently mid-verify (button disabled + spinner text)
// and any per-alert error message from a failed verify attempt.
const verifyingIds = new Set();
const verifyErrors = new Map();

const listEl = document.getElementById("alertList");
const filterChips = document.querySelectorAll(".filter-chip");

filterChips.forEach((chip) => {
  chip.addEventListener("click", () => setFilter(chip.dataset.filter));
});

// One delegated listener handles every card's Confirm/False alarm
// button, including ones added after a later re-render — no need to
// re-attach a handler per card each time the list redraws.
listEl.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-verify]");
  if (!btn) return;
  handleVerify(Number(btn.dataset.id), btn.dataset.verify);
});

function setFilter(filter) {
  currentFilter = filter;
  filterChips.forEach((chip) => chip.classList.toggle("active", chip.dataset.filter === filter));
  render();
}

async function handleVerify(alertId, finalStatus) {
  const officerId = (localStorage.getItem("rpf_officer_id") || "").trim();
  if (!officerId) {
    verifyErrors.set(alertId, 'Enter your Officer ID on the "Add Alert" screen first.');
    render();
    return;
  }

  verifyingIds.add(alertId);
  verifyErrors.delete(alertId);
  render();

  try {
    await verifyAlert(alertId, officerId, finalStatus);
    // Optimistic local update — the /ws/alerts "alert_updated" frame
    // will also arrive and apply the same change via upsertAlert,
    // this just avoids a visible delay waiting on the round-trip.
    const idx = alerts.findIndex((a) => a.id === alertId);
    if (idx !== -1) {
      alerts[idx] = { ...alerts[idx], status: finalStatus, verified_by: officerId };
    }
  } catch (err) {
    verifyErrors.set(alertId, err.message);
  } finally {
    verifyingIds.delete(alertId);
    render();
  }
}

function render() {
  const filtered = currentFilter === "ALL" ? alerts : alerts.filter((a) => a.threat_level === currentFilter);
  const sorted = [...filtered].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  if (sorted.length === 0) {
    listEl.innerHTML = `<div class="empty-state">No alerts in this category.</div>`;
    return;
  }

  listEl.innerHTML = sorted
    .map((a) => {
      const level = (a.threat_level || "").toLowerCase();
      const pending = a.status === "pending_verification";
      const isVerifying = verifyingIds.has(a.id);
      const error = verifyErrors.get(a.id);

      return `
        <div class="alert-card">
          <div class="alert-card-top">
            <span class="threat-pill ${level}">${threatLabel(a.threat_level)}</span>
            <span class="alert-card-time mono">${formatTime(a.timestamp)}</span>
          </div>
          <div class="alert-card-type">${escapeHtml(a.object_type || a.reading_type || "Unclassified object")}</div>
          <div class="alert-card-meta mono">${escapeHtml(a.device_ids || "—")} · ${a.lat.toFixed(4)}, ${a.lng.toFixed(4)}</div>
          <span class="status-tag">${statusLabel(a.status)}${a.verified_by ? ` · ${escapeHtml(a.verified_by)}` : ""}</span>
          ${error ? `<div class="inline-msg error">${escapeHtml(error)}</div>` : ""}
          ${
            pending
              ? `
            <div class="alert-actions">
              <button class="verify-btn confirm" data-verify="confirmed_threat" data-id="${a.id}" ${isVerifying ? "disabled" : ""}>
                ${isVerifying ? "Sending…" : "Confirm threat"}
              </button>
              <button class="verify-btn dismiss" data-verify="false_alarm" data-id="${a.id}" ${isVerifying ? "disabled" : ""}>
                ${isVerifying ? "Sending…" : "False alarm"}
              </button>
            </div>`
              : ""
          }
        </div>
      `;
    })
    .join("");
}

export async function loadAlerts() {
  try {
    alerts = await apiFetchAlerts();
    render();
  } catch (err) {
    listEl.innerHTML = `<div class="empty-state">Couldn't reach the backend.<br>${escapeHtml(err.message)}</div>`;
  }
}

/** Called by ws-client.js when a new_alert / alert_updated frame arrives. */
export function upsertAlert(incoming) {
  const idx = alerts.findIndex((a) => a.id === incoming.id);
  if (idx === -1) alerts.push(incoming);
  else alerts[idx] = incoming;
  render();
}
