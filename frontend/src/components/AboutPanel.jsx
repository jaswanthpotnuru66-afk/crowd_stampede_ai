export default function AboutPanel() {
  const stats = [
    { value: "3.9s",  label: "Avg. advance warning",  icon: "⚡" },
    { value: "81%",   label: "HIGH risk precision",    icon: "🎯" },
    { value: "0.80",  label: "Risk F1 (macro)",        icon: "📊" },
    { value: "8%",    label: "False alarm rate",        icon: "✅" },
  ];

  const pipeline = [
    { step: "01", title: "Frame Buffer",  desc: "Circular queue captures 8 frames at 30 FPS", icon: "🎞️" },
    { step: "02", title: "Swin-Tiny",     desc: "Spatial features via ImageNet-21k transformer", icon: "🧠" },
    { step: "03", title: "2-Layer LSTM",  desc: "Temporal modeling across the 8-frame sequence", icon: "🔄" },
    { step: "04", title: "Risk Output",   desc: "3-class prediction: LOW / MODERATE / HIGH", icon: "🚨" },
  ];

  const techChips = [
    { label: "Swin-T + LSTM", color: "#3b82f6" },
    { label: "ONNX Runtime", color: "#06b6d4" },
    { label: "PyTorch 2.1", color: "#f59e0b" },
    { label: "FastAPI", color: "#10b981" },
    { label: "React 18", color: "#3b82f6" },
    { label: "Vite 5", color: "#8b5cf6" },
    { label: "HajjV2 Dataset", color: "#ef4444" },
    { label: "Kaggle T4 GPU", color: "#06b6d4" },
  ];

  const riskLevels = [
    { color: "#10b981", level: "LOW",      action: "Monitor normally — crowd flow is safe" },
    { color: "#f59e0b", level: "MODERATE", action: "Alert field personnel · Prepare exits" },
    { color: "#ef4444", level: "HIGH",     action: "Immediate dispersal protocol required" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>

      {/* ── About Card ── */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">About CrowdSentinel AI</div>
          <span className="badge b-cyan">v2.0</span>
        </div>

        <div style={{ padding: "16px 20px" }}>
          <p style={{ fontSize: 12.5, color: "var(--text-mid)", lineHeight: 1.75 }}>
            CrowdSentinel AI is a real-time stampede prediction system that analyzes
            surveillance footage to detect dangerous crowd conditions{" "}
            <em style={{ color: "var(--accent)" }}>before</em> they become visible
            to the human eye.
          </p>
          <p style={{ fontSize: 12.5, color: "var(--text-mid)", lineHeight: 1.75, marginTop: 10 }}>
            Unlike frame-by-frame density estimators, it models{" "}
            <strong style={{ color: "var(--text-hi)" }}>how the crowd is changing over time</strong>{" "}
            — rising density, increasing turbulence, slowing velocity — to provide
            actionable advance warning to security operators.
          </p>
        </div>

        {/* Risk legend */}
        <div style={{ padding: "0 20px 18px", display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ fontSize: 9.5, fontWeight: 700, color: "var(--text-lo)", textTransform: "uppercase", letterSpacing: ".12em", marginBottom: 4 }}>
            Risk Classification
          </div>
          {riskLevels.map(r => (
            <div key={r.level} style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "9px 13px", borderRadius: 9,
              background: r.color === "#10b981" ? "rgba(16,185,129,0.06)" : r.color === "#f59e0b" ? "rgba(245,158,11,0.06)" : "rgba(239,68,68,0.06)",
              border: `1px solid ${r.color}28`,
              transition: "border-color .2s",
            }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: r.color, boxShadow: `0 0 10px ${r.color}`, flexShrink: 0 }} />
              <span style={{ fontSize: 11, fontWeight: 800, color: r.color, width: 72, fontFamily: "var(--mono)", letterSpacing: ".05em" }}>{r.level}</span>
              <span style={{ fontSize: 11, color: "var(--text-mid)" }}>{r.action}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Performance Stats ── */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">Model Performance</div>
          <span className="badge b-green">Validated</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, padding: 14 }}>
          {stats.map(s => (
            <div key={s.label} className="stat-card">
              <div style={{ fontSize: 20, marginBottom: 6 }}>{s.icon}</div>
              <div className="stat-val">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── AI Pipeline ── */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">AI Pipeline</div>
          <span className="badge b-blue">4-Stage</span>
        </div>
        <div style={{ paddingTop: 8, paddingBottom: 8 }}>
          {pipeline.map((p, i) => (
            <div key={p.step} className="pipeline-step">
              {i < pipeline.length - 1 && <div className="pipeline-connector" />}
              <div className="pipeline-num">{p.step}</div>
              <div style={{ paddingTop: 2 }}>
                <div className="pipeline-title">
                  <span style={{ marginRight: 6 }}>{p.icon}</span>{p.title}
                </div>
                <div className="pipeline-desc">{p.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Tech Stack ── */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">Tech Stack</div>
        </div>
        <div style={{ padding: "14px 20px", display: "flex", flexWrap: "wrap", gap: 7 }}>
          {techChips.map((t) => (
            <div key={t.label} className="tech-chip" style={{ borderColor: `${t.color}25`, color: t.color }}>
              {t.label}
            </div>
          ))}
        </div>

        {/* Dataset info */}
        <div style={{ margin: "4px 14px 14px", padding: "10px 14px", borderRadius: 9, background: "rgba(6,182,212,0.04)", border: "1px solid rgba(6,182,212,0.1)" }}>
          <div style={{ fontSize: 9, color: "var(--text-lo)", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".12em", marginBottom: 6 }}>Training Details</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
            {[
              { k: "Dataset", v: "HajjV2" },
              { k: "Frames", v: "~33,750" },
              { k: "Epochs", v: "80" },
              { k: "Hardware", v: "Kaggle T4" },
            ].map(({ k, v }) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ fontSize: 10, color: "var(--text-lo)" }}>{k}</span>
                <span style={{ fontSize: 10, color: "var(--text-mid)", fontFamily: "var(--mono)", fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{
          margin: "0 14px 14px",
          padding: "9px 14px",
          borderRadius: 8,
          background: "rgba(8,12,25,0.6)",
          border: "1px solid var(--border-dim)",
          display: "flex", alignItems: "center", gap: 8,
        }}>
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--risk-low)", boxShadow: "0 0 10px var(--risk-low-glow)", animation: "blink 2s infinite" }} />
          <span style={{ fontSize: 11, color: "var(--text-lo)" }}>
            Built at <strong style={{ color: "var(--text-mid)" }}>GITAM School of Science</strong> · MIT License
          </span>
        </div>
      </div>

    </div>
  );
}
