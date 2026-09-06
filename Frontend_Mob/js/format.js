/**
 * format.js
 * ---------
 * Small, pure display helpers shared by the alerts list and the
 * add-alert screen. No DOM access, no state — easy to edit in
 * isolation or reuse elsewhere.
 */

export function formatTime(ts) {
  const d = new Date(ts);
  if (isNaN(d)) return "—";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function statusLabel(status) {
  return (
    { pending_verification: "Pending", confirmed_threat: "Confirmed", false_alarm: "False alarm" }[status] ||
    status
  );
}

export function threatLabel(level) {
  const n = (level || "").toLowerCase();
  return n === "high" ? "High" : n === "uncertain" ? "Uncertain" : "Low";
}

export function escapeHtml(str) {
  return String(str).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}
