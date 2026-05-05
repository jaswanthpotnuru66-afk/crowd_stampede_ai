const STYLES = {
  high:     { bg: "rgba(239,68,68,.25)",  border: "rgba(239,68,68,.5)",  color: "#fca5a5" },
  moderate: { bg: "rgba(245,158,11,.2)",  border: "rgba(245,158,11,.4)", color: "#fde68a" },
  low:      { bg: "rgba(34,197,94,.15)",  border: "rgba(34,197,94,.3)",  color: "#86efac" },
};

export default function ZoneMap({ zones }) {
  const levels = zones || Array(6).fill("low");

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Zone heat map</div>
        <span className="badge b-blue">6 zones</span>
      </div>
      <div style={{ padding: "0 14px 14px" }}>
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gridTemplateRows: "1fr 1fr",
          gap: 4,
          aspectRatio: "1.6",
          background: "#090d18",
          borderRadius: 6,
          padding: 4,
        }}>
          {levels.map((l, i) => {
            const s = STYLES[l] || STYLES.low;
            return (
              <div key={i} style={{
                background: s.bg,
                border: `1px solid ${s.border}`,
                borderRadius: 4,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 2,
              }}>
                <span style={{ fontSize: 11, fontWeight: 500, color: s.color }}>Z{i + 1}</span>
                <span style={{ fontSize: 9, color: s.color, opacity: 0.75 }}>{l.toUpperCase()}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}