import { useState, useCallback, useEffect } from "react";
import { useNavigate }  from "react-router-dom";
import UploadPanel      from "../components/UploadPanel";
import LivePanel        from "../components/LivePanel";
import RTSPPanel        from "../components/RTSPPanel";
import RiskPanel        from "../components/RiskPanel";
import MetricsChart     from "../components/MetricsChart";
import MotionMetrics    from "../components/MotionMetrics";
import AlertBanner      from "../components/AlertBanner";
import useVideoAnalysis from "../hooks/useVideoAnalysis";

/* ── Icons ── */
const CameraIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
  </svg>
);
const UploadIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);
const WebcamIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <circle cx="12" cy="10" r="3"/><path d="M12 1a9 9 0 110 18A9 9 0 0112 1z"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>
  </svg>
);
const SatelliteIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <path d="M2 12a10 10 0 0110-10"/><path d="M2 12a10 10 0 0010 10"/><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 010 14.14"/>
  </svg>
);
const ShieldIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
);
const BackIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
  </svg>
);

/* ── System Clock ── */
function SystemClock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  const fmt = (n) => String(n).padStart(2, "0");
  return (
    <div className="sys-clock">
      {fmt(time.getHours())}:{fmt(time.getMinutes())}:{fmt(time.getSeconds())}
      <span style={{ marginLeft: 8, opacity: 0.4, fontSize: 10 }}>
        {time.toLocaleDateString("en-US", { month: "short", day: "numeric" })}
      </span>
    </div>
  );
}

