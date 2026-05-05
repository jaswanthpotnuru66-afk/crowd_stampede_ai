"""
Quick CLI inference on a single video file using the TRAINED model.
"""
import argparse
import json
import torch
import cv2
import time
from pathlib import Path
from src.models.crowd_monitor import CrowdMonitor
from src.utils.checkpoint import load_model_weights
from src.utils.config import load_config
from src.data.pseudo_label_generator import PseudoLabelGenerator

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--checkpoint", default="checkpoints/best.pth", help="Model checkpoint")
    parser.add_argument("--output", default="results/infer_result.json")
    args = parser.parse_args()

    cfg = load_config()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load model
    model = CrowdMonitor(cfg)
    try:
        load_model_weights(model, args.checkpoint, map_location=device)
    except FileNotFoundError:
        print(f"ERROR: Checkpoint not found at {args.checkpoint}")
        return
        
    model = model.to(device).eval()
    
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"ERROR: File not found: {video_path}")
        return

    cap = cv2.VideoCapture(str(video_path))
    frames = []
    risk_votes = []
    
    print(f"Analyzing: {video_path} with model {args.checkpoint}")
    
    start_time = time.time()
    frame_idx = 0
    seq_len = cfg["data"]["seq_len"]
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        # Simple sequence buffer
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (cfg["data"]["img_size"], cfg["data"]["img_size"]))
        frames.append(torch.from_numpy(resized).permute(2,0,1).float() / 255.0)
        
        if len(frames) == seq_len:
            seq_tensor = torch.stack(frames).unsqueeze(0).to(device)
            with torch.no_grad():
                # Correct output unpacking from CrowdMonitor
                # model returns (density_map, risk_logits, turbulence)
                _, risk_logits, _ = model(seq_tensor)
                risk_int = risk_logits.argmax(dim=1).item()
                risk_str = ["LOW", "MODERATE", "HIGH"][risk_int]
                risk_votes.append(risk_str)
            frames.pop(0) # Sliding window
        
        frame_idx += 1
    
    cap.release()
    elapsed = time.time() - start_time
    
    if not risk_votes:
        print("Error: Video too short for sequence length.")
        return

    # Aggregate result
    from api.analyzer import majority_risk
    final_risk = majority_risk(risk_votes)
    
    result = {
        "risk_class": final_risk,
        "latency_ms": int(elapsed * 1000),
        "frames_analyzed": frame_idx,
        "status": "success"
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n[FINAL MODEL RESULT]")
    print(f"Risk class   : {final_risk}")
    print(f"Latency      : {result['latency_ms']} ms")
    print(f"Frames done  : {result['frames_analyzed']}")
    print(f"\nReport saved to {out}")

if __name__ == "__main__":
    main()