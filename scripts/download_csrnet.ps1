# scripts/download_csrnet.ps1
# Downloads pretrained CSRNet weights for zero-shot crowd counting.
# Run this once before training if you want better crowd count accuracy.
#
# Usage: .\scripts\download_csrnet.ps1

$OutputDir = "checkpoints"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Write-Host "Downloading pretrained CSRNet weights..." -ForegroundColor Cyan

# Use gdown to download from Google Drive
conda run -n crowd_ai python -c @"
import gdown, os
os.makedirs('checkpoints', exist_ok=True)
url = 'https://drive.google.com/uc?id=1J27C8lBOG7ZxE3VtVhcg0lNEVOAGPGBq'
out = 'checkpoints/csrnet_pretrained.pth'
gdown.download(url, out, quiet=False)
print('Downloaded to', out)
"@

Write-Host "Done. Weights saved to checkpoints\csrnet_pretrained.pth" -ForegroundColor Green
Write-Host "The model will automatically use these weights for crowd counting." -ForegroundColor Yellow