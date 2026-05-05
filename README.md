# CrowdSentinel AI 🚨

> Real-time crowd stampede risk prediction using Swin Transformer + LSTM — trained on HajjV2, deployed via FastAPI + React.

<img width="1881" height="895" alt="Screenshot 2026-04-21 095649" src="https://github.com/user-attachments/assets/82d7835f-e565-43d0-9f02-b1373024b918" />


## What It Does

CrowdSentinel AI continuously analyzes surveillance footage and predicts stampede risk **before** dangerous conditions become visible. It combines spatial understanding (Swin Transformer) with temporal pattern modeling (LSTM) to detect the characteristic build-up — rising density, increasing turbulence, slowing velocity — that precedes crowd crushes.

**Key differentiator:** Unlike frame-by-frame density estimators, CrowdSentinel models *how the crowd is changing over time*, providing 3.9 seconds of advance warning on average vs. 0.8 seconds for threshold-based systems.

---

## Results

| Metric | CrowdSentinel AI | CSRNet Baseline | MCNN Baseline |
|--------|-----------------|-----------------|---------------|
| MAE (density) ↓ | **0.071** | 0.094 | 0.118 |
| RMSE ↓ | **0.118** | 0.151 | 0.184 |
| Risk F1 (macro) | **0.80** | — | — |
| HIGH risk precision | **0.81** | — | — |
| Mean advance warning | **3.9s** | 1.2s | — |
| False alarm rate | **8%** | 18% | 22% |
| Inference (ONNX, RTX 3060) | **16.1 FPS** | — | — |

---

## Demo


<img width="1865" height="795" alt="Screenshot 2026-04-19 171952" src="https://github.com/user-attachments/assets/177a1e3e-0e00-4dc7-a2ec-24793bc50440" />

<img width="1856" height="883" alt="Screenshot 2026-04-19 170609" src="https://github.com/user-attachments/assets/952c8bb3-485b-438e-9c4b-b341964a8d58" />

<img width="1874" height="771" alt="Screenshot 2026-04-21 095702" src="https://github.com/user-attachments/assets/f952a321-7760-4cfa-81c8-847f1f20a388" />

---

## Architecture

```
Video Input (MP4 / Webcam / RTSP)
        │
        ▼
┌─────────────────────┐
│   Frame Buffer      │  ← circular queue, 8 frames
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│   Swin-Tiny         │  ← spatial features (768-dim → 512-dim projection)
│   Transformer       │     ImageNet-21k pretrained
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│   2-Layer LSTM      │  ← temporal sequence modeling (8 frames × 512-dim)
│   hidden=512        │
└─────────────────────┘
        │
   ┌────┴────┐────────┐
   ▼         ▼        ▼
Density    Risk     Turbulence
(scalar)  (3-class) (scalar)
```

**Model size:** 29.2M parameters | 110MB ONNX  
**Training:** 80 epochs, AdamW, cosine annealing, Kaggle T4 GPU (~4.5 hrs)  
**Dataset:** HajjV2 — 10 crowd surveillance videos, ~33,750 frames  

---

## Risk Classification

| Level | Indicator | Operator Action |
|-------|-----------|----------------|
| 🟢 LOW | Green banner | Monitor normally |
| 🟡 MODERATE | Amber banner | Alert field personnel, prepare exit routes |
| 🔴 HIGH | Red pulsing + countdown timer | Immediate crowd dispersal protocol |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Deep Learning | PyTorch 2.1, TIMM (Swin-Tiny) |
| Inference | ONNX Runtime GPU |
| Backend | FastAPI, Uvicorn, WebSocket |
| Frontend | React 18, Vite, Recharts, Tailwind CSS |
| Video Processing | OpenCV 4.8 |
| Training Infra | Kaggle T4 GPU (free tier) |

---

## Project Structure

