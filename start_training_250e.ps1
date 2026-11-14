# PawPulse True Resume Training Launcher (Epoch 146 -> 250 Total)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 🐾 PawPulse: Resuming RT-DETR-L from Epoch 146 to 250" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location -Path "C:\animal"
$env:PYTHONPATH = "C:\animal"

& "C:\animal\.venv\Scripts\python.exe" "C:\animal\resume_training_to_250.py"
