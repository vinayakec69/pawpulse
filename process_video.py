"""
PawPulse Video Monitor & Telemetry Worker
RT-DETR-L + ByteTrack Animal Monitoring Engine
With Meowville Aesthetic HUD and H.264 MP4 Export
"""

import os
import cv2
import numpy as np
import time
import json
import subprocess
from collections import defaultdict, deque
from datetime import datetime
from ultralytics import RTDETR
import imageio_ffmpeg

# ==========================================
# CONFIGURATION & COLOR TOKENS (Meowville)
# ==========================================
PIXELS_PER_METER = 35.0        # Calibration factor
REST_SPEED_THRESHOLD = 0.12    # m/s

# Colors in BGR for OpenCV
COLOR_CREAM = (243, 248, 251)   # #FBF8F3
COLOR_MAUVE = (136, 87, 158)    # #9E5788 (Cats)
COLOR_PEACH = (96, 140, 242)    # #F28C60 (Dogs)
COLOR_SAGE  = (122, 166, 77)    # #4DA67A (Food Bowl / Healthy)
COLOR_ROSE  = (84, 84, 222)     # #DE5454 (Alerts / Secluded Corner)
COLOR_DARK  = (43, 43, 43)      # #2B2B2B

# Normalized Zones (relative to frame dimensions)
ZONES = {
    "food_bowl": {
        "name": "Food Bowl Area",
        "polygon": np.array([[0.04, 0.65], [0.30, 0.65], [0.30, 0.96], [0.04, 0.96]], np.float32),
        "color": COLOR_SAGE,
    },
    "secluded_corner": {
        "name": "Secluded Corner",
        "polygon": np.array([[0.70, 0.04], [0.96, 0.04], [0.96, 0.40], [0.70, 0.40]], np.float32),
        "color": COLOR_ROSE,
    }
}

class TrackState:
    def __init__(self, track_id, initial_cls):
        self.track_id = track_id
        self.class_votes = defaultdict(int)
        self.class_votes[initial_cls] += 1
        self.cls = initial_cls
        
        self.last_centroid = None
        self.trajectory = deque(maxlen=45)
        self.total_distance_m = 0.0
        self.consecutive_stationary_sec = 0.0
        self.resting_sec = 0.0
        self.is_resting = False
        self.in_corner_sec = 0.0
        self.in_bowl_sec = 0.0
        self.is_flagged = False
        self.alert_msg = "Normal activity"
        
    def update_class(self, detected_cls):
        self.class_votes[detected_cls] += 1
        # Majority vote determines species
        self.cls = max(self.class_votes.items(), key=lambda x: x[1])[0]

    def update_motion(self, cx, cy, dt, w, h):
        if self.last_centroid is not None and dt > 0:
            dx = cx - self.last_centroid[0]
            dy = cy - self.last_centroid[1]
            dist_px = np.hypot(dx, dy)
            dist_m = dist_px / PIXELS_PER_METER
            
            if dist_px > 2.5: # filter camera jitter
                self.total_distance_m += dist_m
                self.is_resting = False
                self.consecutive_stationary_sec = 0.0
            else:
                self.consecutive_stationary_sec += dt
                if self.consecutive_stationary_sec > 2.0:
                    self.is_resting = True
                    self.resting_sec += dt
        
        self.last_centroid = (cx, cy)
        self.trajectory.append((cx, cy))
        
        # Check zones
        nx, ny = cx / w, cy / h
        pt = (float(cx), float(cy))
        
        corner_pts = (ZONES["secluded_corner"]["polygon"] * [w, h]).astype(np.int32)
        bowl_pts = (ZONES["food_bowl"]["polygon"] * [w, h]).astype(np.int32)
        
        if cv2.pointPolygonTest(corner_pts, pt, False) >= 0:
            self.in_corner_sec += dt
        if cv2.pointPolygonTest(bowl_pts, pt, False) >= 0:
            self.in_bowl_sec += dt
            
        # Alert evaluation
        if self.in_corner_sec > 15.0 or self.consecutive_stationary_sec > 30.0:
            self.is_flagged = True
            self.alert_msg = f"Lethargic/Isolated: {int(self.in_corner_sec)}s in corner"
        else:
            self.is_flagged = False
            self.alert_msg = "Active & Healthy"

