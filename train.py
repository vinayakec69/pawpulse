"""
RT-DETR-L Training Script for Animal Detection (CCTV-Optimized)
Resolution: 1536 | Batch: 2 | Epochs: 150
Hardware: NVIDIA GeForce RTX 5080 (16GB VRAM)
"""

from pathlib import Path
from ultralytics import RTDETR

def train_model():
    dataset_yaml = Path(r"C:\animal\dataset\data.yaml").resolve()
    if not dataset_yaml.exists():
        dataset_yaml = Path(r"C:\animal\dataset\combined_dataset\data.yaml").resolve()
    
    print("=" * 65)
    print("🐾 Initializing CCTV-Optimized RT-DETR-L Training")
    print(f"📁 Dataset: {dataset_yaml}")
    print("=" * 65)

    model = RTDETR("rtdetr-l.pt")

    results = model.train(
        data=str(dataset_yaml),
        epochs=150,
        imgsz=1536,
        batch=2,
        device=0,
        workers=4,
        amp=True,
        optimizer="AdamW",
        lr0=0.0001,
        lrf=0.01,
        cos_lr=True,
        warmup_epochs=5,
        label_smoothing=0.05,
        dropout=0.1,
        degrees=15,
        fliplr=0.5,
        flipud=0.0,
        scale=0.3,
        shear=2.0,
        perspective=0.0008,
        erasing=0.3,
        mixup=0.1,
        copy_paste=0.1,
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.4,
        mosaic=1.0,
        close_mosaic=20,
        cache="disk",
        patience=30,
        project=r"C:\animal\runs\shelter_monitoring",
        name="train_rtdetr_l_cctv_1536",
        exist_ok=True,
        save=True,
        save_period=5,
        plots=True,
        verbose=True
    )

    print("\n✅ Training Complete!")
    print(f"🏆 Best weights saved at: C:\\animal\\runs\\shelter_monitoring\\train_rtdetr_l_cctv_1536\\weights\\best.pt")

if __name__ == "__main__":
    train_model()
