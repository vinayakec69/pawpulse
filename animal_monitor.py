"""
Animal Welfare & Behavior Monitoring Pipeline
Model: RT-DETR-L + ByteTrack
Features:
- Persistent ID Tracking across occlusions (cage bars, crossings)
- Distance traveled (meters)
- Resting / idle hours tracker
- Zone monitoring (Food bowl visits, secluded dark corner dwell time)
- Behavioral anomaly detection (alert when activity < 40% of baseline)
- Real-time HUD overlay & Caretaker Dashboard JSON export
"""

import cv2
import numpy as np
import time
import json
from datetime import datetime
from pathlib import Path
from ultralytics import RTDETR

# ==========================================
# CONFIGURATION & THRESHOLDS
# ==========================================
PIXELS_PER_METER = 25.0       # Calibration factor: 25 pixels ≈ 1 meter (adjust per camera)
REST_SPEED_THRESHOLD = 0.15   # meters/sec below which animal is considered stationary/resting
ALERT_MIN_ACTIVITY_PCT = 0.40 # Alert if activity < 40% of baseline (as per system specs)
DEFAULT_BASELINE_METERS = 800.0 # Expected normal daily distance in meters

# Zones defined as polygons (Normalized [0.0 - 1.0] relative to frame width/height)
ZONES = {
    "food_bowl": {
        "name": "Food Bowl",
        "polygon": np.array([[0.05, 0.70], [0.25, 0.70], [0.25, 0.95], [0.05, 0.95]], np.float32),
        "color": (0, 255, 0), # Green
    },
    "secluded_corner": {
        "name": "Secluded Dark Corner",
        "polygon": np.array([[0.75, 0.05], [0.98, 0.05], [0.98, 0.35], [0.75, 0.35]], np.float32),
        "color": (0, 0, 255), # Red
    }
}

class AnimalProfile:
    def __init__(self, track_id, class_name, baseline_distance=DEFAULT_BASELINE_METERS):
        self.track_id = track_id
        self.class_name = class_name
        self.baseline_distance = baseline_distance
        
        # Motion metrics
        self.last_centroid = None
        self.last_timestamp = time.time()
        self.total_distance_meters = 0.0
        self.trajectory = [] # List of past centroids for trail rendering
        
        # Resting / Activity metrics
        self.is_resting = False
        self.resting_seconds = 0.0
        self.current_rest_start = None
        self.consecutive_stationary_time = 0.0
        
        # Zone dwell times
        self.current_zone = None
        self.zone_entry_time = None
        self.secluded_corner_seconds = 0.0
        self.food_bowl_visits = 0
        self.in_food_bowl = False
        
        # Anomaly status
        self.alert_status = "Healthy"
        self.alert_message = ""
        self.is_flagged = False

    def update_position(self, cx, cy, frame_w, frame_h, timestamp):
        dt = timestamp - self.last_timestamp if self.last_timestamp else 0.0
        self.last_timestamp = timestamp
        
        # Normalized coordinates for zone checks
        nx, ny = cx / frame_w, cy / frame_h

        # Calculate distance
        if self.last_centroid is not None and dt > 0:
            pixel_dist = np.hypot(cx - self.last_centroid[0], cy - self.last_centroid[1])
            meter_dist = pixel_dist / PIXELS_PER_METER
            speed = meter_dist / dt # m/s
            
            # Filter noise jitter (< 3 pixels)
            if pixel_dist > 3.0:
                self.total_distance_meters += meter_dist
                self.is_resting = False
                self.consecutive_stationary_time = 0.0
            else:
                self.consecutive_stationary_time += dt
                if self.consecutive_stationary_time > 3.0: # Stationary for > 3 sec
                    self.is_resting = True
                    self.resting_seconds += dt
        
        self.last_centroid = (cx, cy)
        self.trajectory.append((cx, cy))
        if len(self.trajectory) > 40:
            self.trajectory.pop(0)

        # Check Zones
        in_corner = cv2.pointPolygonTest(
            (ZONES["secluded_corner"]["polygon"] * [frame_w, frame_h]).astype(np.int32),
            (float(cx), float(cy)), False
        ) >= 0

        in_bowl = cv2.pointPolygonTest(
            (ZONES["food_bowl"]["polygon"] * [frame_w, frame_h]).astype(np.int32),
            (float(cx), float(cy)), False
        ) >= 0

        if in_corner:
            self.secluded_corner_seconds += dt
        
        if in_bowl:
            if not self.in_food_bowl:
                self.food_bowl_visits += 1
                self.in_food_bowl = True
        else:
            self.in_food_bowl = False

        # Evaluate Behavioral Anomaly
        self.evaluate_health()

    def evaluate_health(self):
        # Activity ratio compared to baseline
        activity_ratio = (self.total_distance_meters / self.baseline_distance) if self.baseline_distance > 0 else 1.0
        
        # Check lethargy or corner dwelling
        if self.secluded_corner_seconds > 60.0 or (self.consecutive_stationary_time > 120.0 and self.total_distance_meters < 50.0):
            self.is_flagged = True
            self.alert_status = "CRITICAL: Lethargic / Isolated"
            self.alert_message = (
                f"🚨 ALERT: {self.class_name.capitalize()} #{self.track_id} has moved only {self.total_distance_meters:.1f}m "
                f"and remained in corner for {int(self.secluded_corner_seconds)}s! Check Pen!"
            )
        elif self.total_distance_meters < (self.baseline_distance * ALERT_MIN_ACTIVITY_PCT) and self.resting_seconds > 180.0:
            self.is_flagged = True
            self.alert_status = "WARNING: Low Activity"
            self.alert_message = (
                f"⚠️ WARNING: {self.class_name.capitalize()} #{self.track_id} activity is "
                f"{activity_ratio*100:.0f}% of baseline. Potential early symptom."
            )
        else:
            self.is_flagged = False
            self.alert_status = "Healthy"
            self.alert_message = f"{self.class_name.capitalize()} #{self.track_id}: Healthy & Active"