def draw_aesthetic_corner_box(img, x1, y1, x2, y2, color, corner_len=18, thickness=2):
    # Rounded sleek corner brackets [ ]
    cv2.line(img, (x1, y1), (x1 + corner_len, y1), color, thickness)
    cv2.line(img, (x1, y1), (x1, y1 + corner_len), color, thickness)
    
    cv2.line(img, (x2, y1), (x2 - corner_len, y1), color, thickness)
    cv2.line(img, (x2, y1), (x2, y1 + corner_len), color, thickness)
    
    cv2.line(img, (x1, y2), (x1 + corner_len, y2), color, thickness)
    cv2.line(img, (x1, y2), (x1, y2 - corner_len), color, thickness)
    
    cv2.line(img, (x2, y2), (x2 - corner_len, y2), color, thickness)
    cv2.line(img, (x2, y2), (x2, y2 - corner_len), color, thickness)

def draw_pill_badge(img, text, x, y, bg_color, text_color=(255, 255, 255), font_scale=0.45):
    font = cv2.FONT_HERSHEY_DUPLEX
    (tw, th), baseline = cv2.getTextSize(text, font, font_scale, 1)
    pad_x, pad_y = 8, 5
    
    bx1 = max(0, x - pad_x)
    by1 = max(0, y - th - pad_y)
    bx2 = min(img.shape[1], bx1 + tw + pad_x * 2)
    by2 = min(img.shape[0], by1 + th + pad_y * 2)
    
    # Semi-transparent pill background
    sub = img[by1:by2, bx1:bx2]
    if sub.shape[0] > 0 and sub.shape[1] > 0:
        colored = np.full_like(sub, bg_color)
        cv2.addWeighted(sub, 0.25, colored, 0.75, 0, sub)
        img[by1:by2, bx1:bx2] = sub
        cv2.rectangle(img, (bx1, by1), (bx2, by2), bg_color, 1)
        cv2.putText(img, text, (bx1 + pad_x, by1 + th + 2), font, font_scale, text_color, 1, cv2.LINE_AA)

