# Launch Animal Welfare Monitor with RT-DETR-L + ByteTrack
param(
    [string]$Source = "0",
    [string]$Weights = "C:\animal\best.pt"
)

Set-Location "C:\animal"

if (Test-Path "C:\animal\.venv\Scripts\Activate.ps1") {
    & "C:\animal\.venv\Scripts\Activate.ps1"
}

# Fallback to pretrained rtdetr-l.pt if trained weights don't exist yet
if (-not (Test-Path $Weights)) {
    Write-Host "[*] Custom weights not found yet. Falling back to base 'rtdetr-l.pt' for demo/test..." -ForegroundColor Yellow
    $Weights = "rtdetr-l.pt"
}

Write-Host "🎥 Starting Animal Monitor on Source: $Source using Model: $Weights" -ForegroundColor Cyan
python animal_monitor.py --weights $Weights --source $Source
