# PowerShell Turnkey Setup and Training Launcher for RTX 5080 (Blackwell sm_120)
$ErrorActionPreference = "Stop"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "🐾 Updating PyTorch to CUDA 12.8 Nightly for RTX 5080 (sm_120)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location "C:\animal"
$venvPy = "C:\animal\.venv\Scripts\python.exe"

# 1. Install PyTorch Nightly with CUDA 12.8 (Native sm_120 / Blackwell Support)
Write-Host "[+] Installing PyTorch Nightly (CUDA 12.8) for RTX 5080..." -ForegroundColor Green
& $venvPy -m pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128 --force-reinstall

# 2. Re-verify Ultralytics
Write-Host "[+] Checking Ultralytics..." -ForegroundColor Green
& $venvPy -m pip install ultralytics

# 3. Test RTX 5080 execution
Write-Host "`n[+] Verifying RTX 5080 execution on sm_120..." -ForegroundColor Green
& $venvPy -c "import torch; print(f'>>> PyTorch Version: {torch.__version__}'); print(f'>>> GPU: {torch.cuda.get_device_name(0)}'); print(f'>>> Arch list: {torch.cuda.get_arch_list()}'); x = torch.randn(1, device='cuda'); print('>>> CUDA Tensor Allocation: SUCCESS!')"

# 4. Launch Training
Write-Host "`n🚀 Launching CCTV-Optimized RT-DETR-L Training (imgsz=1536, batch=2)..." -ForegroundColor Cyan
& $venvPy train.py
