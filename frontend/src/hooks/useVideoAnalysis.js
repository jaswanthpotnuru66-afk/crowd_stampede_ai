import { useState, useCallback } from "react";

const STEPS = [
  "Extracting frames...",
  "Running Swin Transformer...",
  "LSTM temporal inference...",
  "Mapping risk zones...",
];

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

    // Animate progress while waiting for server
    let stepIdx = 0;
    const stepTimer = setInterval(() => {
      if (stepIdx < STEPS.length) {
        setProgress({ pct: (stepIdx + 1) * 22, label: STEPS[stepIdx], step: stepIdx });
        stepIdx++;
      }
    }, 900);

    try {
      const form = new FormData();
      form.append("file", file);

      const res = await fetch(`/video/analyze`, { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || `Server error ${res.status}`);
      }

      const data = await res.json();
      setProgress({ pct: 100, label: "Analysis complete", step: STEPS.length });
      setTimeout(() => {
        setResult(data);
        setProgress({ pct: 0, label: "", step: -1 });
      }, 600);

    } catch (err) {
      setError(err.message);
    } finally {
      clearInterval(stepTimer);
      setAnalyzing(false);
    }
  }, [analyzing]);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setProgress({ pct: 0, label: "", step: -1 });
  }, []);

  return { analyzing, result, progress, error, analyze, reset };
}