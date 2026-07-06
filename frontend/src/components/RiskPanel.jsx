import { useEffect, useRef, useState } from "react";

/* ── Animated ring gauge ── */
function RingGauge({ value, max = 100, color, label }) {
  const r = 50;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(1, value / max);
  const offset = circ * (1 - pct);

  return (
    <div className="ring-gauge-wrap">
      <div className="ring-gauge">
        <svg width="120" height="120" viewBox="0 0 120 120">
          <circle className="ring-track" cx="60" cy="60" r={r} />
          <circle
            className="ring-fill"
            cx="60" cy="60" r={r}
            stroke={color}
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={{ filter: `drop-shadow(0 0 6px ${color})` }}
          />
        </svg>
        <div className="ring-center">
          <span className="ring-val" style={{ color }}>{Math.round(pct * 100)}</span>
          <span className="ring-label">{label}</span>
        </div>
      </div>
    </div>
  );
}

/* ── Animated number counter ── */
function AnimatedVal({ val }) {
  const [displayed, setDisplayed] = useState(val);
  const prev = useRef(val);
  useEffect(() => {
    if (val === prev.current) return;
    prev.current = val;
    setDisplayed(val);
  }, [val]);
  return <span style={{ animation: "countUp .4s ease" }}>{displayed}</span>;
}

export default function RiskPanel({ data }) {
  if (!data) return null;

  const risk   = data.risk_class || "LOW";
  const probs  = data.risk_probs || [0.75, 0.2, 0.05];

  const bannerClass = { HIGH: "risk-banner-high", MODERATE: "risk-banner-mod", LOW: "risk-banner-low" }[risk];
  const iconClass   = { HIGH: "risk-icon-high",   MODERATE: "risk-icon-mod",   LOW: "risk-icon-low" }[risk];
  const badgeClass  = { HIGH: "b-red", MODERATE: "b-amber", LOW: "b-green" }[risk];
  const ringColor   = { HIGH: "#ef4444", MODERATE: "#f97316", LOW: "#22c55e" }[risk];

  const icon     = { HIGH: "⚠", MODERATE: "◉", LOW: "✓" }[risk];
  const mainText = { HIGH: "HIGH RISK — CRITICAL", MODERATE: "MODERATE RISK", LOW: "LOW RISK — NORMAL" }[risk];
  const subText  = {
    HIGH:     "Stampede conditions likely — initiate immediate evacuation protocol",
    MODERATE: "Crowd density increasing — alert field personnel and prepare exit routes",
    LOW:      "Crowd flow is normal — no intervention required at this time",
  }[risk];

  const riskIndex = Math.round((data.risk_probs?.[2] || 0) * 100);

  const metrics = [
    {
      label: "Max Density",
      value: data.crowd_coverage != null ? Math.round(data.crowd_coverage * 100) + "%" : "—",
      color: data.crowd_coverage > 0.65 ? "red" : data.crowd_coverage > 0.35 ? "amber" : "green",
    },
    {
      label: "Avg Speed",
      value: data.avg_speed != null ? data.avg_speed.toFixed(2) + " px/f" : "—",
      color: "",
    },
    {
      label: "Turbulence",
      value: data.turbulence != null ? data.turbulence.toFixed(3) : "—",
      color: data.turbulence > 0.6 ? "red" : data.turbulence > 0.3 ? "amber" : "green",
    },
  ];

  return (
    <div className="card">
      {/* Header */}
      <div className="card-header">
        <div>
          <div className="card-title">Analysis Results</div>
          {data.video_info && (
            <div className="card-sub">
              {data.video_info.filename} · {data.video_info.duration_s}s · {data.video_info.fps} FPS
            </div>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className={`badge ${badgeClass}`}>{risk}</span>
        </div>
      </div>

      {/* Risk Banner */}
      <div className={`risk-banner ${bannerClass}`}>
        <div className={`risk-icon ${iconClass}`}>{icon}</div>
        <div style={{ flex: 1 }}>
          <div className="risk-main-text">{mainText}</div>
          <div className="risk-sub-text">{subText}</div>
        </div>
        {/* Risk index ring */}
        <div style={{ flexShrink: 0 }}>
          <RingGauge value={riskIndex} max={100} color={ringColor} label="Risk %" />
        </div>
      </div>

      {/* Metric cells */}
      <div className="metrics-grid">
        {metrics.map(m => (
          <div className="metric-cell" key={m.label}>
            <div className="metric-label">{m.label}</div>
            <div className={`metric-val ${m.color}`}>
              <AnimatedVal val={m.value} />
            </div>
          </div>
        ))}
      </div>

      {/* Probability bars */}
      <div className="prob-section">
        <div className="mini-title">Confidence Distribution</div>
        {[
          { name: "Low",      val: probs[0], color: "#22c55e", glow: "rgba(34,197,94,0.5)" },
          { name: "Moderate", val: probs[1], color: "#f97316", glow: "rgba(249,115,22,0.5)" },
          { name: "High",     val: probs[2], color: "#ef4444", glow: "rgba(239,68,68,0.5)" },
        ].map(p => (
          <div className="prob-row" key={p.name}>
            <span className="prob-name" style={{ color: p.color }}>{p.name}</span>
            <div className="prob-track">
              <div
                className="prob-fill"
                style={{
                  width: `${Math.round(p.val * 100)}%`,
                  background: `linear-gradient(90deg, ${p.color}88, ${p.color})`,
                  boxShadow: `0 0 8px ${p.glow}`,
                }}
              />
            </div>
            <span className="prob-pct" style={{ color: p.color }}>
              {Math.round(p.val * 100)}%
            </span>
          </div>
        ))}
      </div>

      {/* Event timeline */}
      {data.events?.length > 0 && (
        <div className="log-section">
          <div className="mini-title">Event Timeline</div>
          {data.events.map((e, i) => (
            <div className="log-row" key={i}>
              <div className="log-dot" style={{ background: e.color, boxShadow: `0 0 8px ${e.color}` }} />
              <span className="log-text">{e.message}</span>
              <span className="log-time">{e.timestamp}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}