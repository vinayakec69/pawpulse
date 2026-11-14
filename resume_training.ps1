# PowerShell Resume Training Launcher for RT-DETR-L on RTX 5080
$ErrorActionPreference = "Stop"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "🔄 Resuming RT-DETR-L Training from Last Checkpoint" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location "C:\animal"
$venvPy = "C:\animal\.venv\Scripts\python.exe"

if (-not (Test-Path $venvPy)) {
    Write-Host "[!] Virtual environment not found at $venvPy" -ForegroundColor Red
    exit 1
}

$lastPt = "C:\animal\runs\shelter_monitoring\train_rtdetr_l_cctv_1536\weights\last.pt"
if (-not (Test-Path $lastPt)) {
    Write-Host "[!] Checkpoint not found at: $lastPt" -ForegroundColor Red
    exit 1
}

Write-Host "[+] Found checkpoint: $lastPt" -ForegroundColor Green
Write-Host "[+] Resuming training on RTX 5080..." -ForegroundColor Cyan

& $venvPy resume_training.py
