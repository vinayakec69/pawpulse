"""
PawPulse Training & VRAM Guardian Daemon
Monitors:
- NVIDIA RTX 5080 VRAM usage (Used, Free, Utilization, Temperature)
- Python training process health (train_30k.py)
- Training progress (epochs, loss, best.pt updates)
Logs to: C:\\animal\\training_monitor.log
"""

import os
import sys
import time
import subprocess
from datetime import datetime

LOG_FILE = r"C:\animal\training_monitor.log"
RUN_DIR = r"C:\animal\runs\shelter_monitoring\train_rtdetr_l_30k_rtx5080"
RESULTS_CSV = os.path.join(RUN_DIR, "results.csv")
BEST_PT = os.path.join(RUN_DIR, "weights", "best.pt")

def get_gpu_metrics():
    try:
        cmd = ["nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu", "--format=csv,noheader,nounits"]
        out = subprocess.check_output(cmd, encoding="utf-8", stderr=subprocess.DEVNULL).strip()
        total, used, free, util, temp = [int(x.strip()) for x in out.split(",")]
        return {
            "total_mb": total,
            "used_mb": used,
            "free_mb": free,
            "util_pct": util,
            "temp_c": temp
        }
    except Exception as e:
        return None

def is_training_running():
    try:
        # Check running processes with train_30k.py
        cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" | Select-Object -ExpandProperty CommandLine"]
        out = subprocess.check_output(cmd, encoding="utf-8", stderr=subprocess.DEVNULL)
        return "train_30k.py" in out
    except Exception:
        return False

def get_latest_epoch():
    if not os.path.exists(RESULTS_CSV):
        return 0
    try:
        with open(RESULTS_CSV, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if len(lines) > 1:
            last_line = lines[-1].split(",")
            return int(last_line[0])
    except Exception:
        pass
    return 0

def log_status(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{ts}] {msg}"
    print(formatted)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def main():
    log_status("🛡️ PawPulse Background VRAM & Training Guardian Daemon started.")
    alert_triggered = False

    while True:
        gpu = get_gpu_metrics()
        running = is_training_running()
        epoch = get_latest_epoch()

        if gpu:
            used = gpu["used_mb"]
            free = gpu["free_mb"]
            total = gpu["total_mb"]
            temp = gpu["temp_c"]
            util = gpu["util_pct"]

            status_str = f"STATUS: {'RUNNING' if running else 'HALTED'} | Epoch: {epoch}/175 | VRAM: {used}/{total} MB ({free} MB free) | GPU Util: {util}% | Temp: {temp}°C"

            # Check danger threshold (>14,800 MB = <1,500 MB remaining on 16GB)
            if used > 14800:
                log_status(f"⚠️ WARNING: HIGH VRAM USAGE DETECTED! {status_str}")
                alert_triggered = True
            else:
                log_status(status_str)
                alert_triggered = False

            if not running:
                log_status("⚠️ ALERT: Training process (train_30k.py) is not active! Check terminal.")
        else:
            log_status("⚠️ Could not read nvidia-smi GPU metrics.")

        # Check every 60 seconds
        time.sleep(60)

if __name__ == "__main__":
    main()
