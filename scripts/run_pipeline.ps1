# scripts/run_pipeline.ps1
# Run the entire pipeline from raw videos to running app
# Usage: .\scripts\run_pipeline.ps1

$ErrorActionPreference = "Stop"

Write-Host "`n[1/5] Activating conda environment..." -ForegroundColor Cyan
conda activate crowd_ai

Write-Host "`n[2/5] Preparing data (frame extraction + pseudo-labels)..." -ForegroundColor Cyan
python prepare_data.py

Write-Host "`n[3/5] Training model..." -ForegroundColor Cyan
python train.py

Write-Host "`n[4/5] Evaluating model..." -ForegroundColor Cyan
python evaluate.py

Write-Host "`n[5/5] Exporting to ONNX..." -ForegroundColor Cyan
python export_onnx.py

Write-Host "`nPipeline complete!" -ForegroundColor Green
Write-Host "Start backend : uvicorn api.main:app --reload" -ForegroundColor Yellow
Write-Host "Start frontend: cd frontend && npm run dev"    -ForegroundColor Yellow