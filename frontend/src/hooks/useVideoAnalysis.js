import { useState, useCallback } from "react";

const STEPS = [
  "Extracting frames...",
  "Running Swin Transformer...",
  "LSTM temporal inference...",
  "Mapping risk zones...",
];

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export default function useVideoAnalysis() {
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [progress, setProgress] = useState({ pct: 0, label: "", step: -1 });
  const [error, setError] = useState(null);

  const analyze = useCallback(async (file) => {
    if (!file || analyzing) return;

    setAnalyzing(true);
    setResult(null);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    let step = 0;
    setProgress({ pct: 12, label: STEPS[0], step: 0 });

    const timer = window.setInterval(() => {
      step = Math.min(step + 1, STEPS.length - 1);
      setProgress({
        pct: Math.min(92, 12 + step * 24),
        label: STEPS[step],
        step,
      });
    }, 900);

    try {
      const response = await fetch(`${API_BASE}/video/analyze`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.detail || data?.error || `Analysis failed (${response.status})`);
      }

      setProgress({ pct: 100, label: "Analysis complete", step: STEPS.length });
      setResult(data);
    } catch (err) {
      setError(err.message || "Analysis failed");
    } finally {
      window.clearInterval(timer);
      setAnalyzing(false);
      setProgress({ pct: 0, label: "", step: -1 });
    }
  }, [analyzing]);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setProgress({ pct: 0, label: "", step: -1 });
  }, []);

  return { analyzing, result, progress, error, analyze, reset };
}
