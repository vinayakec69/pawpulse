# PawPulse 30k Dataset Training Launcher (PowerShell)
# Hardware: NVIDIA GeForce RTX 5080 (16GB VRAM)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🐾 PAWPULSE: STARTING/RESUMING 30K DATASET TRAINING (RT-DETR-L)" -ForegroundColor Green
Write-Host "⚡ Target Device: NVIDIA GeForce RTX 5080 (device=0)" -ForegroundColor Yellow
Write-Host "📁 Dataset: C:\animal\dataset\dataset_30k\data_30k.yaml" -ForegroundColor White
Write-Host "🛡️ VRAM Safety: batch=2, workers=4, cache=False, max_split_size_mb:128" -ForegroundColor Magenta
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location -Path "C:\animal"

$env:PYTORCH_CUDA_ALLOC_CONF = "garbage_collection_threshold:0.8,max_split_size_mb:128"

# Verify virtual environment python
$PythonExe = "C:\animal\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "❌ Error: Python interpreter not found at $PythonExe" -ForegroundColor Red
    exit 1
}

# Run training
& $PythonExe "C:\animal\train_30k.py"
