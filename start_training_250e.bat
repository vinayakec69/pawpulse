@echo off
title PawPulse RT-DETR-L Training (Epoch 146 to 250 Total)
echo ==========================================================
echo  PawPulse: Resuming RT-DETR-L from Epoch 146 to 250 Total
echo  Hardware: NVIDIA RTX 5080 (Blackwell 16GB VRAM)
echo ==========================================================
echo.
cd /d "C:\animal"
"C:\animal\.venv\Scripts\python.exe" "C:\animal\resume_training_to_250.py"
pause