/* ── Ticker ── */
function TickerBar({ data, analyzing, liveData }) {
  const items = [
    { label: "System",           val: "ONLINE",                                                                            cls: "green" },
    { label: "Model",            val: "Swin-T + LSTM",                                                                     cls: "cyan"  },
    { label: "Persons Detected", val: data?.count != null ? data.count.toLocaleString() : "—",                            cls: data?.count > 600 ? "red" : "cyan" },
    { label: "Risk Class",       val: data?.risk_class || "STANDBY",                                                       cls: data?.risk_class === "HIGH" ? "red" : data?.risk_class === "MODERATE" ? "amber" : "green" },
    { label: "Coverage",         val: data?.crowd_coverage != null ? (data.crowd_coverage * 100).toFixed(1) + "%" : "—",  cls: data?.crowd_coverage > 0.65 ? "red" : "cyan" },
    { label: "Turbulence",       val: data?.turbulence?.toFixed(3) || "—",                                                cls: "cyan"  },
    { label: "Frames",           val: data?.frames_analyzed?.toLocaleString() || "—",                                     cls: "cyan"  },
    { label: "Latency",          val: data?.latency_ms ? data.latency_ms + " ms" : "—",                                   cls: "green" },
    { label: "Status",           val: analyzing ? "ANALYZING" : liveData ? "LIVE FEED" : "IDLE",                          cls: analyzing ? "amber" : liveData ? "green" : "cyan" },
    { label: "Precision",        val: "81%",                                                                               cls: "green" },
    { label: "F1 Score",         val: "0.80",                                                                              cls: "green" },
  ];
  const doubled = [...items, ...items];
  return (
    <div className="ticker-bar">
      <div className="ticker-track">
        {doubled.map((item, i) => (
          <div className="ticker-item" key={i}>
            <span className="ticker-label">{item.label}</span>
            <span className={`ticker-val ${item.cls}`}>{item.val}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════
   DASHBOARD PAGE
══════════════════════════════════════ */
export default function DashboardPage() {
  const navigate                  = useNavigate();
  const [tab, setTab]             = useState("upload");
  const [videoFile, setVideoFile] = useState(null);
  const [videoUrl, setVideoUrl]   = useState(null);
  const [liveData, setLiveData]   = useState(null);
  const [alert, setAlert]         = useState(null);

  const { analyzing, result, progress, error, analyze, reset } = useVideoAnalysis();
  const displayData = tab === "upload" ? result : liveData;

  const handleFileSelected = useCallback((file) => {
    setVideoFile(file); setVideoUrl(URL.createObjectURL(file)); reset();
  }, [reset]);

  const handleAnalyze = useCallback(() => { analyze(videoFile); }, [analyze, videoFile]);

  const handleLiveData = useCallback((data) => {
    setLiveData(data);
    if (data.risk_class === "HIGH" && !alert) {
      setAlert({ message: "CRITICAL — Stampede conditions detected", sub: "Immediate crowd dispersal protocol required", time: new Date().toLocaleTimeString() });
      setTimeout(() => setAlert(null), 8000);
    }
  }, [alert]);

  const handleExport = useCallback(async () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "crowdsentinel_report.json"; a.click();
  }, [result]);

  const tabs = [
    { id: "upload", label: "Video Analysis", icon: <UploadIcon /> },
    { id: "webcam", label: "Live Webcam",    icon: <WebcamIcon /> },
    { id: "rtsp",   label: "CCTV / RTSP",   icon: <SatelliteIcon /> },
  ];

  return (
    <div className="app">

      {/* Navbar */}
      <nav className="navbar">
        <div className="nav-left">
          {/* Back to landing */}
          <button
            onClick={() => navigate("/")}
            style={{
              display: "flex", alignItems: "center", gap: 6, marginRight: 12,
              padding: "5px 10px", background: "rgba(255,255,255,0.04)",
              border: "1px solid var(--border)", borderRadius: 7,
              color: "var(--text-lo)", fontSize: 11, fontWeight: 600, cursor: "pointer",
              transition: "all .2s",
            }}
            onMouseEnter={e => e.currentTarget.style.color = "var(--text-hi)"}
            onMouseLeave={e => e.currentTarget.style.color = "var(--text-lo)"}
          >
            <BackIcon /> Back
          </button>

          <div className="brand">
            <div className="brand-logo"><CameraIcon /></div>
            <span className="brand-name">Crowd<span className="brand-accent">Sentinel</span></span>
          </div>

          <div className="nav-links">
            {tabs.map(t => (
              <button
                key={t.id}
                className={`nav-link${tab === t.id ? " active" : ""}`}
                onClick={() => setTab(t.id)}
              >
                {t.icon}{t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="nav-right">
          <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 12px", background: "rgba(34,197,94,0.07)", border: "1px solid rgba(34,197,94,0.18)", borderRadius: 8, color: "var(--risk-low)", fontSize: 11, fontWeight: 600 }}>
            <ShieldIcon /><span>AI Protected</span>
          </div>
          <SystemClock />
          <div className="status-pill">
            <div className={`status-dot ${analyzing ? "processing" : liveData ? "online" : "idle"}`} />
            <span className="status-text">
              {analyzing ? "Analyzing…" : liveData ? "Live Feed Active" : "System Ready"}
            </span>
          </div>
        </div>
      </nav>

      {/* Ticker */}
      <TickerBar data={displayData} analyzing={analyzing} liveData={liveData} />

      {/* Alert */}
      {alert && (
        <AlertBanner
          message={alert.message}
          sub={alert.sub}
          time={alert.time}
          onClose={() => setAlert(null)}
        />
      )}

      {/* Grid */}
      <div className="main-grid">
        <div className="left-col">
          {tab === "upload" && (
            <UploadPanel
              videoFile={videoFile}
              videoUrl={videoUrl}
              analyzing={analyzing}
              progress={progress}
              error={error}
              hasResult={!!result}
              onFileSelected={handleFileSelected}
              onAnalyze={handleAnalyze}
              onExport={handleExport}
            />
          )}
          {tab === "webcam" && <LivePanel onData={handleLiveData} />}
          {tab === "rtsp"   && <RTSPPanel onData={handleLiveData} />}

          {displayData && (
            <>
              <RiskPanel data={displayData} />
              <MetricsChart
                history={displayData.count_history || []}
                riskClass={displayData.risk_class}
              />
            </>
          )}
        </div>

        <div className="right-col">
          <MotionMetrics data={displayData} />
        </div>
      </div>

    </div>
  );
}
