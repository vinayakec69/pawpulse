"""
PawPulse MP4 Video Processing Worker + Supabase Bridge
Processes CCTV recordings using RT-DETR-L + ByteTrack and syncs metrics directly to Supabase.
"""

import os
import sys
import time
import cv2
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from ultralytics import RTDETR

# Try importing supabase
try:
    from supabase import create_client, Client
except ImportError:
    print("[!] supabase-py not installed. Run: pip install supabase")

# ==========================================
# DEFAULT CONFIGURATION
# ==========================================
PIXELS_PER_METER = 25.0       # Calibrated: 25 pixels ≈ 1 meter
ALERT_MIN_ACTIVITY_PCT = 0.40 # Alert if activity < 40% of baseline
DEFAULT_BASELINE = 800.0      # Expected daily distance (meters)

ZONES = {
    "food_bowl": {
        "name": "Food & Water Bowl",
        "polygon": np.array([[0.05, 0.70], [0.25, 0.70], [0.25, 0.95], [0.05, 0.95]], np.float32),
        "color": (82, 166, 132), # Sage green
    },
    "secluded_corner": {
        "name": "Secluded Dark Corner",
        "polygon": np.array([[0.75, 0.05], [0.98, 0.05], [0.98, 0.35], [0.75, 0.35]], np.float32),
        "color": (229, 107, 111), # Soft coral
    }
}

class AnimalTrackerState:
    def __init__(self, track_id, class_name, baseline_dist=DEFAULT_BASELINE):
        self.track_id = track_id
        self.class_name = class_name
        self.baseline_dist = baseline_dist
        
        self.last_centroid = None
        self.last_time = time.time()
        self.total_distance = 0.0
        self.resting_seconds = 0.0
        self.stationary_time = 0.0
        self.secluded_corner_seconds = 0.0
        self.food_bowl_visits = 0
        self.in_bowl = False
        self.is_flagged = False
        self.alert_sent = False
        self.status = "Healthy"

    def update(self, cx, cy, frame_w, frame_h, dt):
        if self.last_centroid is not None and dt > 0:
            px_dist = np.hypot(cx - self.last_centroid[0], cy - self.last_centroid[1])
            m_dist = px_dist / PIXELS_PER_METER
            speed = m_dist / dt
            
            if px_dist > 3.0:
                self.total_distance += m_dist
                self.stationary_time = 0.0
            else:
                self.stationary_time += dt
                if self.stationary_time > 3.0:
                    self.resting_seconds += dt
        
        self.last_centroid = (cx, cy)
        
        # Check zones
        corner_pts = (ZONES["secluded_corner"]["polygon"] * [frame_w, frame_h]).astype(np.int32)
        bowl_pts = (ZONES["food_bowl"]["polygon"] * [frame_w, frame_h]).astype(np.int32)
        
        in_corner = cv2.pointPolygonTest(corner_pts, (float(cx), float(cy)), False) >= 0
        in_bowl = cv2.pointPolygonTest(bowl_pts, (float(cx), float(cy)), False) >= 0
        
        if in_corner:
            self.secluded_corner_seconds += dt
            
        if in_bowl:
            if not self.in_bowl:
                self.food_bowl_visits += 1
                self.in_bowl = True
        else:
            self.in_bowl = False

        # Evaluation
        if self.secluded_corner_seconds > 45.0 or (self.total_distance < 50.0 and self.resting_seconds > 60.0):
            self.is_flagged = True
            self.status = "Lethargic / Isolated"
        elif self.stationary_time > 3.0:
            self.status = "Resting"
        else:
            self.status = "Healthy"


class VideoWorker:
    def __init__(self, model_path, supabase_url=None, supabase_key=None):
        print(f"🐾 Loading RT-DETR model from: {model_path}")
        self.model = RTDETR(model_path)
        self.supabase = None
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                print("✅ Connected to Supabase Backend successfully!")
            except Exception as e:
                print(f"[!] Warning: Could not connect to Supabase: {e}")
        
        self.animals = {}

    def process_video(self, video_path, output_path=None, show_ui=True):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Error: Cannot open video: {video_path}")
            return
        
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

        print(f"🎬 Processing MP4: {video_path} ({w}x{h} @ {fps:.1f} FPS)")
        
        frame_idx = 0
        last_sync_time = time.time()
        
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_idx += 1
                dt = 1.0 / fps
                video_time_sec = frame_idx / fps
                
                # Run RT-DETR + ByteTrack
                results = self.model.track(
                    source=frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    conf=0.35,
                    classes=[0, 1],
                    verbose=False
                )
                
                if results and results[0].boxes and results[0].boxes.id is not None:
                    boxes = results[0].boxes.xyxy.cpu().numpy()
                    track_ids = results[0].boxes.id.int().cpu().numpy()
                    cls_ids = results[0].boxes.cls.int().cpu().numpy()
                    
                    for box, tid, cid in zip(boxes, track_ids, cls_ids):
                        species = "dog" if cid == 0 else "cat"
                        if tid not in self.animals:
                            self.animals[tid] = AnimalTrackerState(tid, species)
                        
                        state = self.animals[tid]
                        x1, y1, x2, y2 = box.astype(int)
                        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                        
                        state.update(cx, cy, w, h, dt)
                        
                        # Draw soft rounded overlays on video
                        color = (111, 107, 229) if state.is_flagged else (132, 166, 82)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        label = f"{species.upper()} #{tid} | {state.total_distance:.1f}m | {state.status}"
                        cv2.putText(frame, label, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # Sync telemetry to Supabase every 2 seconds
                if time.time() - last_sync_time > 2.0:
                    last_sync_time = time.time()
                    self.sync_to_supabase(video_time_sec)

                if writer:
                    writer.write(frame)
                    
                if show_ui:
                    cv2.imshow("PawPulse CCTV Ingestion", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        finally:
            cap.release()
            if writer:
                writer.release()
            cv2.destroyAllWindows()
            print("🏁 Video processing completed!")

    def sync_to_supabase(self, video_time):
        if not self.supabase:
            return
        
        for tid, state in self.animals.items():
            try:
                # Upsert animal status
                self.supabase.table("animals").update({
                    "current_status": state.status,
                    "is_flagged": state.is_flagged
                }).eq("track_id", tid).execute()
                
                # If newly flagged, send alert
                if state.is_flagged and not state.alert_sent:
                    state.alert_sent = True
                    self.supabase.table("alerts").insert({
                        "severity": "CRITICAL",
                        "alert_type": "LETHARGY",
                        "message": f"🚨 ALERT: {state.class_name.capitalize()} #{tid} has moved only {state.total_distance:.1f}m and remained in corner for {int(state.secluded_corner_seconds)}s! Please check Pen 2.",
                        "activity_ratio": round(state.total_distance / state.baseline_dist, 3)
                    }).execute()
                    print(f"🔔 Dispatched Realtime Alert to Supabase for #{tid}!")
            except Exception as e:
                print(f"[!] Supabase sync error: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, required=True, help="Path to input MP4 video")
    parser.add_argument("--weights", type=str, default=r"C:\animal\best.pt", help="Model weights (best.pt)")
    parser.add_argument("--output", type=str, default="annotated_output.mp4")
    parser.add_argument("--supabase-url", type=str, default=os.getenv("SUPABASE_URL"))
    parser.add_argument("--supabase-key", type=str, default=os.getenv("SUPABASE_ANON_KEY"))
    args = parser.parse_args()

    worker = VideoWorker(args.weights, args.supabase_url, args.supabase_key)
    worker.process_video(args.video, args.output)