def process_video_file(video_path, output_mp4, weights_path, conf_thresh=0.28):
    print(f"\n==========================================")
    print(f"🎬 Processing: {video_path}")
    print(f"📦 Model: {weights_path}")
    print(f"🎯 Output: {output_mp4}")
    print(f"==========================================")
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    os.makedirs(os.path.dirname(os.path.abspath(output_mp4)), exist_ok=True)
    temp_avi = output_mp4 + ".temp.avi"
    
    cap = cv2.VideoCapture(video_path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video dimensions: {w}x{h} @ {fps:.1f} FPS, total frames: {total_frames}")
    
    model = RTDETR(weights_path)
    tracks = {}
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    writer = cv2.VideoWriter(temp_avi, fourcc, fps, (w, h))
    
    frame_idx = 0
    t_start = time.time()
    dt = 1.0 / fps
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        
        # 1. Overlay semi-transparent monitoring zones
        overlay = frame.copy()
        for zid, zdata in ZONES.items():
            pts = (zdata["polygon"] * [w, h]).astype(np.int32)
            cv2.fillPoly(overlay, [pts], zdata["color"])
            cv2.polylines(overlay, [pts], True, zdata["color"], 2)
            cv2.putText(overlay, zdata["name"], (pts[0][0] + 6, pts[0][1] + 20),
                        cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.20, frame, 0.80, 0, frame)
        
        # 2. Track with ByteTrack
        results = model.track(
            source=frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=conf_thresh,
            classes=[0, 1], # 0: dog, 1: cat
            verbose=False
        )
        
        active_ids = []
        if results and len(results) > 0 and results[0].boxes and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().numpy()
            clss = results[0].boxes.cls.int().cpu().numpy()
            confs = results[0].boxes.conf.cpu().numpy()
            
            for box, tid, cid, cnf in zip(boxes, track_ids, clss, confs):
                active_ids.append(tid)
                species = "dog" if cid == 0 else "cat"
                
                if tid not in tracks:
                    tracks[tid] = TrackState(tid, species)
                
                track = tracks[tid]
                track.update_class(species)
                
                x1, y1, x2, y2 = box.astype(int)
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                track.update_motion(cx, cy, dt, w, h)
                
                # Visual styling
                primary_color = COLOR_ROSE if track.is_flagged else (COLOR_MAUVE if track.cls == "cat" else COLOR_PEACH)
                
                # Motion trail
                pts = list(track.trajectory)
                for i in range(1, len(pts)):
                    alpha = i / len(pts)
                    trail_thickness = max(1, int(alpha * 3))
                    cv2.line(frame, pts[i - 1], pts[i], primary_color, trail_thickness, cv2.LINE_AA)
                
                # Sleek corner box
                draw_aesthetic_corner_box(frame, x1, y1, x2, y2, primary_color, corner_len=max(12, int((x2 - x1) * 0.15)), thickness=2)
                
                # Tag badge
                icon = "🐱" if track.cls == "cat" else "🐶"
                state_lbl = "REST" if track.is_resting else f"{track.total_distance_m:.1f}m"
                badge_text = f"{icon} {track.cls.upper()} #{tid} • {state_lbl} • {cnf:.0%}"
                draw_pill_badge(frame, badge_text, x1, y1 - 8, primary_color, (255, 255, 255), font_scale=0.45)
        
        # 3. Top Status HUD Bar
        hud_bg = frame[:48, :].copy()
        cv2.rectangle(hud_bg, (0, 0), (w, 48), COLOR_DARK, -1)
        cv2.addWeighted(hud_bg, 0.75, frame[:48, :], 0.25, 0, frame[:48, :])
        
        cv2.putText(frame, "PAWPULSE • VETERINARY VISION (RT-DETR-L + BYTETRACK)",
                    (12, 20), cv2.FONT_HERSHEY_DUPLEX, 0.42, COLOR_CREAM, 1, cv2.LINE_AA)
        
        status_txt = f"TRACKING: {len(active_ids)} ANIMALS | RESIDENTS: {len(tracks)} | FRAME: {frame_idx}/{total_frames}"
        cv2.putText(frame, status_txt, (12, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.38, COLOR_SAGE, 1, cv2.LINE_AA)
        
        writer.write(frame)
        
        if frame_idx % 25 == 0 or frame_idx == total_frames:
            print(f"  Frame {frame_idx}/{total_frames} ({(frame_idx/max(1, total_frames))*100:.1f}%) | Active: {len(active_ids)}")
            
    cap.release()
    writer.release()
    
    elapsed = time.time() - t_start
    print(f"Inference completed in {elapsed:.2f}s ({(total_frames / max(1, elapsed)):.1f} FPS)")
    
    # 4. Transcode to web-standard H.264 MP4 with imageio-ffmpeg
    print(f"Encoding to standard web H.264 MP4: {output_mp4} ...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", temp_avi,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_mp4
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FFmpeg transcode warning: {res.stderr}")
    else:
        print(f"Transcoded successfully! Saved: {output_mp4} ({os.path.getsize(output_mp4)} bytes)")
    
    # Clean up temp AVI
    if os.path.exists(temp_avi):
        try:
            os.remove(temp_avi)
        except Exception:
            pass
            
    # 5. Export summary telemetry report
    report = {
        "timestamp": datetime.now().isoformat(),
        "video": os.path.basename(video_path),
        "total_frames": total_frames,
        "processed_fps": round(total_frames / max(0.01, elapsed), 1),
        "unique_animals_tracked": len(tracks),
        "animals": {}
    }
    for tid, t in tracks.items():
        report["animals"][f"{t.cls}_{int(tid)}"] = {
            "id": int(tid),
            "species": str(t.cls),
            "total_distance_m": round(float(t.total_distance_m), 2),
            "resting_sec": round(float(t.resting_sec), 1),
            "corner_dwell_sec": round(float(t.in_corner_sec), 1),
            "food_bowl_sec": round(float(t.in_bowl_sec), 1),
            "alert_status": str(t.alert_msg),
            "is_flagged": bool(t.is_flagged)
        }
    
    report_path = os.path.splitext(output_mp4)[0] + "_telemetry.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Telemetry report saved to: {report_path}")
    
    return report

if __name__ == "__main__":
    weights = r"C:\animal\runs\shelter_monitoring\train_rtdetr_l_cctv_1536\weights\best.pt"
    
    # Process both test videos
    cat_in = "test_cat.mp4"
    cat_out = r"C:\animal\dashboard\assets\monitored_cat.mp4"
    if os.path.exists(cat_in):
        process_video_file(cat_in, cat_out, weights)
        
    dog_in = "test_dog_hiera.mp4"
    dog_out = r"C:\animal\dashboard\assets\monitored_dog.mp4"
    if os.path.exists(dog_in):
        process_video_file(dog_in, dog_out, weights)
