"""
PawPulse: True Resume of RT-DETR-L Training from Epoch 146 to 250 Total
Preserves:
- 54.3% mAP50 base accuracy
- Full AdamW optimizer state & momentum
- Full Exponential Moving Average (EMA) weights
- Continues directly: Epoch 146 -> 250 (105 epochs)
"""

import os
import sys
import torch
from ultralytics import RTDETR

def main():
    print("=" * 68)
    print("🐾 PAWPULSE: TRUE RESUME OF TRAINING (EPOCH 146 -> 250 TOTAL)")
    print("=" * 68)

    if not torch.cuda.is_available():
        print("❌ Error: CUDA GPU not detected!")
        sys.exit(1)

    gpu_name = torch.cuda.get_device_name(0)
    print(f"⚡ GPU: {gpu_name}")
    print(f"🔥 PyTorch: {torch.__version__} | CUDA: {torch.version.cuda}")

    last_pt = r"C:\animal\runs\shelter_monitoring\train_rtdetr_l_cctv_1536\weights\last.pt"
    if not os.path.exists(last_pt):
        print(f"❌ Error: {last_pt} not found!")
        sys.exit(1)

    print(f"📦 Resuming from unstripped checkpoint: {last_pt}")
    print("🚀 Preserving 54.3% mAP50 baseline + AdamW momentum + EMA weights")
    print("🎯 Target: Continues from Epoch 146 up to 250 total epochs")
    print("=" * 68)

    model = RTDETR(last_pt)
    model.train(resume=True)

if __name__ == "__main__":
    main()
