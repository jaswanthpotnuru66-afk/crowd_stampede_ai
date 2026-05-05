import { useState, useCallback } from "react";
import UploadPanel from "./components/UploadPanel";
import LivePanel from "./components/LivePanel";
import RTSPPanel from "./components/RTSPPanel";
import RiskPanel from "./components/RiskPanel";
import MetricsChart from "./components/MetricsChart";
import MotionMetrics from "./components/MotionMetrics";
import AlertBanner from "./components/AlertBanner";
import useVideoAnalysis from "./hooks/useVideoAnalysis";

export default function App() {
  const [tab, setTab] = useState("upload");   // "upload" | "webcam" | "rtsp"
  const [videoFile, setVideoFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [liveData, setLiveData] = useState(null);
  const [alert, setAlert] = useState(null);

  const { analyzing, result, progress, error, analyze, reset } = useVideoAnalysis();

  const displayData = tab === "upload" ? result : liveData;

  const handleFileSelected = useCallback((file) => {
    setVideoFile(file);
    setVideoUrl(URL.createObjectURL(file));
    reset();
  }, [reset]);

  const handleAnalyze = useCallback(() => {
    analyze(videoFile);
  }, [analyze, videoFile]);

  const handleLiveData = useCallback((data) => {
    setLiveData(data);
    if (data.risk_class === "HIGH" && !alert) {
      setAlert({ message: "High risk detected — immediate action required", time: new Date().toLocaleTimeString() });
      setTimeout(() => setAlert(null), 6000);
    }
  }, [alert]);

  const handleExport = useCallback(async () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "crowd_report.json"; a.click();
  }, [result]);

  return (
    <div className="app">
      {/* Navbar */}
      <nav className="navbar">
        <div className="nav-left">
          <span className="brand">Crowd<span className="brand-accent">Sentinel</span></span>
          <div className="nav-links">
            <button className={`nav-link ${tab === "upload" ? "active" : ""}`} onClick={() => setTab("upload")}>
              Video upload
            </button>
            <button className={`nav-link ${tab === "webcam" ? "active" : ""}`} onClick={() => setTab("webcam")}>
              Webcam
            </button>
            <button className={`nav-link ${tab === "rtsp" ? "active" : ""}`} onClick={() => setTab("rtsp")}>
              CCTV / RTSP
            </button>
          </div>
        </div>
        <div className="nav-right">
          <div className={`status-dot ${analyzing ? "processing" : liveData ? "online" : "idle"}`} />
          <span className="status-text">
            {analyzing ? "Analyzing..." : liveData ? "Live" : "Ready"}
          </span>
        </div>
      </nav>

      {/* Alert */}
      {alert && (
        <AlertBanner
          message={alert.message}
          time={alert.time}
          onClose={() => setAlert(null)}
        />
      )}

      {/* Main layout */}
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

          {tab === "webcam" && (
            <LivePanel onData={handleLiveData} />
          )}

          {tab === "rtsp" && (
            <RTSPPanel onData={handleLiveData} />
          )}

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