/**
 * alerts-view.js
 * --------------
 * Everything for the "Alert Notifications" screen: holding the
 * current list + filter, fetching from the backend, merging in
 * live WebSocket updates, and rendering the cards.
 */
import { fetchAlerts as apiFetchAlerts } from "./api.js";
import { formatTime, statusLabel, threatLabel, escapeHtml } from "./format.js";

let alerts = [];
let currentFilter = "ALL";

const listEl = document.getElementById("alertList");
const filterChips = document.querySelectorAll(".filter-chip");

filterChips.forEach((chip) => {
  chip.addEventListener("click", () => setFilter(chip.dataset.filter));
});

function setFilter(filter) {
  currentFilter = filter;
  filterChips.forEach((chip) => chip.classList.toggle("active", chip.dataset.filter === filter));
  render();
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
      return `
        <div class="alert-card">
          <div class="alert-card-top">
            <span class="threat-pill ${level}">${threatLabel(a.threat_level)}</span>
            <span class="alert-card-time mono">${formatTime(a.timestamp)}</span>
          </div>
          <div class="alert-card-type">${escapeHtml(a.object_type || a.reading_type || "Unclassified object")}</div>
          <div class="alert-card-meta mono">${escapeHtml(a.device_ids || "—")} · ${a.lat.toFixed(4)}, ${a.lng.toFixed(4)}</div>
          <span class="status-tag">${statusLabel(a.status)}</span>
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
