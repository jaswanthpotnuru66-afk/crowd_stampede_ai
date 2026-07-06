import { useRef, useEffect } from "react";

function normalizeHistory(history, currentCount) {
  const values = (history || [])
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value));

  if (values.length === 0) return [];

  const fallback = Number(currentCount) || 0;
  const max = Math.max(...values);

  if (max === 0 && fallback > 0) {
    return values.map(() => Math.round(fallback));
  }

  if (max > 0 && max <= 1 && fallback > 1) {
    return values.map((value) => Math.round((value / max) * fallback));
  }

  return values.map((value) => Math.max(0, Math.round(value)));
}

function formatCount(value) {
  return Math.round(value).toLocaleString();
}

function TrendArrow({ history }) {
  if (history.length < 2) return null;
  const last = history[history.length - 1];
  const prev = history[history.length - 2];
  const delta = last - prev;
  const up = delta > 0;
  const color = up ? "#ef4444" : "#10b981";

  return (
    <span style={{ color, fontSize: 10, fontFamily: "var(--mono)", display: "flex", alignItems: "center", gap: 3 }}>
      {up ? "UP" : "DOWN"} {formatCount(Math.abs(delta))}
    </span>
  );
}

export default function MetricsChart({ history = [], riskClass, currentCount = 0 }) {
  const svgRef = useRef(null);
  const chartHistory = normalizeHistory(history, currentCount);

  useEffect(() => {
    if (!svgRef.current || chartHistory.length < 2) return;

    const W = 600;
    const H = 140;
    const rawMin = Math.min(...chartHistory);
    const rawMax = Math.max(...chartHistory);
    const mn = rawMax === rawMin ? 0 : rawMin;
    const mx = rawMax === rawMin ? Math.max(rawMax, 1) : rawMax;
    const range = mx - mn || 1;

    const color = riskClass === "HIGH" ? "#ef4444" : riskClass === "MODERATE" ? "#f97316" : "#22c55e";
    const glowId = "chartGlow";
    const gradId = "chartGrad";
    const gridColor = "rgba(255,255,255,0.04)";

    const pts = chartHistory.map((v, i) => ({
      x: (i / (chartHistory.length - 1)) * W,
      y: H - 14 - ((v - mn) / range) * (H - 28),
    }));

    const line = pts.map((p, i) => {
      if (i === 0) return `M ${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
      const prev = pts[i - 1];
      const cx1 = (prev.x + (p.x - prev.x) * 0.5).toFixed(1);
      const cy1 = prev.y.toFixed(1);
      const cx2 = (p.x - (p.x - prev.x) * 0.5).toFixed(1);
      const cy2 = p.y.toFixed(1);
      return `C ${cx1} ${cy1}, ${cx2} ${cy2}, ${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
    }).join(" ");

    const areaPts = [
      `M ${pts[0].x.toFixed(1)} ${H}`,
      ...pts.map((p, i) => {
        if (i === 0) return `L ${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
        const prev = pts[i - 1];
        const cx1 = (prev.x + (p.x - prev.x) * 0.5).toFixed(1);
        const cx2 = (p.x - (p.x - prev.x) * 0.5).toFixed(1);
        return `C ${cx1} ${prev.y.toFixed(1)}, ${cx2} ${p.y.toFixed(1)}, ${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
      }),
      `L ${pts[pts.length - 1].x.toFixed(1)} ${H}`,
      "Z",
    ].join(" ");

    const gridLines = [0.25, 0.5, 0.75].map((frac) => {
      const y = H - 14 - frac * (H - 28);
      const val = Math.round(mn + frac * range);
      return `
        <line x1="0" y1="${y.toFixed(1)}" x2="${W}" y2="${y.toFixed(1)}" stroke="${gridColor}" stroke-width="1"/>
        <text x="4" y="${(y - 3).toFixed(1)}" font-size="8" fill="rgba(255,255,255,0.18)" font-family="JetBrains Mono, monospace">${val}</text>
      `;
    }).join("");

    const lastPt = pts[pts.length - 1];

    svgRef.current.innerHTML = `
      <defs>
        <filter id="${glowId}">
          <feGaussianBlur stdDeviation="3" result="blur"/>
          <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <linearGradient id="${gradId}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="${color}" stop-opacity="0.22"/>
          <stop offset="60%" stop-color="${color}" stop-opacity="0.06"/>
          <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
        </linearGradient>
      </defs>
      ${gridLines}
      <path d="${areaPts}" fill="url(#${gradId})"/>
      <path d="${line}" fill="none" stroke="${color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" filter="url(#${glowId})"/>
      <circle cx="${lastPt.x.toFixed(1)}" cy="${lastPt.y.toFixed(1)}" r="5" fill="${color}" filter="url(#${glowId})" opacity="0.9"/>
      <circle cx="${lastPt.x.toFixed(1)}" cy="${lastPt.y.toFixed(1)}" r="9" fill="${color}" opacity="0.15">
        <animate attributeName="r" values="5;14;5" dur="2s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.3;0;0.3" dur="2s" repeatCount="indefinite"/>
      </circle>
    `;
  }, [chartHistory, riskClass]);

  const riskColor = riskClass === "HIGH" ? "#ef4444" : riskClass === "MODERATE" ? "#f97316" : "#22c55e";
  const lastVal = chartHistory.length > 0 ? chartHistory[chartHistory.length - 1] : null;
  const minVal = chartHistory.length >= 2 ? Math.min(...chartHistory) : null;
  const maxVal = chartHistory.length >= 2 ? Math.max(...chartHistory) : null;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">Crowd Count History</div>
          <div className="card-sub">Detected persons over time · {chartHistory.length} samples</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {chartHistory.length >= 2 && <TrendArrow history={chartHistory} />}
          {lastVal != null && (
            <span style={{ fontSize: 18, fontWeight: 800, fontFamily: "var(--mono)", color: riskColor, letterSpacing: "-.02em" }}>
              {formatCount(lastVal)}
              <span style={{ fontSize: 10, color: "var(--text-lo)", fontWeight: 500, marginLeft: 4 }}>persons</span>
            </span>
          )}
        </div>
      </div>

      <div style={{ padding: "16px 20px 8px" }}>
        {chartHistory.length < 2 ? (
          <div style={{
            height: 140, background: "rgba(16,10,14,0.65)", borderRadius: 10,
            display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8,
            border: "1px solid var(--border-dim)",
          }}>
            <div style={{ fontSize: 28, opacity: 0.28 }}>CHART</div>
            <span style={{ fontSize: 11, color: "var(--text-lo)" }}>Awaiting analysis data...</span>
          </div>
        ) : (
          <div style={{ position: "relative" }}>
            <svg
              ref={svgRef}
              width="100%" height="140"
              viewBox="0 0 600 140"
              preserveAspectRatio="none"
              style={{
                display: "block",
                background: "rgba(8,12,25,0.6)",
                borderRadius: 10,
                border: "1px solid var(--border-dim)",
              }}
            />
          </div>
        )}

        {chartHistory.length >= 2 && (
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 10, gap: 8 }}>
            {[
              { label: "MIN", val: formatCount(minVal), color: "#22c55e" },
              { label: "AVG", val: formatCount(chartHistory.reduce((a, b) => a + b, 0) / chartHistory.length), color: "var(--accent)" },
              { label: "MAX", val: formatCount(maxVal), color: "#ef4444" },
              { label: "SAMPLES", val: chartHistory.length, color: "var(--text-lo)" },
            ].map((s) => (
              <div key={s.label} style={{
                flex: 1, textAlign: "center",
                padding: "7px 0",
                background: "rgba(16,10,14,0.55)",
                border: "1px solid var(--border-dim)",
                borderRadius: 7,
              }}>
                <div style={{ fontSize: 9, color: "var(--text-lo)", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".1em" }}>{s.label}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: s.color, fontFamily: "var(--mono)", marginTop: 3 }}>{s.val}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
