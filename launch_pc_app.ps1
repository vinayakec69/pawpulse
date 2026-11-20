# 🐾 PawPulse Native PC Desktop Application Launcher
$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "🐾 LAUNCHING PAWPULSE DESKTOP PC SOFTWARE" -ForegroundColor Green
Write-Host "   Hardware: NVIDIA GeForce RTX 5080 (CUDA 12.8)" -ForegroundColor Yellow
Write-Host "   Model: RT-DETR-X Flagship (65.5M Parameters)" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan

# Set CUDA Allocator memory policy
$env:PYTORCH_CUDA_ALLOC_CONF = "garbage_collection_threshold:0.8,max_split_size_mb:128"

Set-Location "C:\animal"

& "C:\animal\.venv\Scripts\python.exe" "C:\animal\pawpulse_app.py"
