"""
Resume RT-DETR-L Training from last checkpoint
Hardware: NVIDIA GeForce RTX 5080 (16GB VRAM)
"""

from pathlib import Path
from ultralytics import RTDETR

def resume_training():
    last_checkpoint = Path(r"C:\animal\runs\shelter_monitoring\train_rtdetr_l_cctv_1536\weights\last.pt").resolve()
    
    if not last_checkpoint.exists():
        raise FileNotFoundError(f"Checkpoint not found at: {last_checkpoint}")

    print("=" * 65)
    print(f"🔄 Resuming RT-DETR-L Training from: {last_checkpoint}")
    print("=" * 65)

    model = RTDETR(str(last_checkpoint))
    results = model.train(resume=True)
    print("\n✅ Resumed Training Finished!")

if __name__ == "__main__":
    resume_training()
