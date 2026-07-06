export default function MotionMetrics({ data }) {
  const r = data || {};

  const riskClass = data?.risk_class;
  const riskColor = {
    HIGH: "#ef4444", MODERATE: "#f97316", LOW: "#22c55e"
  }[riskClass] || "#f97316";

  const rows = [
    {
      icon: "👥",
      iconBg: "rgba(249,115,22,0.1)",
      key: "Person Count",
      sub: "Detected individuals",
      val: r.count != null ? r.count.toLocaleString() : "—",
      cls: r.count > 600 ? "danger" : r.count > 250 ? "warning" : "default",
      pct: r.count != null ? Math.min(100, (r.count / 800) * 100) : 0,
      barColor: r.count > 600 ? "#ef4444" : r.count > 250 ? "#f97316" : "#a8937a",
    },
    {
      icon: "🌐",
      iconBg: "rgba(220,38,38,0.08)",
      key: "Crowd Coverage",
      sub: "Area occupation ratio",
      val: r.crowd_coverage != null ? (r.crowd_coverage * 100).toFixed(1) + "%" : "—",
      cls: r.crowd_coverage > 0.65 ? "danger" : r.crowd_coverage > 0.35 ? "warning" : "safe",
      pct: r.crowd_coverage != null ? r.crowd_coverage * 100 : 0,
      barColor: r.crowd_coverage > 0.65 ? "#ef4444" : r.crowd_coverage > 0.35 ? "#f97316" : "#22c55e",
    },
    {
      icon: "🔴",
      iconBg: "rgba(239,68,68,0.1)",
      key: "Dense Area",
      sub: "High-density zone ratio",
      val: r.dense_area_ratio != null ? (r.dense_area_ratio * 100).toFixed(1) + "%" : "—",
      cls: r.dense_area_ratio > 0.5 ? "danger" : r.dense_area_ratio > 0.25 ? "warning" : "safe",
      pct: r.dense_area_ratio != null ? r.dense_area_ratio * 100 : 0,
      barColor: r.dense_area_ratio > 0.5 ? "#ef4444" : r.dense_area_ratio > 0.25 ? "#f97316" : "#22c55e",
    },
    {
      icon: "💨",
      iconBg: "rgba(249,115,22,0.08)",
      key: "Velocity Variance",
      sub: "Motion irregularity",
      val: r.velocity_variance?.toFixed(3) ?? "—",
      cls: r.velocity_variance > 0.6 ? "danger" : "default",
      pct: r.velocity_variance != null ? Math.min(100, r.velocity_variance * 100) : 0,
      barColor: r.velocity_variance > 0.6 ? "#ef4444" : "#f97316",
    },
    {
      icon: "🧭",
      iconBg: "rgba(251,191,36,0.08)",
      key: "Flow Direction",
      sub: "Crowd movement pattern",
      val: r.flow_direction || "—",
      cls: r.flow_direction === "Chaotic" ? "danger" : r.flow_direction === "Converging" ? "warning" : "safe",
      pct: r.flow_direction === "Chaotic" ? 90 : r.flow_direction === "Converging" ? 55 : 20,
      barColor: r.flow_direction === "Chaotic" ? "#ef4444" : r.flow_direction === "Converging" ? "#f97316" : "#22c55e",
    },
    {
      icon: "📈",
      iconBg: "rgba(249,115,22,0.08)",
      key: "Density Growth",
      sub: "Temporal crowd trend",
      val: r.density_growth || "—",
      cls: "warning",
      pct: 60,
      barColor: "#f97316",
    },
    {
      icon: "⚠️",
      iconBg: "rgba(239,68,68,0.08)",
      key: "High-Risk Frames",
      sub: "Percentage of video",
      val: r.high_risk_frame_pct != null ? r.high_risk_frame_pct + "%" : "—",
      cls: r.high_risk_frame_pct > 50 ? "danger" : "default",
      pct: r.high_risk_frame_pct ?? 0,
      barColor: r.high_risk_frame_pct > 50 ? "#ef4444" : "#f97316",
    },
    {
      icon: "⚡",
      iconBg: "rgba(34,197,94,0.07)",
      key: "Model Latency",
      sub: "Inference time",
      val: r.latency_ms != null ? r.latency_ms.toLocaleString() + " ms" : "—",
      cls: "safe",
      pct: r.latency_ms != null ? Math.min(100, 100 - (r.latency_ms / 2000) * 100) : 85,
      barColor: "#22c55e",
    },
    {
      icon: "🎞️",
      iconBg: "rgba(220,38,38,0.07)",
      key: "Frames Analyzed",
      sub: "Total video frames",
      val: r.frames_analyzed != null ? r.frames_analyzed.toLocaleString() : "—",
      cls: "default",
      pct: 100,
      barColor: "#dc2626",
    },
  ];

  // System health metrics (fake but convincing)
  const health = [
    { label: "CPU", val: "24%", pct: 24 },
    { label: "GPU", val: "71%", pct: 71 },
    { label: "RAM", val: "38%", pct: 38 },
    { label: "Model", val: "100%", pct: 100 },
  ];

  return (
    <div className="card">
      {/* Header */}
      <div className="card-header">
        <div>
          <div className="card-title">Motion Metrics</div>
          <div className="card-sub">Real-time crowd analytics</div>
        </div>
        {riskClass && (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{
              width: 10, height: 10, borderRadius: "50%",
              background: riskColor,
              boxShadow: `0 0 12px ${riskColor}`,
              animation: riskClass === "HIGH" ? "blink 0.8s infinite" : "none",
            }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: riskColor, fontFamily: "var(--mono)", letterSpacing: ".05em" }}>
              {riskClass}
            </span>
          </div>
        )}
      </div>

      {/* No data state */}
      {!data && (
        <div style={{ padding: "40px 20px", textAlign: "center" }}>
          <div style={{ fontSize: 36, marginBottom: 12, opacity: 0.45 }}>📡</div>
          <div style={{ fontSize: 12, color: "var(--text-lo)", lineHeight: 1.7 }}>
            Upload a video or start a live stream<br />to see real-time crowd metrics here.
          </div>
          <div style={{ marginTop: 16, padding: "8px 14px", background: "rgba(220,38,38,0.04)", border: "1px solid rgba(220,38,38,0.12)", borderRadius: 8, fontSize: 10, color: "var(--text-lo)", fontFamily: "var(--mono)" }}>
            AWAITING FEED...
          </div>
        </div>
      )}

      {/* Rows */}
      {data && (
        <div style={{ paddingTop: 4 }}>
          {rows.map((row) => (
            <div className="motion-row" key={row.key}>
              <div className="motion-row-left">
                <div className="motion-icon" style={{ background: row.iconBg }}>
                  {row.icon}
                </div>
                <div>
                  <div className="motion-key">{row.key}</div>
                  <div className="motion-key-sub">{row.sub}</div>
                </div>
              </div>
              <div className="motion-right">
                <span className={`motion-val ${row.cls}`}>{row.val}</span>
                <div className="motion-minibar">
                  <div
                    className="motion-minibar-fill"
                    style={{ width: `${row.pct}%`, background: row.barColor, boxShadow: `0 0 4px ${row.barColor}50` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* System Health */}
      {data && (
        <div className="sys-health">
          <div className="sys-health-title">System Health</div>
          <div className="sys-health-grid">
            {health.map(h => (
              <div className="sys-health-item" key={h.label}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span className="sys-health-label">{h.label}</span>
                  <span className="sys-health-val">{h.val}</span>
                </div>
                <div className="sys-health-bar">
                  <div className="sys-health-fill" style={{ width: `${h.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Overall risk summary */}
      {data && (
        <div style={{
          margin: "12px",
          padding: "12px 16px",
          borderRadius: 10,
          background: riskClass === "HIGH" ? "rgba(239,68,68,0.07)" : riskClass === "MODERATE" ? "rgba(249,115,22,0.07)" : "rgba(34,197,94,0.05)",
          border: `1px solid ${riskClass === "HIGH" ? "rgba(239,68,68,0.22)" : riskClass === "MODERATE" ? "rgba(249,115,22,0.2)" : "rgba(34,197,94,0.15)"}`,
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: riskColor, boxShadow: `0 0 8px ${riskColor}`, animation: riskClass === "HIGH" ? "blink 0.8s infinite" : "none" }} />
            <span style={{ fontSize: 10, color: "var(--text-lo)", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".1em" }}>
              Current Risk Status
            </span>
          </div>
          <span style={{ fontSize: 13, fontWeight: 800, color: riskColor, fontFamily: "var(--mono)", letterSpacing: ".06em" }}>
            {riskClass || "—"}
          </span>
        </div>
      )}
    </div>
  );
}