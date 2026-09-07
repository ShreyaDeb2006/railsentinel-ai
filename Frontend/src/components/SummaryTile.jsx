export default function SummaryTile({ label, count, icon, tone, onClick }) {
  return (
    <button className={`summary-tile ${tone}`} onClick={onClick}>
      <div className="summary-tile-top">
        <span className="summary-tile-label">{label}</span>
        <span className="summary-tile-icon">{icon}</span>
      </div>
      <div className="summary-tile-count">{count}</div>
    </button>
  );
}
