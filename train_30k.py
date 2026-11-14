"""
PawPulse RT-DETR-L 30k Dataset Training Engine
Hardware: NVIDIA GeForce RTX 5080 (16GB VRAM)
Dataset: C:/animal/dataset/dataset_30k/data_30k.yaml (30,000+ images)
Target: High-precision shelter surveillance animal detection (Zero cat/dog confusion)
"""

import os
import sys
import torch
from ultralytics import RTDETR

def train_30k():
    print("=" * 65)
    print("🐾 PAWPULSE 30K DATASET TRAINING — RT-DETR-L")
    print("=" * 65)

    if not torch.cuda.is_available():
        print("❌ Error: CUDA GPU not found!")
        sys.exit(1)

    gpu_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print(f"⚡ GPU: {gpu_name} ({vram_gb:.1f} GB VRAM)")
    print(f"🔥 PyTorch: {torch.__version__} | CUDA: {torch.version.cuda}")

    dataset_yaml = r"C:\animal\dataset\dataset_30k\data_30k.yaml"
    if not os.path.exists(dataset_yaml):
        dataset_yaml = r"C:\animal\dataset\data.yaml"

    base_weights = r"C:\animal\best.pt"
    if not os.path.exists(base_weights):
        base_weights = "rtdetr-l.pt"

    print(f"📦 Resuming from: {base_weights}")
    print(f"📁 Dataset: {dataset_yaml}")
    print("⚙️ Hyperparameters:")
    print("   - Resolution: 1280x1280")
    print("   - Batch Size: 4 (RTX 5080 16GB)")
    print("   - Epochs: 100")
    print("   - Mosaic: 0.0 (Disabled: Prevents cat/dog feature scrambling)")
    print("   - Cls Weight: 2.0 (Doubled species classification penalty)")
    print("   - Learning Rate: lr0=0.0001 with Cosine LR schedule")
    print("=" * 65)

    model = RTDETR(base_weights)

    results = model.train(
        data=dataset_yaml,
        epochs=100,
        imgsz=1280,
        batch=4,
        device="0",
        optimizer="AdamW",
        lr0=0.0001,
        lrf=0.01,
        cos_lr=True,
        warmup_epochs=3,
        mosaic=0.0,             # Keep disabled to prevent cat/dog confusion
        close_mosaic=0,
        cls=2.0,                # Heavier species loss penalty
        box=5.0,                # High spatial precision
        amp=True,               # Mixed precision Tensor Cores
        workers=8,
        save=True,
        save_period=5,
        project=r"C:\animal\runs\shelter_monitoring",
        name="train_rtdetr_l_30k_rtx5080",
        exist_ok=True,
        plots=True,
        verbose=True
    )

    print("\n🎉 30k Dataset Training Complete!")
    best_weights = r"C:\animal\runs\shelter_monitoring\train_rtdetr_l_30k_rtx5080\weights\best.pt"
    print(f"⭐ New weights saved to: {best_weights}")

if __name__ == "__main__":
    train_30k()
