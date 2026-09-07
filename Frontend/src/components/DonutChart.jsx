const COLORS = { high: "#f0453f", uncertain: "#f5a623", low: "#2fbf6f" };
const RADIUS = 40;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export default function DonutChart({ high, uncertain, low }) {
  const total = high + uncertain + low;
  const segments = [
    { key: "high", label: "High risk", value: high },
    { key: "uncertain", label: "Uncertain", value: uncertain },
    { key: "low", label: "Low risk", value: low },
  ];

  let offset = 0;

  return (
    <div className="donut-wrap">
      <svg viewBox="0 0 100 100" width="140" height="140">
        {total === 0 ? (
          <circle cx="50" cy="50" r={RADIUS} fill="none" stroke="#22304a" strokeWidth="14" />
        ) : (
          segments.map((seg) => {
            const fraction = seg.value / total;
            const length = fraction * CIRCUMFERENCE;
            const dashOffset = -offset;
            offset += length;
            if (seg.value === 0) return null;
            return (
              <circle
                key={seg.key}
                cx="50"
                cy="50"
                r={RADIUS}
                fill="none"
                stroke={COLORS[seg.key]}
                strokeWidth="14"
                strokeDasharray={`${length} ${CIRCUMFERENCE - length}`}
                strokeDashoffset={dashOffset}
                transform="rotate(-90 50 50)"
                strokeLinecap="butt"
              />
            );
          })
        )}
        <text x="50" y="54" textAnchor="middle" className="donut-center-label">
          {total}
        </text>
      </svg>
      <ul className="donut-legend">
        {segments.map((seg) => (
          <li key={seg.key}>
            <span className={`donut-dot ${seg.key}`} />
            {seg.label}
            <span className="mono donut-count">{seg.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
