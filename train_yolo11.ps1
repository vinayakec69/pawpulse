# PawPulse YOLO11-X 150-Epoch Maximum Accuracy Training Launcher (PowerShell)
# Hardware: NVIDIA GeForce RTX 5080 (16GB VRAM)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🐾 PAWPULSE: STARTING YOLO11-X 150-EPOCH HIGH-ACCURACY TRAINING" -ForegroundColor Green
Write-Host "⚡ Target Device: NVIDIA GeForce RTX 5080 (device=0)" -ForegroundColor Yellow
Write-Host "📁 Dataset: C:\animal\dataset\dataset_30k\data_30k.yaml" -ForegroundColor White
Write-Host "🎯 Target: 150 Epochs | batch=8 | imgsz=1280 | YOLO11-X (Flagship)" -ForegroundColor Magenta
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location -Path "C:\animal"

$env:PYTORCH_CUDA_ALLOC_CONF = "garbage_collection_threshold:0.8,max_split_size_mb:128"

$PythonExe = "C:\animal\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "❌ Error: Python interpreter not found at $PythonExe" -ForegroundColor Red
    exit 1
}

& $PythonExe "C:\animal\train_yolo11.py"
