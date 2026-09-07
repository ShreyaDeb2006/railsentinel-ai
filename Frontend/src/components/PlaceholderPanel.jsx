export default function PlaceholderPanel({ title, note }) {
  return (
    <div className="panel placeholder-panel">
      <div className="panel-heading">{title}</div>
      <div className="placeholder-body">
        <span className="placeholder-dot" />
        <p>{note || "Not built yet — coming soon."}</p>
      </div>
    </div>
  );
}
