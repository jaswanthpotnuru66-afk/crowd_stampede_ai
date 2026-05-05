export default function MotionMetrics({ data }) {
  const rows = [
    { key: "Crowd coverage",   val: data?.crowd_coverage != null ? (data.crowd_coverage * 100).toFixed(2) + "%" : "—", color: data?.crowd_coverage > 0.12 ? "#f87171" : data?.crowd_coverage > 0.05 ? "#fbbf24" : "#94a3b8" },
    { key: "Person count",     val: data?.count != null ? data.count : "—",                                          color: data?.count > 80 ? "#f87171" : data?.count > 30 ? "#fbbf24" : "#94a3b8" },
    { key: "Velocity variance",  val: data?.velocity_variance?.toFixed(2),                                    color: data?.velocity_variance > 0.6 ? "#f87171" : "#94a3b8" },
    { key: "Flow direction",     val: data?.flow_direction || "—",                                             color: data?.flow_direction === "Chaotic" ? "#f87171" : "#94a3b8" },
    { key: "Density growth",     val: data?.density_growth || "—",                                             color: "#fbbf24" },
    { key: "High-risk frames",   val: data?.high_risk_frame_pct != null ? data.high_risk_frame_pct + "%" : "—", color: "#94a3b8" },
    { key: "Model latency",      val: data?.latency_ms != null ? data.latency_ms + " ms" : "—",               color: "#4ade80" },
    { key: "Frames analyzed",    val: data?.frames_analyzed?.toLocaleString() || "—",                         color: "#94a3b8" },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Motion metrics</div>
      </div>
      <div style={{ padding: "4px 14px 12px" }}>
        {rows.map((r, i) => (
          <div key={r.key} style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "7px 0",
            borderBottom: i < rows.length - 1 ? "1px solid #1a2235" : "none",
          }}>
            <span style={{ fontSize: 11, color: "#64748b" }}>{r.key}</span>
            <span style={{ fontSize: 12, fontWeight: 500, color: r.color }}>{r.val || "—"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}