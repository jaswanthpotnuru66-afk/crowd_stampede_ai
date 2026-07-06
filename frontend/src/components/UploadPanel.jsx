import { useRef, useState } from "react";

const STEPS = ["Frame Extraction", "Swin Features", "LSTM Inference", "Risk Mapping"];

export default function UploadPanel({ videoFile, videoUrl, analyzing, progress, error, onFileSelected, onAnalyze, onExport, hasResult }) {
  const inputRef   = useRef(null);
  const [drag, setDrag] = useState(false);

  const pickFile = (file) => {
    if (file && file.type.startsWith("video/")) onFileSelected(file);
  };

  return (
    <div className="card">
      {/* Header */}
      <div className="card-header">
        <div>
          <div className="card-title">Video Analysis</div>
          <div className="card-sub">Upload surveillance footage for AI-powered risk assessment</div>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <span className="badge b-cyan">MP4</span>
          <span className="badge b-gray">AVI</span>
          <span className="badge b-gray">MOV</span>
        </div>
      </div>

      {/* Drop zone or video preview */}
      {!videoUrl ? (
        <div
          className={`drop-zone${drag ? " dragover" : ""}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); pickFile(e.dataTransfer.files[0]); }}
        >
          <div className="drop-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="2" width="20" height="20" rx="3"/>
              <polygon points="10,8 16,12 10,16"/>
            </svg>
          </div>
          <p className="drop-title">Drop surveillance footage here</p>
          <p className="drop-sub">
            Supports crowd surveillance videos in MP4, AVI, or MOV format.<br/>
            The AI model will analyze risk in seconds.
          </p>
          <button
            className="btn-primary"
            onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Browse Files
          </button>

          {/* Corner markers (surveillance aesthetic) */}
          {["top: 10px; left: 10px; border-top: 2px solid; border-left: 2px solid;",
            "top: 10px; right: 10px; border-top: 2px solid; border-right: 2px solid;",
            "bottom: 10px; left: 10px; border-bottom: 2px solid; border-left: 2px solid;",
            "bottom: 10px; right: 10px; border-bottom: 2px solid; border-right: 2px solid;"
          ].map((style, i) => (
            <div key={i} style={{
              position: "absolute", width: 14, height: 14,
              borderColor: "rgba(6,182,212,0.4)", opacity: 0.6,
              ...Object.fromEntries(
                style.split(";").filter(Boolean).map(s => {
                  const [k, v] = s.split(":").map(x => x.trim());
                  return [k.replace(/-([a-z])/g, (_, c) => c.toUpperCase()), v];
                })
              )
            }} />
          ))}
        </div>
      ) : (
        <div className="video-wrap">
          <video src={videoUrl} controls className="video-player" />
          <div className="file-meta-bar">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" strokeWidth="1.8" strokeLinecap="round">
              <rect x="2" y="2" width="20" height="20" rx="2"/><polygon points="10,8 16,12 10,16"/>
            </svg>
            <span className="meta-filename">{videoFile?.name}</span>
            <span className="meta-size">{videoFile ? (videoFile.size / 1e6).toFixed(1) + " MB" : ""}</span>
            <button className="btn-ghost-sm" onClick={() => inputRef.current?.click()}>Replace</button>
          </div>
        </div>
      )}

      <input
        ref={inputRef} type="file" accept="video/*"
        style={{ display: "none" }}
        onChange={(e) => pickFile(e.target.files[0])}
      />

      {/* Analyze / Export */}
      {videoUrl && (
        <div className="action-bar">
          <button className="btn-primary" onClick={onAnalyze} disabled={analyzing}>
            {analyzing ? (
              <><span className="spinner" /> Analyzing…</>
            ) : (
              <>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                Run AI Analysis
              </>
            )}
          </button>
          {hasResult && (
            <button className="btn-ghost" onClick={onExport}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              Export Report
            </button>
          )}
        </div>
      )}

      {/* Error */}
      {error && <div className="error-bar">⚠ {error}</div>}

      {/* Progress */}
      {analyzing && (
        <div className="progress-wrap">
          <div className="progress-header">
            <span style={{ color: "var(--accent)", fontWeight: 600 }}>{progress.label}</span>
            <span style={{ fontFamily: "var(--mono)", fontWeight: 700, color: "var(--accent)" }}>{progress.pct}%</span>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress.pct}%` }} />
          </div>
          <div className="step-pills">
            {STEPS.map((s, i) => (
              <div key={s} className={`step-pill${i < progress.step ? " done" : i === progress.step ? " active" : ""}`}>
                {i < progress.step ? "✓ " : ""}{s}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}