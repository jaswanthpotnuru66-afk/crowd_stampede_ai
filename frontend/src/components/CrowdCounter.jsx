import React from 'react'

export default function CrowdCounter({ count = 0, fps = 0 }) {
  return (
    <div className="rounded-2xl p-5" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <p className="text-xs tracking-widest uppercase mb-1" style={{ color: 'var(--text-secondary)' }}>Estimated Count</p>
      <p className="mono text-5xl font-semibold" style={{ color: 'var(--text-primary)' }}>
        {Math.round(count).toLocaleString()}
      </p>
      <p className="mono text-xs mt-2" style={{ color: 'var(--text-secondary)' }}>{fps.toFixed(1)} fps</p>
    </div>
  )
}