```
crowd_stampede_ai/
├── api/                    # FastAPI backend
│   ├── main.py             # App entry point
│   ├── routes.py           # WebSocket + REST endpoints
│   ├── analyzer.py         # Inference pipeline
│   └── frame_buffer.py     # Async circular frame buffer
├── src/
│   ├── models/
│   │   ├── swin_backbone.py    # Swin-Tiny + projection head
│   │   ├── lstm_temporal.py    # 2-layer LSTM + output heads
│   │   └── crowd_monitor.py    # Combined CrowdMonitor model
│   ├── data/
│   │   ├── extract_frames.py   # Video → JPEG frames
│   │   ├── pseudo_label_generator.py  # MOG2 + optical flow labels
│   │   └── dataset.py          # CrowdSequenceDataset
│   └── engine/
│       ├── trainer.py          # Mixed precision training loop
│       ├── evaluator.py        # MAE, RMSE, F1 evaluation
│       └── inferencer.py       # ONNX/PyTorch inference wrapper
├── frontend/               # React dashboard
│   └── src/components/     # LiveFeed, RiskPanel, AlertBanner, etc.
├── configs/                # YAML training/inference configs
├── exports/                # crowd_model.onnx (via Git LFS)
├── checkpoints/            # best.pth (via Git LFS)
├── train.py                # Training entry point
├── export_onnx.py          # PyTorch → ONNX export
└── prepare_data.py         # End-to-end data preparation
```

---

## Quick Start

### Prerequisites
- Python 3.11
- Node.js 18+
- NVIDIA GPU with CUDA 12.1 (CPU works for offline analysis)

### 1. Setup environment

```bash
git clone https://github.com/jaswanthpotnuru66-afk/crowd_stampede_ai.git
cd crowd_stampede_ai

conda env create -f environment.yml
conda activate crowd_ai
```

### 2. Prepare data

Place HajjV2 MP4 files in `data/hajjv2/videos/`, then:

```bash
python prepare_data.py
```

### 3. Train

```bash
python train.py
```

Or skip training — download the pretrained ONNX model from [Releases](https://github.com/jaswanthpotnuru66-afk/crowd_stampede_ai/releases/tag/v1.0.0).

### 4. Export to ONNX

```bash
python export_onnx.py --checkpoint checkpoints/best.pth
```

### 5. Run the system

```bash
# Terminal 1 — Backend
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173**

---

## Supported Input Sources

| Source | How to Use |
|--------|-----------|
| Recorded video | Upload MP4/AVI via dashboard |
| Live webcam | Click "Start Webcam" in dashboard |
| IP camera (RTSP) | Set `source: rtsp://user:pass@ip:554/stream` in `configs/infer.yaml` |

---

## Pseudo-Label Generation

No manually annotated ground truth required. Labels are derived automatically:

1. **MOG2 background subtraction** → crowd coverage (foreground pixel ratio)
2. **Farneback optical flow** → average speed + velocity variance (turbulence)
3. **Rule-based scoring** → LOW / MODERATE / HIGH risk class

This makes the system fully trainable on any crowd video dataset without annotation effort.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `OMP: Error #15` on Windows | Run `set KMP_DUPLICATE_LIB_OK=TRUE` before Python |
| No CUDA provider in ONNX Runtime | Install `onnxruntime-gpu` and CUDA 12.1 |
| Dashboard shows "Offline" | Start the uvicorn backend first |
| FPS below 5 on GPU | Model is running on CPU — verify CUDA provider |

---

## Citation

If you use this work, please cite:

```bibtex
@project{crowdsentinel2024,
  title     = {CrowdSentinel AI: Real-Time Crowd Stampede Risk Prediction},
  author    = {Jaswanth Potnuru},
  year      = {2024},
  institute = {GITAM School of Science},
  url       = {https://github.com/jaswanthpotnuru66-afk/crowd_stampede_ai}
}
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

> ⚠️ CrowdSentinel AI is a decision-support tool. All crowd management decisions remain the responsibility of qualified security personnel.
