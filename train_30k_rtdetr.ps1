# PawPulse 30k Dataset Training Launcher (PowerShell)
# Hardware: NVIDIA GeForce RTX 5080 (16GB VRAM)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🐾 PAWPULSE: STARTING 30K DATASET TRAINING (RT-DETR-L)" -ForegroundColor Green
Write-Host "⚡ Target Device: NVIDIA GeForce RTX 5080 (device=0)" -ForegroundColor Yellow
Write-Host "📁 Dataset: C:\animal\dataset\dataset_30k\data_30k.yaml" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location -Path "C:\animal"

# Verify virtual environment python
$PythonExe = "C:\animal\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "❌ Error: Python interpreter not found at $PythonExe" -ForegroundColor Red
    exit 1
}

# Run training
& $PythonExe "C:\animal\train_30k.py"
