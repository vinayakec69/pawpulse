"""
PawPulse Phase 2 Training: 250 Epochs Target
Resumes from 150-epoch best.pt -> Adds 100 fine-tuning epochs to reach 250 total.
Optimized for:
- Fixing Cat vs Dog classification (cls=2.0 weight)
- Eliminating fur scrambling (mosaic=0.0 disabled)
- Stable bounding boxes at 1536px resolution
- Blackwell RTX 5080 (16GB VRAM, batch=2, AMP=True)
"""

import os
import sys
import torch
from pathlib import Path
from ultralytics import RTDETR

def main():
    print("=" * 65)
    print("🐾 PAWPULSE: EXTENDING TRAINING TO 250 EPOCHS TOTAL")
    print("=" * 65)

    # 1. Hardware verification
    if not torch.cuda.is_available():
        print("❌ Error: CUDA GPU is not available! Check PyTorch installation.")
        sys.exit(1)

    gpu_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print(f"⚡ GPU: {gpu_name} ({vram_gb:.1f} GB VRAM)")
    print(f"🔥 PyTorch: {torch.__version__} | CUDA: {torch.version.cuda}")

    # 2. Checkpoint path selection
    import argparse
    parser = argparse.ArgumentParser(description="PawPulse Phase 2 Training")
    parser.add_argument("--weights", type=str, default="last", choices=["last", "best"],
                        help="Choose checkpoint to continue from: 'last' (Epoch 150) or 'best' (Epoch 133 peak)")
    args, _ = parser.parse_known_args()

    last_pt = r"C:\animal\runs\shelter_monitoring\train_rtdetr_l_cctv_1536\weights\last.pt"
    best_pt = r"C:\animal\runs\shelter_monitoring\train_rtdetr_l_cctv_1536\weights\best.pt"
    
    if args.weights == "last" and os.path.exists(last_pt):
        base_weights = last_pt
        ckpt_note = "last.pt (End of Epoch 150)"
    elif os.path.exists(best_pt):
        base_weights = best_pt
        ckpt_note = "best.pt (Epoch 133 Peak mAP 55.4%)"
    else:
        base_weights = last_pt
        ckpt_note = "last.pt"

    print(f"📦 Continuing directly from: {ckpt_note}")
    print(f"📁 Path: {base_weights}")
    print("🎯 Target: +100 Epochs (completing 250 Epochs Total)")
    print("⚙️ Hyperparameters:")
    print("   - Resolution: 1536x1536 (CCTV high-res)")
    print("   - Batch size: 2")
    print("   - Mosaic: 0.0 (OFF - stops cat/dog feature scrambling)")
    print("   - Cls weight: 2.0 (Doubled classification penalty)")
    print("   - Learning rate: lr0=0.00005 with Cosine LR decay")
    print("=" * 65)

    # 3. Initialize model
    model = RTDETR(base_weights)

    # 4. Start Phase 2 training
    results = model.train(
        data=r"C:\animal\dataset\data.yaml",
        epochs=100,             # 100 additional epochs = 250 epochs total
        imgsz=1536,
        batch=2,
        device="0",
        optimizer="AdamW",
        lr0=0.00005,            # Fine-tuning rate to refine learned weights
        lrf=0.01,
        cos_lr=True,
        mosaic=0.0,             # No mosaic: preserves natural fur textures
        close_mosaic=0,
        cls=2.0,                # Heavier weight on class loss to resolve cat vs dog
        box=5.0,                # Solid localization
        amp=True,               # Mixed precision on Tensor Cores
        workers=4,
        save=True,
        save_period=5,
        project=r"C:\animal\runs\shelter_monitoring",
        name="train_rtdetr_l_cctv_1536_250epochs",
        exist_ok=True,
        verbose=True
    )

    print("\n🎉 Training completed successfully up to 250 epochs total!")
    best_path = r"C:\animal\runs\shelter_monitoring\train_rtdetr_l_cctv_1536_250epochs\weights\best.pt"
    print(f"⭐ New weights saved to: {best_path}")

if __name__ == "__main__":
    main()
