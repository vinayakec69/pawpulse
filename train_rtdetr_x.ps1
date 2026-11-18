# 🐾 PawPulse RT-DETR-X Training Launcher for Windows PowerShell
$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "🐾 PAWPULSE RT-DETR-X FLAGSHIP TRAINING LAUNCHER" -ForegroundColor Green
Write-Host "   Hardware: NVIDIA GeForce RTX 5080 (16GB VRAM)" -ForegroundColor Yellow
Write-Host "   Architecture: RT-DETR-X (65.5M Parameters)" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan

# Configure CUDA Allocator to prevent memory fragmentation on Windows
$env:PYTORCH_CUDA_ALLOC_CONF = "garbage_collection_threshold:0.8,max_split_size_mb:128"

Set-Location "C:\animal"

# Execute training with python.exe (Device Guard / Smart App Control compliant)
& "C:\animal\.venv\Scripts\python.exe" "C:\animal\train_rtdetr_x.py" @args
