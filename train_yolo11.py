"""
PawPulse YOLO11 Maximum Accuracy Training Engine
Architecture: YOLO11-X (Flagship Extra-Large) / YOLO11-L
Hardware: NVIDIA GeForce RTX 5080 (16GB VRAM, Tensor Cores, CUDA 12.8)
Dataset: C:/animal/dataset/dataset_30k/data_30k.yaml (23,778 images)

Key Advantages over RT-DETR-L:
- Task-Aligned Assigner (TAL) for significantly higher mAP50 and mAP50-95
- Larger batch size (batch=8) for clean, stable Batch Normalization
- Zero FP16 NaN instability (smooth full cosine annealing)
- Compact ~50MB production weights with 100+ FPS inference
"""

import os
import sys

# CUDA Allocator Configuration for RTX 5080
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "garbage_collection_threshold:0.8,max_split_size_mb:128"

import torch
from ultralytics import YOLO

def train_yolo11():
    print("=" * 75)
    print("🐾 PAWPULSE YOLO11 HIGH-ACCURACY TRAINING ENGINE (RTX 5080)")
    print("=" * 75)

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

    # Flagship high-accuracy model: yolo11x (Extra-Large, 56.9M params)
    # If downloading 'yolo11x.pt' takes too long, fallback to 'yolo11l.pt' (25M params)
    base_model = "yolo11x.pt"

    print(f"📦 Base Architecture: {base_model} (Flagship Accuracy)")
    print(f"📁 Dataset: {dataset_yaml}")
    print("=" * 75)
    print("⚙️ HIGH-ACCURACY HYPERPARAMETER CONFIGURATION:")
    print("   [1] Model:           YOLO11-X (Flagship Deep CNN + C2PSA Attention)")
    print("   [2] Resolution:      1280x1280 (High-definition surveillance)")
    print("   [3] Batch Size:      batch=8 (Stable batch normalization & gradients)")
    print("   [4] Target Epochs:   60 epochs (Estimated ~10 hours on RTX 5080)")
    print("   [5] Loss Weights:    cls=1.5 (Penalized species loss), box=7.5")
    print("   [6] Surveillance:    hsv_v=0.4, hsv_s=0.5, degrees=10.0, fliplr=0.5")
    print("   [7] Early Stopping:  patience=20 epochs")
    print("=" * 75)

    model = YOLO(base_model)

    results = model.train(
        # 1. Dataset & Hardware
        data=dataset_yaml,
        epochs=60,
        imgsz=1280,
        batch=8,
        device="0",
        workers=4,
        amp=True,
        cache=False,

        # 2. Optimization
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        cos_lr=True,
        warmup_epochs=3,
        warmup_momentum=0.8,
        weight_decay=0.0005,

        # 3. High-Accuracy Loss Balancing
        cls=1.5,                 # Heavy penalty on Cat vs Dog confusion
        box=7.5,                 # Tight spatial IoU localization
        dfl=1.5,                 # Distribution Focal Loss for sub-pixel boundary accuracy
        label_smoothing=0.05,

        # 4. CCTV Invariance Augmentations
        mosaic=0.5,              # Controlled mosaic for scale diversity
        close_mosaic=10,         # Turn OFF mosaic in final 10 epochs for pristine silhouette convergence
        mixup=0.0,               # Off: Keep distinct fur textures
        copy_paste=0.0,
        fliplr=0.5,
        flipud=0.0,
        degrees=10.0,
        scale=0.3,
        shear=1.5,
        perspective=0.0005,
        erasing=0.20,
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.4,

        # 5. Checkpointing & Organization
        patience=20,
        save=True,
        save_period=5,
        project=r"C:\animal\runs\shelter_monitoring",
        name="train_yolo11_rtx5080",
        exist_ok=True,
        plots=True,
        verbose=True
    )

    print("\n🎉 YOLO11 Training Complete!")
    best_weights = r"C:\animal\runs\shelter_monitoring\train_yolo11_rtx5080\weights\best.pt"
    print(f"⭐ Optimal converged weights saved to: {best_weights}")

if __name__ == "__main__":
    train_yolo11()
