export default function AlertBanner({ message, sub, time, onClose }) {
  return (
    <div className="alert-banner">
      {/* Animated ping rings */}
      <div className="alert-icon-wrap">
        <div className="alert-ring" />
        <div className="alert-ring-2" />
        <span className="alert-icon">🚨</span>
      </div>

      <div className="alert-text">
        <div className="alert-title">{message}</div>
        {sub && <div className="alert-sub">{sub} · {time}</div>}
      </div>

      {/* Sound wave bars */}
      <div className="alert-soundbars">
        {[1,2,3,4,5].map(i => (
          <div key={i} className="alert-soundbar" style={{ animationDelay: `${(i-1)*0.1}s` }} />
        ))}
      </div>

      {onClose && (
        <button className="alert-close" onClick={onClose} title="Dismiss">×</button>
      )}
    </div>
  );
}