@echo off
chcp 65001 >nul
title PawPulse Desktop Vision Sentinel - PC Suite
echo ================================================================================
echo   PAWPULSE DESKTOP PC SOFTWARE
echo   Hardware: NVIDIA GeForce RTX 5080 (CUDA Acceleration)
echo   Architecture: Flagship RT-DETR-X Transformer (65.5M Parameters)
echo ================================================================================
cd /d C:\animal
"C:\animal\.venv\Scripts\python.exe" "C:\animal\pawpulse_app.py"
pause