class AnimalMonitoringSystem:
    def __init__(self, model_path="rtdetr-l.pt"):
        print(f"📦 Loading RT-DETR model from: {model_path} ...")
        self.model = RTDETR(model_path)
        self.profiles = {}
        self.alert_history = []

    def draw_hud(self, frame, active_profiles):
        h, w = frame.shape[:2]

        # 1. Draw Defined Monitoring Zones
        for zone_id, zone in ZONES.items():
            pts = (zone["polygon"] * [w, h]).astype(np.int32)
            overlay = frame.copy()
            cv2.fillPoly(overlay, [pts], zone["color"])
            cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
            cv2.polylines(frame, [pts], True, zone["color"], 2)
            cv2.putText(frame, zone["name"], (pts[0][0] + 5, pts[0][1] + 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, zone["color"], 2)

        # 2. Draw Top Telemetry Dashboard Bar
        dashboard_h = 70
        cv2.rectangle(frame, (0, 0), (w, dashboard_h), (25, 25, 25), -1)
        cv2.line(frame, (0, dashboard_h), (w, dashboard_h), (0, 200, 255), 2)
        cv2.putText(frame, "🐾 ANIMAL WELFARE MONITOR (RT-DETR + ByteTrack)", (15, 30),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 2)
        cv2.putText(frame, f"Active Tracks: {len(active_profiles)} | System Status: ONLINE",
                    (15, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128), 1)

        # 3. Draw Bounding Boxes, ID Tags, and Path Trails
        alert_banners = []
        for p in active_profiles:
            # Draw motion trail
            for i in range(1, len(p.trajectory)):
                cv2.line(frame, p.trajectory[i-1], p.trajectory[i], (0, 255, 255), 2)

            if p.last_centroid:
                cx, cy = p.last_centroid
                box_color = (0, 0, 255) if p.is_flagged else (0, 255, 0)
                
                # Tag label
                tag = f"{p.class_name.upper()} #{p.track_id} | {p.total_distance_meters:.1f}m | Rest: {int(p.resting_seconds)}s"
                cv2.putText(frame, tag, (cx - 60, cy - 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)
                cv2.circle(frame, (cx, cy), 6, box_color, -1)

            if p.is_flagged:
                alert_banners.append(p.alert_message)

        # 4. Draw Alerts Banner (Bottom Screen)
        if alert_banners:
            banner_y = h - 60
            cv2.rectangle(frame, (0, banner_y), (w, h), (0, 0, 180), -1)
            cv2.line(frame, (0, banner_y), (w, banner_y), (0, 0, 255), 3)
            alert_text = alert_banners[0]
            cv2.putText(frame, alert_text, (20, banner_y + 40),
                        cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 2)

        return frame

    def process_stream(self, source=0, save_output=True, output_path="output_monitored.mp4"):
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"❌ Error: Cannot open video source: {source}")
            return

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        writer = None
        if save_output:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

        print(f"🎥 Tracking video stream ({w}x{h} @ {fps:.1f} FPS)... Press 'q' to stop.")

        frame_count = 0
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                current_time = time.time()

                # Run RT-DETR with ByteTrack persistence
                results = self.model.track(
                    source=frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    conf=0.35,
                    classes=[0, 1], # 0: dog, 1: cat
                    verbose=False
                )

                active_in_frame = []
                if results and results[0].boxes and results[0].boxes.id is not None:
                    boxes = results[0].boxes.xyxy.cpu().numpy()
                    track_ids = results[0].boxes.id.int().cpu().numpy()
                    cls_ids = results[0].boxes.cls.int().cpu().numpy()

                    for box, track_id, cls_id in zip(boxes, track_ids, cls_ids):
                        class_name = "dog" if cls_id == 0 else "cat"
                        if track_id not in self.profiles:
                            self.profiles[track_id] = AnimalProfile(track_id, class_name)
                        
                        profile = self.profiles[track_id]
                        x1, y1, x2, y2 = box.astype(int)
                        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                        
                        # Draw bounding box
                        color = (0, 0, 255) if profile.is_flagged else (0, 255, 0)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        
                        # Update motion & health state
                        profile.update_position(cx, cy, w, h, current_time)
                        active_in_frame.append(profile)

                # Render HUD Overlays
                annotated_frame = self.draw_hud(frame, active_in_frame)

                if writer:
                    writer.write(annotated_frame)

                cv2.imshow("RT-DETR Animal Welfare System", annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            cap.release()
            if writer:
                writer.release()
            cv2.destroyAllWindows()
            self.export_report()

    def export_report(self, filepath="caretaker_report.json"):
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_animals_monitored": len(self.profiles),
            "animals": {}
        }
        for tid, p in self.profiles.items():
            report["animals"][f"{p.class_name}_{tid}"] = {
                "id": tid,
                "type": p.class_name,
                "status": p.alert_status,
                "is_flagged": p.is_flagged,
                "total_distance_m": round(p.total_distance_meters, 2),
                "resting_seconds": round(p.resting_seconds, 1),
                "food_bowl_visits": p.food_bowl_visits,
                "secluded_corner_seconds": round(p.secluded_corner_seconds, 1),
                "alert_message": p.alert_message
            }
        
        with open(filepath, "w") as f:
            json.dump(report, f, indent=4)
        print(f"\n📋 Caretaker Telemetry Report saved to: {filepath}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Animal Monitoring with RT-DETR + ByteTrack")
    parser.add_argument("--weights", type=str, default=r"C:\animal\best.pt", help="Path to trained weights (best.pt)")
    parser.add_argument("--source", type=str, default="0", help="Video file or camera index")
    parser.add_argument("--output", type=str, default="output_monitored.mp4", help="Output annotated video path")
    args = parser.parse_args()

    # Convert numeric camera index if passed as digit
    src = int(args.source) if args.source.isdigit() else args.source
    
    system = AnimalMonitoringSystem(model_path=args.weights)
    system.process_stream(source=src, save_output=True, output_path=args.output)
