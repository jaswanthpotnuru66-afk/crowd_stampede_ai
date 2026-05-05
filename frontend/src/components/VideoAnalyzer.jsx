import React, { useState } from 'react'
import { Upload, Play, BarChart3, AlertTriangle } from 'lucide-react'

export default function VideoAnalyzer() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const handleFileChange = (e) => {
    setFile(e.target.files?.[0])
    setError(null)
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a video file')
      return
    }

    setLoading(true)
    setError(null)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/api/analyze-video', {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      
      if (data.success) {
        setResults(data)
      } else {
        setError(data.error || 'Analysis failed')
      }
    } catch (err) {
      setError(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const getStats = () => {
    if (!results?.results) return null
    const densities = results.results.map(r => r.density)
    const avg = (densities.reduce((a, b) => a + b, 0) / densities.length).toFixed(1)
    const max = Math.max(...densities).toFixed(1)
    const highRiskFrames = results.results.filter(r => r.risk_label === 'HIGH').length
    
    return { avg, max, highRiskFrames }
  }

  const stats = getStats()

  return (
    <div className="rounded-2xl p-6" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
      <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
        <Upload size={20} style={{ color: '#60a5fa' }} />
        Analyze Video
      </h2>

      {/* Upload Section */}
      <div className="mb-4">
        <label className="block text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>
          Select MP4 video file
        </label>
        <input
          type="file"
          accept="video/mp4"
          onChange={handleFileChange}
          disabled={loading}
          className="w-full p-2 rounded-lg text-sm"
          style={{ background: 'var(--bg-input)', border: '1px solid var(--border)', color: 'var(--text)' }}
        />
        {file && <p className="text-xs mt-2" style={{ color: '#60a5fa' }}>Selected: {file.name}</p>}
      </div>

      <button
        onClick={handleUpload}
        disabled={loading || !file}
        className={`w-full py-2 rounded-lg font-semibold flex items-center justify-center gap-2 transition ${
          loading || !file ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-80'
        }`}
        style={{ background: loading ? '#666' : '#60a5fa', color: '#000' }}
      >
        {loading ? 'Analyzing...' : <><Play size={16} /> Analyze</> }
      </button>

      {error && (
        <div className="mt-4 p-3 rounded-lg bg-red-900/30 border border-red-600 text-sm" style={{ color: '#ff6b6b' }}>
          {error}
        </div>
      )}

      {/* Results Summary */}
      {results && stats && (
        <div className="mt-6 pt-6" style={{ borderTop: '1px solid var(--border)' }}>
          <p className="text-xs tracking-widest uppercase mb-3" style={{ color: 'var(--text-secondary)' }}>
            Analysis Results
          </p>
          
          <div className="space-y-2 mb-4">
            {[
              ['Total Frames', results.total_frames],
              ['Avg Density', `${stats.avg} persons/m²`],
              ['Max Density', `${stats.max} persons/m²`],
              ['High-Risk Frames', `${stats.highRiskFrames} / ${results.total_frames}`],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between py-1.5 text-sm">
                <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
                <span className="font-mono" style={{ color: '#60a5fa' }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Frame-by-frame table */}
          <div className="mt-4">
            <p className="text-xs mb-2 tracking-widest uppercase" style={{ color: 'var(--text-secondary)' }}>
              Sample Results (every 10 frames)
            </p>
            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
              <table className="w-full text-xs" style={{ color: 'var(--text-secondary)' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th className="text-left py-1">Frame</th>
                    <th className="text-left py-1">Time</th>
                    <th className="text-right py-1">Density</th>
                    <th className="text-center py-1">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {results.results.filter((_, i) => i % 10 === 0).map((r) => (
                    <tr key={r.frame} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td className="py-1">{r.frame}</td>
                      <td className="py-1">{r.timestamp}s</td>
                      <td className="text-right py-1 font-mono">{r.density}</td>
                      <td className="text-center py-1">
                        <span
                          className="px-2 py-0.5 rounded text-xs font-bold"
                          style={{
                            background:
                              r.risk_label === 'HIGH'
                                ? 'rgba(255, 0, 0, 0.2)'
                                : r.risk_label === 'MODERATE'
                                ? 'rgba(255, 165, 0, 0.2)'
                                : 'rgba(0, 200, 0, 0.2)',
                            color:
                              r.risk_label === 'HIGH'
                                ? '#ff6b6b'
                                : r.risk_label === 'MODERATE'
                                ? '#ffa500'
                                : '#51cf66',
                          }}
                        >
                          {r.risk_label}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
