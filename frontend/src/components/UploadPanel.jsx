import { useRef, useState } from "react";

const STEPS = ["Frame extraction", "Swin features", "LSTM inference", "Risk mapping"];

export default function UploadPanel({ videoFile, videoUrl, analyzing, progress, error, onFileSelected, onAnalyze, onExport, hasResult }) {
  const inputRef     = useRef(null);
  const [dragging, setDragging] = useState(false);

  const pickFile = (file) => {
    if (file && file.type.startsWith("video/")) onFileSelected(file);
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">Video upload</div>
          <div className="card-sub">Analyze recorded surveillance footage</div>
        </div>
        <span className="badge b-blue">MP4 · AVI · MOV</span>
      </div>

      {!videoUrl ? (
        <div
          className={`drop-zone${dragging ? " dragover" : ""}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); pickFile(e.dataTransfer.files[0]); }}
        >
          <div className="drop-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <p className="drop-title">Drop your video here</p>
          <p className="drop-sub">Any crowd surveillance footage — MP4, AVI, MOV</p>
          <button className="btn-primary" onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}>
            Browse file
          </button>
        </div>
      ) : (
        <div className="video-wrap">
          <video src={videoUrl} controls className="video-player" />
          <div className="file-meta-bar">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round"><rect x="2" y="2" width="20" height="20" rx="2"/><polygon points="10,8 16,12 10,16"/></svg>
            <span className="meta-filename">{videoFile?.name}</span>
            <span className="meta-size">{videoFile ? (videoFile.size / 1e6).toFixed(1) + " MB" : ""}</span>
            <button className="btn-ghost-sm" onClick={() => inputRef.current?.click()}>Change</button>
          </div>
        </div>
      )}

      <input ref={inputRef} type="file" accept="video/*" style={{ display: "none" }}
        onChange={(e) => pickFile(e.target.files[0])} />

      {videoUrl && (
        <div className="action-bar">
          <button className="btn-primary" onClick={onAnalyze} disabled={analyzing}>
            {analyzing
              ? <><span className="spinner" /> Analyzing...</>
              : <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> Analyze video</>
            }
          </button>
          {hasResult && (
            <button className="btn-ghost" onClick={onExport}>Export report</button>
          )}
        </div>
      )}

      {error && (
        <div className="error-bar">{error}</div>
      )}

      {analyzing && (
        <div className="progress-wrap">
          <div className="progress-header">
            <span>{progress.label}</span>
            <span>{progress.pct}%</span>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress.pct}%` }} />
          </div>
          <div className="step-pills">
            {STEPS.map((s, i) => (
              <div key={s} className={`step-pill${i < progress.step ? " done" : i === progress.step ? " active" : ""}`}>
                {s}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}