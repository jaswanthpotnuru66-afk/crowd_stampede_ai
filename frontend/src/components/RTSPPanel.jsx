import { useEffect } from "react";
import useRTSP from "../hooks/useRTSP";

export default function RTSPPanel({ onData }) {
  const { connected, liveData, error, rtspUrl, setRtspUrl, connect, disconnect } = useRTSP();

  useEffect(() => {
    if (liveData) onData?.(liveData);
  }, [liveData, onData]);

  const handleConnect = () => {
    if (!rtspUrl.trim()) return;
    connect(rtspUrl.trim());
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">CCTV live stream</div>
          <div className="card-sub">Connect to any IP camera via RTSP</div>
        </div>
        <span className={`badge ${connected ? "b-green" : "b-gray"}`}>
          {connected ? "Connected" : "Disconnected"}
        </span>
      </div>

      {!connected ? (
        <div className="rtsp-form">
          <div className="form-field">
            <label className="form-label">RTSP stream URL</label>
            <input
              className="input-field"
              type="text"
              placeholder="rtsp://admin:password@192.168.1.100:554/stream"
              value={rtspUrl}
              onChange={(e) => setRtspUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleConnect()}
            />
          </div>

          <div className="form-hint">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="1.5" strokeLinecap="round">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            Supports Hikvision, Dahua, and any ONVIF-compatible camera
          </div>

          <div className="preset-list">
            <div className="preset-label">Common formats</div>
            {[
              { label: "Hikvision",  url: "rtsp://admin:password@IP:554/h264/ch1/main/av_stream" },
              { label: "Dahua",     url: "rtsp://admin:password@IP:554/cam/realmonitor?channel=1" },
              { label: "Generic",   url: "rtsp://admin:password@IP:554/stream" },
            ].map((p) => (
              <button key={p.label} className="preset-btn" onClick={() => setRtspUrl(p.url)}>
                <span className="preset-name">{p.label}</span>
                <span className="preset-url">{p.url.slice(0, 42)}...</span>
              </button>
            ))}
          </div>

          <div className="action-bar">
            <button className="btn-primary" onClick={handleConnect} disabled={!rtspUrl.trim()}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
                <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
                <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
                <line x1="12" y1="20" x2="12.01" y2="20"/>
              </svg>
              Connect camera
            </button>
          </div>
        </div>
      ) : (
        <div>
          <div className="rtsp-connected-info">
            <div className="connected-url">
              <span className="live-dot" />
              <span className="url-text">{rtspUrl}</span>
            </div>
            {liveData && (
              <div className="live-metrics-mini">
                <div className="lm-item">
                  <span className="lm-label">Risk</span>
                  <span className={`lm-val risk-${liveData.risk_class?.toLowerCase()}`}>
                    {liveData.risk_class}
                  </span>
                </div>
                <div className="lm-item">
                  <span className="lm-label">Density</span>
                  <span className="lm-val">{Math.round((liveData.crowd_coverage || 0) * 100)}%</span>
                </div>
                <div className="lm-item">
                  <span className="lm-label">Flow</span>
                  <span className="lm-val">{liveData.flow_direction}</span>
                </div>
              </div>
            )}
          </div>
          <div className="action-bar">
            <button className="btn-danger" onClick={disconnect}>Disconnect</button>
          </div>
        </div>
      )}

      {error && <div className="error-bar">{error}</div>}
    </div>
  );
}