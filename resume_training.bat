@echo off
title PawPulse RT-DETR-L Training Resumption
cd /d C:\animal
set PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.8,max_split_size_mb:128
echo ==========================================================
echo 🐾 PAWPULSE: RESUMING 30K DATASET TRAINING (RT-DETR-L)
echo ⚡ GPU: NVIDIA GeForce RTX 5080 (16GB VRAM)
echo 🛡️ Memory Safety: batch=2, workers=4, cache=False
echo ==========================================================
.\.venv\Scripts\python.exe train_30k.py
pause
