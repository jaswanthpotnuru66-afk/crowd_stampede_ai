import { useState, useCallback } from "react";

const STEPS = [
  "Extracting frames...",
  "Running Swin Transformer...",
  "LSTM temporal inference...",
  "Mapping risk zones...",
];

/* ── Hardcoded demo result (realistic HajjV2-style output) ── */
const MOCK_RESULT = {
  risk_class: "HIGH",
  risk_probs: [0.05, 0.18, 0.77],

  count: 742,
  crowd_coverage: 0.74,
  dense_area_ratio: 0.58,
  avg_speed: 3.21,
  turbulence: 0.812,
  velocity_variance: 0.693,
  flow_direction: "Chaotic",
  density_growth: "Rapid",
  high_risk_frame_pct: 68,
  latency_ms: 312,
  frames_analyzed: 874,

  count_history: [
    210, 240, 275, 310, 365, 420, 480, 530, 575, 610,
    638, 655, 672, 690, 705, 718, 728, 735, 740, 742,
  ],

  video_info: {
    filename: "crowd_footage.mp4",
    duration_s: 29,
    fps: 30,
  },

  events: [
    { message: "Crowd density exceeded 40% threshold",      timestamp: "00:04", color: "#f97316" },
    { message: "Turbulence spike detected — chaotic motion", timestamp: "00:11", color: "#ef4444" },
    { message: "HIGH risk classification triggered",         timestamp: "00:18", color: "#ef4444" },
    { message: "Dense area ratio exceeded 50%",              timestamp: "00:22", color: "#ef4444" },
    { message: "Velocity variance critical — 0.693",         timestamp: "00:26", color: "#dc2626" },
  ],
};

export default function useVideoAnalysis() {
  const [analyzing, setAnalyzing] = useState(false);
  const [result,    setResult]    = useState(null);
  const [progress,  setProgress]  = useState({ pct: 0, label: "", step: -1 });
  const [error,     setError]     = useState(null);

  const analyze = useCallback(async (file) => {
    if (!file || analyzing) return;
    setAnalyzing(true);
    setResult(null);
    setError(null);

    /* Animate through each step with realistic timing */
    for (let i = 0; i < STEPS.length; i++) {
      setProgress({ pct: (i + 1) * 22, label: STEPS[i], step: i });
      await new Promise((r) => setTimeout(r, 900));
    }

    setProgress({ pct: 100, label: "Analysis complete", step: STEPS.length });

    await new Promise((r) => setTimeout(r, 600));

    setResult(MOCK_RESULT);
    setProgress({ pct: 0, label: "", step: -1 });
    setAnalyzing(false);
  }, [analyzing]);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setProgress({ pct: 0, label: "", step: -1 });
  }, []);

  return { analyzing, result, progress, error, analyze, reset };
}