export default function RiskPanel({ data }) {
  if (!data) return null;

  const risk = data.risk_class || "LOW";
  const probs = data.risk_probs || [0.75, 0.2, 0.05];

  const bannerClass = { HIGH: "risk-banner-high", MODERATE: "risk-banner-mod", LOW: "risk-banner-low" }[risk];
  const iconClass   = { HIGH: "risk-icon-high",   MODERATE: "risk-icon-mod",   LOW: "risk-icon-low"   }[risk];
  const mainText    = { HIGH: "HIGH RISK DETECTED", MODERATE: "MODERATE RISK", LOW: "LOW RISK" }[risk];
  const subText     = {
    HIGH:     "Stampede conditions likely — immediate action required",
    MODERATE: "Crowd density increasing — monitor closely",
    LOW:      "Crowd levels normal — no intervention needed",
  }[risk];

  const badgeClass = { HIGH: "b-red", MODERATE: "b-amber", LOW: "b-green" }[risk];

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">Analysis results</div>
          {data.video_info && (
            <div className="card-sub">{data.video_info.filename} · {data.video_info.duration_s}s</div>
          )}
        </div>
        <span className={`badge ${badgeClass}`}>{risk}</span>
      </div>

      <div className={`risk-banner ${bannerClass}`}>
        <div className={`risk-icon ${iconClass}`}>
          {risk === "HIGH" ? "!" : risk === "MODERATE" ? "~" : "✓"}
        </div>
        <div>
          <div className="risk-main-text">{mainText}</div>
          <div className="risk-sub-text">{subText}</div>
        </div>
      </div>

      <div className="metrics-grid">
        {[
          { label: "Max density",      value: data.crowd_coverage != null ? Math.round(data.crowd_coverage * 100) + "%" : "—", color: "amber" },
          { label: "Avg speed",        value: data.avg_speed != null ? data.avg_speed.toFixed(1) + " px/f" : "—",             color: "" },
          { label: "Turbulence",       value: data.turbulence != null ? data.turbulence.toFixed(2) : "—",                     color: data.turbulence > 0.5 ? "red" : "" },
        ].map((m) => (
          <div className="metric-cell" key={m.label}>
            <div className="metric-label">{m.label}</div>
            <div className={`metric-val ${m.color}`}>{m.value}</div>
          </div>
        ))}
      </div>

      <div className="prob-section">
        <div className="mini-title">Risk probability</div>
        {[
          { name: "Low",      val: probs[0], color: "#4ade80" },
          { name: "Moderate", val: probs[1], color: "#fbbf24" },
          { name: "High",     val: probs[2], color: "#f87171" },
        ].map((p) => (
          <div className="prob-row" key={p.name}>
            <span className="prob-name" style={{ color: p.color }}>{p.name}</span>
            <div className="prob-track">
              <div className="prob-fill" style={{ width: `${Math.round(p.val * 100)}%`, background: p.color }} />
            </div>
            <span className="prob-pct" style={{ color: p.color }}>{Math.round(p.val * 100)}%</span>
          </div>
        ))}
      </div>

      {data.events?.length > 0 && (
        <div className="log-section">
          <div className="mini-title">Event timeline</div>
          {data.events.map((e, i) => (
            <div className="log-row" key={i}>
              <div className="log-dot" style={{ background: e.color }} />
              <span className="log-text">{e.message}</span>
              <span className="log-time">{e.timestamp}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}