import { useRef, useEffect } from "react";
import useWebSocket from "../hooks/useWebSocket";

const WS_URL = "ws://localhost:8000/live/ws";

export default function LivePanel({ onData }) {
  const { connected, liveData, error, connect, disconnect } = useWebSocket(WS_URL);
  const videoRef = useRef(null);

  useEffect(() => {
    if (liveData) onData?.(liveData);
  }, [liveData, onData]);

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">Webcam live stream</div>
          <div className="card-sub">Analyze live footage from your device camera</div>
        </div>
        <span className={`badge ${connected ? "b-green" : "b-gray"}`}>
          {connected ? "Live" : "Offline"}
        </span>
      </div>

      <div className="feed-box">
        {connected ? (
          <>
            <video ref={videoRef} autoPlay muted playsInline className="feed-video"
              style={{ width: "100%", display: "block", borderRadius: 6 }} />
            {liveData?.density_map_b64 && (
              <img
                src={`data:image/jpeg;base64,${liveData.density_map_b64}`}
                className="density-overlay"
                alt="density"
              />
            )}
            <div className="feed-tag-tl">CAM · WEBCAM</div>
            <div className="feed-tag-tr">
              <span className="live-dot" /> REC
            </div>
            {liveData && (
              <>
                <div className={`feed-tag-br risk-${liveData.risk_class?.toLowerCase()}`}>
                  {liveData.risk_class} RISK
                </div>
              </>
            )}
          </>
        ) : (
          <div className="feed-placeholder">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#334155" strokeWidth="1.2" strokeLinecap="round">
              <path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2"/>
            </svg>
            <p style={{ fontSize: 12, color: "#475569", marginTop: 8 }}>Camera not started</p>
          </div>
        )}
      </div>

      {error && <div className="error-bar">{error}</div>}

      <div className="action-bar">
        {!connected ? (
          <button className="btn-primary" onClick={connect}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2"/>
            </svg>
            Start webcam
          </button>
        ) : (
          <button className="btn-danger" onClick={disconnect}>
            Stop stream
          </button>
        )}
      </div>
    </div>
  );
}