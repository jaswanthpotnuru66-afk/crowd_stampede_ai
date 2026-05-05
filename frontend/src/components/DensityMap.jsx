import React, { useRef, useEffect } from 'react'

export default function DensityMap({ riskLabel = 'LOW', density = 0 }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const W = canvas.width, H = canvas.height
    ctx.clearRect(0, 0, W, H)

    // Simple density heatmap visualization
    const cols = { LOW: [0, 230, 118], MODERATE: [255, 167, 38], HIGH: [239, 83, 80] }
    const [r, g, b] = cols[riskLabel] || cols.LOW
    const norm = Math.min(density / 300, 1)

    const grd = ctx.createRadialGradient(W/2, H/2, 0, W/2, H/2, W/2)
    grd.addColorStop(0, `rgba(${r},${g},${b},${0.3 + norm * 0.5})`)
    grd.addColorStop(1, 'rgba(0,0,0,0)')
    ctx.fillStyle = grd
    ctx.fillRect(0, 0, W, H)
  }, [riskLabel, density])

  return (
    <div className="rounded-2xl overflow-hidden relative" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <p className="absolute top-3 left-4 text-xs tracking-widest uppercase z-10" style={{ color: 'var(--text-secondary)' }}>Density Map</p>
      <canvas ref={canvasRef} width={400} height={220} className="w-full" />
    </div>
  )
}