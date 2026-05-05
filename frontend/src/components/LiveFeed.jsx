import React, { useRef } from 'react'

export default function LiveFeed({ onStart, onStop, connected }) {
  const videoRef = useRef(null)
  return (
    <div className="rounded-2xl overflow-hidden relative" style={{ background: '#000', border: '1px solid var(--border)' }}>
      <video ref={videoRef} className="w-full" autoPlay muted playsInline />
      <div className="absolute bottom-3 left-3 flex gap-2">
        <button onClick={() => onStart(videoRef)}
          className="px-4 py-2 rounded-lg text-sm font-medium"
          style={{ background: 'rgba(0,230,118,0.2)', color: '#00e676', border: '1px solid #00e676' }}>
          ▶ Start Camera
        </button>
        <button onClick={onStop}
          className="px-4 py-2 rounded-lg text-sm font-medium"
          style={{ background: 'rgba(239,83,80,0.15)', color: '#ef5350', border: '1px solid #ef5350' }}>
          ■ Stop
        </button>
      </div>
      <div className={`absolute top-3 right-3 w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-gray-600'}`} />
    </div>
  )
}