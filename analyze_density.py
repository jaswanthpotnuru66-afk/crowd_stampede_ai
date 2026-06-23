import os
import cv2
import numpy as np
from pathlib import Path
from src.data.pseudo_label_generator import PseudoLabelGenerator

def analyze_videos():
    video_dir = Path("data/hajjv2/videos")
    videos = list(video_dir.glob("*.mp4"))
    
    gen = PseudoLabelGenerator()
    results = []
    
    for vid_path in videos:
        cap = cv2.VideoCapture(str(vid_path))
        coverage_sum = 0
        frame_count = 0
        
        # Analyze first 50 frames to get a good average
        while cap.isOpened() and frame_count < 50:
            ret, frame = cap.read()
            if not ret:
                break
                
            density, _ = gen.get_density_map(frame)
            flow = gen.get_optical_flow(frame)
            metrics = gen.get_risk_metrics(density, flow)
            
            coverage_sum += metrics["crowd_coverage"]
            frame_count += 1
            
        cap.release()
        
        avg_coverage = coverage_sum / max(1, frame_count)
        results.append((vid_path.name, avg_coverage))
        print(f"Analyzed {vid_path.name}: coverage={avg_coverage:.4f}")
        
    # Sort by coverage
    results.sort(key=lambda x: x[1])
    
    # Split into 3 chunks
    n = len(results)
    low = [r[0] for r in results[:n//3]]
    moderate = [r[0] for r in results[n//3:2*n//3]]
    high = [r[0] for r in results[2*n//3:]]
    
    print("\n--- NEW MAPPINGS ---")
    print(f"LOW: {low}")
    print(f"MODERATE: {moderate}")
    print(f"HIGH: {high}")

if __name__ == '__main__':
    analyze_videos()
