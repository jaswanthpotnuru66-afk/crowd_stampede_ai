# CrowdSentinel AI

Swin-LSTM crowd density estimation and stampede risk prediction.

## Quick Start
```bash
# 1. Setup
.\scripts\setup.ps1
.\scripts\download_csrnet.ps1

# 2. Prepare data (extracts frames + pseudo labels)
python prepare_data.py

# 3. Train
python train.py

# 4. Export for fast inference
python export_onnx.py

# 5. Start API
uvicorn api.main:app --host 0.0.0.0 --port 8000

# 6. Start UI
cd frontend && npm install && npm run dev
```

Open http://localhost:5173

## Architecture
- **Backbone**: Swin-Tiny (pretrained ImageNet-1K)
- **Temporal**: 2-layer LSTM, hidden=512
- **Pseudo labels**: motion-density maps calibrated with YOLO person counts when available
- **Risk logic**: zone-based hotspot growth, not just global crowd count
- **Dataset**: HajjV2 (10 crowd videos)
- **Inference**: ONNX Runtime GPU (~15 FPS on RTX 3060)

## Risk Classes
| Class | Density (persons/m²) |
|-------|----------------------|
| LOW | < 2.0 |
| MODERATE | 2.0 – 6.0 |
| HIGH | > 6.0 |
