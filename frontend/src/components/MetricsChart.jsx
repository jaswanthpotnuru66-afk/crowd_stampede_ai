import { useEffect, useRef } from "react";

export default function MetricsChart({ history = [], riskClass }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current || history.length < 2) return;
    const W = 500, H = 52;
    const mn = Math.min(...history);
    const mx = Math.max(...history);
    const pts = history.map((v, i) => {
      const x = (i / (history.length - 1)) * W;
      const y = H - ((v - mn) / (mx - mn + 1)) * (H - 8) - 4;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    const color = riskClass === "HIGH" ? "#f87171" : riskClass === "MODERATE" ? "#fbbf24" : "#4ade80";
    svgRef.current.innerHTML = `<polyline points="${pts.join(" ")}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linejoin="round"/>`;
  }, [history, riskClass]);

  return (
    <div className="card" style={{ padding: "14px" }}>
      <div className="mini-title" style={{ marginBottom: 8 }}>Crowd count — over time</div>
      <svg
        ref={svgRef}
        width="100%" height="52"
        viewBox="0 0 500 52"
        preserveAspectRatio="none"
        style={{ display: "block", background: "#090d18", borderRadius: 6 }}
      />
    </div>
  );
}