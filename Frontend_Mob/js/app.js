/**
 * app.js
 * ------
 * Entry point. Wires up the Alerts/Add Alert toggle, the connection
 * indicator, and starts the alerts feed. Each screen's own logic
 * lives in alerts-view.js / add-alert-view.js — this file just
 * connects them.
 */
import { loadAlerts, upsertAlert } from "./alerts-view.js";
import "./add-alert-view.js"; // wires its own DOM listeners as a side effect
import { connectAlertsSocket } from "./ws-client.js";

const alertsScreen = document.getElementById("alertsScreen");
const addScreen = document.getElementById("addScreen");
const toggleAlertsBtn = document.getElementById("toggleAlerts");
const toggleAddBtn = document.getElementById("toggleAdd");
const connDot = document.getElementById("connDot");
const connLabel = document.getElementById("connLabel");

function switchView(view) {
  alertsScreen.classList.toggle("active", view === "alerts");
  addScreen.classList.toggle("active", view === "add");
  toggleAlertsBtn.classList.toggle("active", view === "alerts");
  toggleAddBtn.classList.toggle("active", view === "add");
}

toggleAlertsBtn.addEventListener("click", () => switchView("alerts"));
toggleAddBtn.addEventListener("click", () => switchView("add"));

function setConnected(isLive) {
  connDot.classList.toggle("live", isLive);
  connLabel.textContent = isLive ? "Live" : "Offline";
}

// A submitted manual alert should show up in the list right away,
// even before the WebSocket round-trip confirms it.
document.addEventListener("alert-submitted", loadAlerts);

loadAlerts();
connectAlertsSocket(upsertAlert, setConnected);
setInterval(loadAlerts, 15000); // safety-net poll in case the socket drops silently
