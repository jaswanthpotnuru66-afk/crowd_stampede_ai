import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

/* ── Animated number counter ── */
function Counter({ target, suffix = "", duration = 1800 }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = target / (duration / 16);
    const id = setInterval(() => {
      start += step;
      if (start >= target) { setVal(target); clearInterval(id); }
      else setVal(Math.floor(start));
    }, 16);
    return () => clearInterval(id);
  }, [target, duration]);
  return <>{val.toLocaleString()}{suffix}</>;
}

export default function LandingPage() {
  const navigate = useNavigate();

  const stats = [
    { value: 3.9,   suffix: "s",  label: "Advance Warning",    icon: "⚡", color: "#f97316", isFloat: true, fixed: 1 },
    { value: 81,    suffix: "%",  label: "HIGH Risk Precision", icon: "🎯", color: "#ef4444" },
    { value: 33750, suffix: "",   label: "Training Frames",     icon: "🎞️", color: "#fbbf24" },
    { value: 8,     suffix: "%",  label: "False Alarm Rate",    icon: "✅", color: "#22c55e" },
  ];

  const pipeline = [
    { step: "01", title: "Frame Buffer",  desc: "A circular queue captures the last 8 frames at 30 FPS, giving the model a short-term temporal window of the crowd.",  icon: "🎞️", color: "#f97316" },
    { step: "02", title: "Swin-Tiny",     desc: "Each frame is passed through a Swin Transformer (ImageNet-21k pretrained) to extract rich spatial crowd features.",   icon: "🧠", color: "#dc2626" },
    { step: "03", title: "2-Layer LSTM",  desc: "The 8-frame feature sequence is processed by a bidirectional LSTM that learns how crowd density evolves over time.",   icon: "🔄", color: "#fbbf24" },
    { step: "04", title: "Risk Output",   desc: "A 3-class softmax head outputs LOW / MODERATE / HIGH probabilities with 3.9s average advance warning before incidents.", icon: "🚨", color: "#ef4444" },
  ];

  const riskLevels = [
    { color: "#22c55e", bg: "rgba(34,197,94,0.06)",   border: "rgba(34,197,94,0.2)",  level: "LOW",      action: "Monitor normally", detail: "Crowd density and movement patterns are within safe parameters." },
    { color: "#f97316", bg: "rgba(249,115,22,0.06)",  border: "rgba(249,115,22,0.2)", level: "MODERATE", action: "Alert personnel", detail: "Rising density or turbulence detected. Prepare exit routes and alert field staff." },
    { color: "#ef4444", bg: "rgba(239,68,68,0.06)",   border: "rgba(239,68,68,0.2)",  level: "HIGH",     action: "Immediate action", detail: "Dangerous conditions detected. Initiate dispersal protocol immediately." },
  ];

  const techStack = [
    { label: "Swin Transformer", sub: "Backbone",     color: "#f97316" },
    { label: "2-Layer LSTM",     sub: "Temporal",     color: "#dc2626" },
    { label: "PyTorch 2.1",      sub: "Training",     color: "#fbbf24" },
    { label: "FastAPI",          sub: "Backend",      color: "#22c55e" },
    { label: "React 18 + Vite",  sub: "Frontend",     color: "#f97316" },
    { label: "HajjV2 Dataset",   sub: "Training data", color: "#ef4444" },
    { label: "ONNX Runtime",     sub: "Inference",    color: "#fbbf24" },
    { label: "Kaggle T4 GPU",    sub: "Hardware",     color: "#dc2626" },
  ];

  return (
    <div className="landing-page">

      {/* ── NAVBAR ── */}
      <nav className="landing-nav">
        <div className="landing-nav-brand">
          <div className="landing-nav-logo">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
            </svg>
          </div>
          <span className="landing-nav-name">Crowd<span className="landing-accent">Sentinel</span> AI</span>
        </div>
        <div className="landing-nav-right">
          <span className="landing-badge">v2.0</span>
          <button className="landing-nav-btn" onClick={() => navigate("/dashboard")}>
            Launch Dashboard
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
            </svg>
          </button>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section className="lp-hero">
        <div className="lp-hero-orb lp-orb-1" />
        <div className="lp-hero-orb lp-orb-2" />
        {/* third orb removed — was overboard */}
        <div className="lp-hero-inner">
          <div className="lp-hero-tag">
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 10px #22c55e", animation: "blink 2s infinite" }} />
            AI-Powered Crowd Safety Intelligence
          </div>
          <h1 className="lp-hero-title">
            Predict stampedes<br />
            <span className="lp-hero-gradient">before they happen</span>
          </h1>
          <p className="lp-hero-desc">
            CrowdSentinel AI analyzes live surveillance footage using a Swin Transformer + LSTM
            architecture to detect dangerous crowd conditions with up to <strong>3.9 seconds of advance warning</strong>
            — giving security teams precious time to act.
          </p>
          <div className="lp-hero-btns">
            <button className="lp-btn-primary" onClick={() => navigate("/dashboard")}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              Launch Dashboard
            </button>
            <a className="lp-btn-ghost" href="#how-it-works">
              How it works
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </a>
          </div>
        </div>
      </section>



      {/* ── HOW IT WORKS ── */}
      <section className="lp-section" id="how-it-works">
        <div className="lp-container">
          <div className="lp-section-header">
            <div className="lp-section-tag">Architecture</div>
            <h2 className="lp-section-title">How the AI Works</h2>
            <p className="lp-section-desc">A 4-stage deep learning pipeline that reads crowd footage the same way a trained security expert would — but faster, 24/7, without fatigue.</p>
          </div>
          <div className="lp-pipeline">
            {pipeline.map((p, i) => (
              <div key={p.step} className="lp-pipeline-card" style={{ "--card-color": p.color }}>
                <div className="lp-pipeline-header">
                  <div className="lp-pipeline-step" style={{ borderColor: `${p.color}30`, background: `${p.color}10`, color: p.color }}>{p.step}</div>
                  <div className="lp-pipeline-icon">{p.icon}</div>
                </div>
                <div className="lp-pipeline-title">{p.title}</div>
                <div className="lp-pipeline-desc">{p.desc}</div>
                {i < pipeline.length - 1 && (
                  <div className="lp-pipeline-arrow">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={p.color} strokeWidth="2" strokeLinecap="round" opacity="0.5">
                      <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── RISK LEVELS ── */}
      <section className="lp-section lp-risk-section">
        <div className="lp-container">
          <div className="lp-section-header">
            <div className="lp-section-tag">Classification</div>
            <h2 className="lp-section-title">3-Class Risk System</h2>
            <p className="lp-section-desc">Every analysis frame is classified into one of three risk levels, each triggering a corresponding response protocol.</p>
          </div>
          <div className="lp-risk-grid">
            {riskLevels.map(r => (
              <div key={r.level} className="lp-risk-card" style={{ background: r.bg, borderColor: r.border }}>
                <div className="lp-risk-header">
                  <div className="lp-risk-dot" style={{ background: r.color, boxShadow: `0 0 12px ${r.color}` }} />
                  <div className="lp-risk-level" style={{ color: r.color }}>{r.level}</div>
                </div>
                <div className="lp-risk-action" style={{ color: r.color }}>{r.action}</div>
                <div className="lp-risk-detail">{r.detail}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TECH STACK ── */}
      <section className="lp-section">
        <div className="lp-container">
          <div className="lp-section-header">
            <div className="lp-section-tag">Built With</div>
            <h2 className="lp-section-title">Technology Stack</h2>
          </div>
          <div className="lp-tech-grid">
            {techStack.map(t => (
              <div key={t.label} className="lp-tech-card" style={{ "--tc": t.color }}>
                <div className="lp-tech-label" style={{ color: t.color }}>{t.label}</div>
                <div className="lp-tech-sub">{t.sub}</div>
              </div>
            ))}
          </div>

          {/* Training info */}
          <div className="lp-train-bar">
            {[
              { k: "Dataset",   v: "HajjV2 Crowd Footage" },
              { k: "Frames",    v: "~33,750" },
              { k: "Epochs",    v: "80" },
              { k: "Hardware",  v: "Kaggle T4 GPU" },
              { k: "Classes",   v: "LOW / MODERATE / HIGH" },
              { k: "F1 Score",  v: "0.80 (macro)" },
            ].map(({ k, v }) => (
              <div key={k} className="lp-train-item">
                <span className="lp-train-k">{k}</span>
                <span className="lp-train-v">{v}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FINAL CTA ── */}
      <section className="lp-cta-section">
        <div className="lp-cta-orb" />
        <div className="lp-container lp-cta-inner">
          <div className="lp-cta-tag">Ready to use</div>
          <h2 className="lp-cta-title">Analyze Your Crowd Footage</h2>
          <p className="lp-cta-desc">
            Upload a surveillance video, connect a live webcam, or stream via RTSP.<br/>
            The AI will classify crowd risk in seconds.
          </p>
          <button className="lp-cta-btn" onClick={() => navigate("/dashboard")}>
            <span>Open Dashboard</span>
            <div className="lp-cta-btn-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
              </svg>
            </div>
          </button>
          <div className="lp-footer-note">
            Swin-T + LSTM · 29.2M params
          </div>
        </div>
      </section>

    </div>
  );
}
