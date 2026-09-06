/**
 * Renders the LOW / UNCERTAIN / HIGH pill. threat_level from the
 * backend arrives upper-case (see fusion.py classify()).
 */
export default function ThreatBadge({ level }) {
  const normalized = (level || "").toLowerCase();
  const label =
    normalized === "high"
      ? "High"
      : normalized === "uncertain"
      ? "Uncertain"
      : "Low";

  return <span className={`threat-pill ${normalized}`}>{label}</span>;
}
