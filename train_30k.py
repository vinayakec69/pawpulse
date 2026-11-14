"""
PawPulse Comprehensive RT-DETR-L 30k Training Engine
Hardware: NVIDIA GeForce RTX 5080 (16GB VRAM, Tensor Cores, CUDA 12.8)
Dataset: C:/animal/dataset/dataset_30k/data_30k.yaml (23,778 verified images)

Full Hyperparameter Suite:
- Zero-Blended Texture Augmentation (mosaic=0, mixup=0, copy_paste=0) to fix Cat vs Dog confusion
- CCTV-Calibrated Lighting Invariance (hsv_s=0.5, hsv_v=0.4) for low-light night-vision
- Top-Down Surveillance Geometry (perspective=0.0008, shear=2.0, degrees=15, scale=0.3)
- Penalized Classification Loss (cls=2.0, box=5.0)
- Regularized Generalization (label_smoothing=0.05, dropout=0.1, weight_decay=0.0005)
"""

import os
import sys
import torch
from ultralytics import RTDETR

def train_30k():
    print("=" * 70)
    print("🐾 PAWPULSE 30K DATASET TRAINING — RT-DETR-L FULL HYPERPARAMETER SUITE")
    print("=" * 70)

    if not torch.cuda.is_available():
        print("❌ Error: CUDA GPU not found! Please check NVIDIA drivers.")
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
    print("=" * 70)
    print("⚙️ EXHAUSTIVE HYPERPARAMETER SPECIFICATION:")
    print("   [1] Model Architecture:   RT-DETR-L (1280x1280 high-res)")
    print("   [2] Batch & Memory:       batch=4, workers=8, amp=True (FP16 Tensor Cores)")
    print("   [3] Optimization:         AdamW, lr0=0.0001, lrf=0.01, cos_lr=True, warmup=5 epochs")
    print("   [4] Species Loss Weights: cls=2.0 (Doubled species loss), box=5.0 (Bounding box IoU)")
    print("   [5] Species Isolation:    mosaic=0.0, mixup=0.0, copy_paste=0.0 (Eliminates fur blending)")
    print("   [6] Surveillance Invariance: hsv_v=0.4, hsv_s=0.5, shear=2.0, perspective=0.0008")
    print("   [7] Regularization:       label_smoothing=0.05, dropout=0.1, weight_decay=0.0005")
    print("   [8] Early Stopping:       patience=30 epochs without validation improvement")
    print("=" * 70)

    model = RTDETR(base_weights)

    results = model.train(
        # 1. Dataset & Hardware
        data=dataset_yaml,
        epochs=100,
        imgsz=1280,
        batch=4,
        device="0",
        workers=8,
        amp=True,
        cache="disk",

        # 2. Optimizer & Learning Rate Schedule
        optimizer="AdamW",
        lr0=0.0001,
        lrf=0.01,
        cos_lr=True,
        warmup_epochs=5,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        weight_decay=0.0005,

        # 3. Loss Scaling & Balancing
        cls=2.0,                 # Doubled classification loss: heavy penalty on Cat vs Dog confusion
        box=5.0,                 # High spatial localization accuracy
        label_smoothing=0.05,    # Softens targets: prevents overconfidence on ambiguous dark silhouettes
        dropout=0.1,             # Randomly drops feature connections to prevent background memorization

        # 4. Anti-Scrambling Augmentations (Preserves distinct natural silhouettes)
        mosaic=0.0,              # OFF: Never cut and stitch animal patches together
        close_mosaic=0,
        mixup=0.0,               # OFF: Never blend transparent dog and cat images
        copy_paste=0.0,          # OFF: Never paste cat limbs onto dogs

        # 5. Surveillance & CCTV Environmental Invariance
        fliplr=0.5,              # 50% horizontal flip (left/right motion invariance)
        flipud=0.0,              # 0% vertical flip (animals do not walk on ceilings)
        degrees=15.0,            # +/- 15 deg camera mounting rotation
        scale=0.3,               # +/- 30% scale variation (handles near & far camera distance)
        shear=2.0,               # 2 deg shear angle (handles overhead fisheye angle distortion)
        perspective=0.0008,      # Top-down perspective transformation
        erasing=0.25,            # 25% random cutout (robust to cage bars, bowls & obstacle occlusion)
        hsv_h=0.015,             # Subtle hue variation (+/- 1.5%)
        hsv_s=0.5,               # Strong saturation jitter (handles washed-out monochrome infrared)
        hsv_v=0.4,               # Strong brightness jitter (handles pitch-black corners & glaring spotlights)

        # 6. Checkpointing & Monitoring
        patience=30,             # Early stopping if no mAP gain in 30 epochs
        save=True,
        save_period=5,           # Saves checkpoint every 5 epochs
        project=r"C:\animal\runs\shelter_monitoring",
        name="train_rtdetr_l_30k_rtx5080",
        exist_ok=True,
        plots=True,
        verbose=True
    )

    print("\n🎉 30k Dataset Training Complete!")
    best_weights = r"C:\animal\runs\shelter_monitoring\train_rtdetr_l_30k_rtx5080\weights\best.pt"
    print(f"⭐ Optimal converged weights saved to: {best_weights}")

if __name__ == "__main__":
    train_30k()
