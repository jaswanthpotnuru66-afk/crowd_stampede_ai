# scripts/setup.ps1
# First-time setup: creates conda env and installs all dependencies
# Usage: .\scripts\setup.ps1

Write-Host "Creating conda environment..." -ForegroundColor Cyan
conda env create -f environment.yml

Write-Host "Activating environment..." -ForegroundColor Cyan
conda activate crowd_ai

Write-Host "Installing PyTorch with CUDA 11.8..." -ForegroundColor Cyan
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

Write-Host "Installing remaining requirements..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
Set-Location frontend
npm install
Set-Location ..

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "Next: copy your .mp4 videos into data\hajjv2\videos\" -ForegroundColor Yellow
Write-Host "Then: .\scripts\run_pipeline.ps1"                      -ForegroundColor Yellow