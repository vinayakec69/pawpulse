# PawPulse: AI-Based CCTV Animal Activity & Health Monitoring System for Shelters

[![Vercel Deployment](https://img.shields.io/badge/Deployed%20on-Vercel-black?logo=vercel)](https://flying-flint-yu8fe55.tmp.now)
[![Model](https://img.shields.io/badge/Model-RT--DETR--L%20%2B%20ByteTrack-blueviolet)](https://github.com/ultralytics/ultralytics)
[![Database](https://img.shields.io/badge/Database-Supabase%20PostgreSQL-3ECF8E?logo=supabase)](https://supabase.com)
[![Hardware](https://img.shields.io/badge/Inference-NVIDIA%20RTX%205080-76B900?logo=nvidia)](https://nvidia.com)

**PawPulse** transforms passive shelter CCTV cameras into a non-intrusive veterinary decision-support system. Using high-resolution **RT-DETR-L** (Real-Time Detection Transformer) paired with **ByteTrack**, it tracks individual dogs and cats across cage bars, mesh fences, and communal runs to detect early behavioural indicators of illness (lethargy, prolonged corner isolation, and missed feeding routines) before symptoms become severe.

Developed for **Department of Information Science & Engineering, Sahyadri College of Engineering & Management, Mangaluru** (Mini-Project IS17, Academic Year 2026–27).

---

## 🌟 Key Features

* **High-Resolution CCTV Detection (RT-DETR-L at 1536px)**: Transformer-based multi-animal detection trained on CCTV shelter pens, resolving small bodies, dim lighting, and mutual occlusions without conventional NMS bottlenecks.
* **Persistent Multi-Animal Tracking (ByteTrack)**: Maintains consistent track identities and individual motion trajectories across temporary occlusions and mesh barriers.
* **Spatio-Temporal Behavioral Metric Extraction**:
  * **Cumulative Displacement**: $d_t = \sqrt{(c_{x,t} - c_{x,t-1})^2 + (c_{y,t} - c_{y,t-1})^2}$ calibrated to real meters.
  * **Resting / Inactivity Accumulator**: Tracks stationary hours below velocity thresholds ($< 0.12\text{ m/s}$).
  * **Posture Proxy Aspect Ratio**: $r = \frac{w}{h}$ to distinguish standing vs. recumbent/collapsed postures.
  * **Enclosure Zone Analytics**: Polygon point-in-polygon tests monitoring visits to the **Food & Water Bowl** and dwell time in **Secluded Dark Corners**.
* **Statistical Anomaly Detection**:
  * Rolling 3-day individual and pen baseline comparisons.
  * **Z-Score Deviation Engine**: $Z_t = \frac{x_t - \mu}{\sigma}$ flagging sustained mobility drops ($Z < -2.5\sigma$ or activity $< 40\%$ of baseline).
* **Supabase Realtime Cloud Backend**: PostgreSQL time-series storage (`telemetry_logs`, `animals`, `alerts`, `enclosures`, `zones`) broadcasting instant WebSocket notifications to on-duty caretakers.
* **Meowville-Themed Caretaker Web Dashboard**: Warm, nurturing boutique aesthetic (cream `#FBF8F3`, plum `#9E5788`, peach `#F28C60`, sage `#4DA67A`) featuring live CCTV HUD viewports, 24-hour baseline comparison charts, and 1-click CSV report exports.

---

## 🏛️ System Architecture

```text
 ┌──────────────────────┐
 │ CCTV / Recorded MP4  │ (High-angle shelter enclosure feeds)
 └──────────┬───────────┘
            │
            v
 ┌──────────────────────┐
 │ RT-DETR-L + ByteTrack│ (Detection at 1536px + persistent Kalman tracking)
 └──────────┬───────────┘
            │
            v
 ┌──────────────────────┐
 │ Spatio-Temporal      │ (Displacement, Rest Hours, Food Bowl Visits,
 │ Behavioral Analytics │  Corner Dwell Time, Posture Ratio r = w/h)
 └──────────┬───────────┘
            │
            v
 ┌──────────────────────┐
 │ Anomaly Detection    │ (Z-Score & CUSUM deviation from 3-day baseline)
 └──────────┬───────────┘
            │
      ┌─────┴─────────────────────┐
      │                           │
      v                           v
┌───────────┐             ┌────────────────────────┐
│ Supabase  │──WebSockets>│ Decision-Support       │
│ PostgreSQL│             │ Web Dashboard (Vercel) │
└───────────┘             └────────────────────────┘
```

---

## 📊 Model Evaluation & Benchmarks

Trained on CCTV shelter imagery with high-resolution 1536px feature mapping:

| Target Class | Precision | Recall | mAP50 | mAP50-95 |
| :--- | :---: | :---: | :---: | :---: |
| 🐶 **Dog** | **65.6%** | **62.5%** | **64.2%** | **34.3%** |
| 🐱 **Cat** | **53.2%** | **49.5%** | **46.8%** | **25.6%** |
| 🐾 **All Classes (Val)** | **59.4%** | **56.0%** | **55.5%** | **30.0%** |

*Inference Speed: ~15.8 FPS on NVIDIA GeForce RTX 5080 (16GB VRAM, TensorRT/PyTorch nightly cu128).*

---

## 📁 Repository Structure

```text
pawpulse/
├── dashboard/                     # Web Application (Frontend)
│   ├── index.html                 # Meowville shelter caretaker dashboard
│   ├── css/
│   │   ├── meowville.css          # Design tokens, color palette, offset frames
│   │   └── pawpulse.css           # Glassmorphism, animations, UI components
│   ├── js/
│   │   ├── app.js                 # Controller, Supabase Realtime, Chart.js
│   │   └── canvas.js              # CCTV simulation & telemetry HUD engine
│   ├── assets/                    # Sample videos & telemetry exports
│   │   ├── cctv_5min_shelter_pen2.mp4   # 5-minute continuous surveillance stream
│   │   ├── monitored_cat.mp4            # Annotated cat tracking clip
│   │   └── monitored_dog.mp4            # Annotated dog tracking clip
│   └── vercel.json                # Vercel deployment configuration
├── animal_monitor.py              # Standalone local video/webcam tracking pipeline
├── video_worker_supabase.py       # Production worker syncing RT-DETR to Supabase
├── process_video.py               # Offline batch video processor with HUD burner
├── generate_5min_cctv.py          # 5-minute CCTV video generator script
├── resume_training_to_250.py      # Session resumption training script
├── train.py                       # Base RT-DETR-L training pipeline
├── supabase_schema.sql            # PostgreSQL DDL, RLS policies & seed data
├── launch_dashboard.bat           # 1-click local dashboard launcher
└── requirements.txt               # Python package dependencies
```

---

## 🚀 Quick Start Guide

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/vinayakec69/pawpulse.git
cd pawpulse

python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Set Up Supabase Database

1. Create a project at [supabase.com](https://supabase.com).
2. Go to **SQL Editor** $\rightarrow$ Open `supabase_schema.sql` $\rightarrow$ Click **Run**.
3. Copy your **Project URL** and **Publishable/Anon Key**.

### 3. Launch the Caretaker Dashboard

* **Local Mode**: Double-click `launch_dashboard.bat` or run:
  ```bash
  python -m http.server 8080 --directory dashboard
  ```
  Visit: `http://localhost:8080`
* **Vercel Live**: [https://flying-flint-yu8fe55.tmp.now](https://flying-flint-yu8fe55.tmp.now)
* Click the **Database / Key icon** in the top navigation bar, paste your Supabase URL and Publishable key, and click **Save & Connect**.

### 4. Run Video Ingestion & Tracking Worker

To process a video file and stream live telemetry to Supabase:
```bash
python video_worker_supabase.py \
  --video "dashboard/assets/cctv_5min_shelter_pen2.mp4" \
  --weights "best.pt" \
  --supabase-url "https://your-project.supabase.co" \
  --supabase-key "your-publishable-or-secret-key"
```

---

## 📜 Academic Attribution & Ethics

* **Institution**: Sahyadri College of Engineering & Management, Mangaluru
* **Department**: Information Science & Engineering (IS17)
* **Guide**: Dr. Akhila Thejaswi R
* **Scope & Ethics Notice**: PawPulse functions strictly as a non-invasive **decision-support tool** for shelter personnel and visiting veterinarians. It flags measurable behavioural anomalies (social isolation, lethargy, missed feedings) for human verification; it does not diagnose medical conditions or prescribe treatments.
