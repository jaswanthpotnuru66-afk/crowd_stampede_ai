export default function AlertBanner({ message, time, onClose }) {
  return (
    <div style={{
      background: "#200d0d",
      borderBottom: "1px solid #7f1d1d",
      padding: "10px 20px",
      display: "flex",
      alignItems: "center",
      gap: 10,
    }}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="2" strokeLinecap="round">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
        <line x1="12" y1="9" x2="12" y2="13"/>
        <line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <span style={{ fontSize: 13, color: "#fca5a5", flex: 1 }}>{message}</span>
      <span style={{ fontSize: 11, color: "#7f1d1d" }}>{time}</span>
      {onClose && (
        <button onClick={onClose} style={{ background: "none", border: "none", color: "#7f1d1d", cursor: "pointer", fontSize: 16 }}>×</button>
      )}
    </div>
  );
}