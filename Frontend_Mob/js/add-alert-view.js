/**
 * add-alert-view.js
 * -----------------
 * Everything for the "Add Alert" screen: form fields, "use current
 * location", and the big red button's submit handler.
 */
import { submitHandheldReading } from "./api.js";
import { escapeHtml } from "./format.js";

const officerIdEl = document.getElementById("officerId");
const threatLevelEl = document.getElementById("threatLevel");
const descriptionEl = document.getElementById("description");
const notesEl = document.getElementById("notes");
const latEl = document.getElementById("lat");
const lngEl = document.getElementById("lng");
const msgEl = document.getElementById("addMsg");
const alertBtn = document.getElementById("alertBtn");

// Officer ID persists locally, same storage key the React app uses,
// so a device only has to type it once across either app.
officerIdEl.value = localStorage.getItem("rpf_officer_id") || "";

document.getElementById("locateBtn").addEventListener("click", useCurrentLocation);
alertBtn.addEventListener("click", submitAlert);

function showMessage(text, kind) {
  msgEl.innerHTML = text ? `<div class="inline-msg ${kind}">${escapeHtml(text)}</div>` : "";
}

function useCurrentLocation() {
  if (!navigator.geolocation) {
    showMessage("Location isn't available on this device.", "error");
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      latEl.value = pos.coords.latitude.toFixed(6);
      lngEl.value = pos.coords.longitude.toFixed(6);
    },
    () => showMessage("Couldn't get your location — enter it manually.", "error")
  );
}

async function submitAlert() {
  const officerId = officerIdEl.value.trim();
  const threatLevel = threatLevelEl.value;
  const description = descriptionEl.value.trim();
  const notes = notesEl.value.trim();
  const lat = parseFloat(latEl.value);
  const lng = parseFloat(lngEl.value);

  if (!officerId) return showMessage("Enter your officer ID before reporting.", "error");
  if (!description) return showMessage("Describe what you observed.", "error");
  if (Number.isNaN(lat) || Number.isNaN(lng)) {
    return showMessage('Enter a valid GPS location, or tap "Use current location".', "error");
  }

  alertBtn.disabled = true;
  showMessage(null);

  try {
    await submitHandheldReading({ readingValue: threatLevel, description, notes, deviceId: officerId, lat, lng });
    localStorage.setItem("rpf_officer_id", officerId);
    showMessage("Alert sent.", "success");
    descriptionEl.value = "";
    notesEl.value = "";
    document.dispatchEvent(new CustomEvent("alert-submitted"));
  } catch (err) {
    showMessage(err.message, "error");
  } finally {
    alertBtn.disabled = false;
  }
}
