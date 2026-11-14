"""
Generate a 5-Minute (300 seconds / 4500 frames @ 15 FPS) Realistic Shelter CCTV Video
Scenario:
- 0:00 - 1:15: Morning Activity (Buddy roaming, Shanti slow movement, Mochi stretching)
- 1:15 - 2:00: Feeding routine (visiting Food Bowl area)
- 2:00 - 5:00: Lethargy & Corner Isolation (Shanti retreats to Secluded Dark Corner and stays for 3 minutes!)
- Full CCTV OSD: Live ticking clock, camera ID, REC indicator, noise filter.
"""

import cv2
import numpy as np
import time
import os
import subprocess
import imageio_ffmpeg
from datetime import datetime, timedelta

def generate_5min_video(output_mp4="C:/animal/dashboard/assets/cctv_5min_shelter_pen2.mp4", duration_sec=300, fps=15):
    print("=" * 65)
    print(f"🎥 Generating {duration_sec}s (5-Minute) Authentic Shelter CCTV Footage")
    print(f"🎯 Output: {output_mp4}")
    print("=" * 65)

    os.makedirs(os.path.dirname(os.path.abspath(output_mp4)), exist_ok=True)
    temp_avi = output_mp4 + ".temp.avi"

    width, height = 800, 600
    total_frames = int(duration_sec * fps)

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    writer = cv2.VideoWriter(temp_avi, fourcc, fps, (width, height))

    # Base start time for CCTV clock
    start_time = datetime(2026, 11, 14, 8, 0, 0)

    # Waypoints for animals:
    # Food Bowl: (100, 480) [Bottom-Left]
    # Secluded Corner: (700, 100) [Top-Right]
    # Center Run: (400, 320)
    
    # State tracking
    buddy_pos = [350.0, 300.0]
    shanti_pos = [450.0, 350.0]
    mochi_pos = [180.0, 420.0]

    np.random.seed(42)

    t0 = time.time()
    for f in range(total_frames):
        current_sec = f / fps
        frame_time = start_time + timedelta(seconds=current_sec)

        # 1. Base Pen Floor (Concrete shelter texture with perspective grid)
        frame = np.full((height, width, 3), (32, 28, 36), dtype=np.uint8)

        # Grid lines (perspective)
        for i in range(0, width, 50):
            cv2.line(frame, (i, 0), (int(width * 0.5 + (i - width * 0.5) * 1.3), height), (42, 38, 48), 1)
        for j in range(0, height, 40):
            cv2.line(frame, (0, j), (width, j), (42, 38, 48), 1)

        # 2. Designated Physical Enclosure Zones
        # Food Bowl Zone (Bottom-Left)
        cv2.rectangle(frame, (40, 400), (220, 560), (45, 60, 45), -1)
        cv2.rectangle(frame, (40, 400), (220, 560), (60, 120, 70), 2)
        cv2.putText(frame, "FOOD BOWL AREA", (50, 425), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 160, 90), 1)
        # Draw physical food bowls
        cv2.circle(frame, (100, 480), 24, (70, 90, 80), -1)
        cv2.circle(frame, (160, 480), 24, (60, 80, 90), -1)

        # Secluded Dark Corner (Top-Right)
        cv2.rectangle(frame, (580, 30), (770, 220), (50, 35, 40), -1)
        cv2.rectangle(frame, (580, 30), (770, 220), (120, 50, 60), 2)
        cv2.putText(frame, "SECLUDED CORNER", (590, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 70, 80), 1)

        # 3. Simulate Animal Trajectories
        # BUDDY (Dog #1 - Healthy, active, plays, visits bowl)
        if current_sec < 75: # Morning roam
            buddy_pos[0] += np.random.uniform(-3, 3) + np.sin(current_sec * 0.5) * 4
            buddy_pos[1] += np.random.uniform(-3, 3) + np.cos(current_sec * 0.5) * 3
        elif current_sec < 130: # Feeding visit
            buddy_pos[0] += (110 - buddy_pos[0]) * 0.05 + np.random.uniform(-1, 1)
            buddy_pos[1] += (480 - buddy_pos[1]) * 0.05 + np.random.uniform(-1, 1)
        else: # Resting near center
            buddy_pos[0] += (380 - buddy_pos[0]) * 0.02 + np.random.uniform(-1.5, 1.5)
            buddy_pos[1] += (340 - buddy_pos[1]) * 0.02 + np.random.uniform(-1.5, 1.5)

        # SHANTI (Dog #3 - Lethargic, slow, retreats to corner at 120s and stays till end)
        if current_sec < 60: # Slow wandering
            shanti_pos[0] += np.random.uniform(-1.2, 1.2)
            shanti_pos[1] += np.random.uniform(-1.2, 1.2)
        elif current_sec < 120: # Drifting towards dark corner
            shanti_pos[0] += (680 - shanti_pos[0]) * 0.03
            shanti_pos[1] += (120 - shanti_pos[1]) * 0.03
        else: # Stationary in Secluded Dark Corner (LETHARGY TEST!)
            shanti_pos[0] = 685 + np.random.uniform(-0.4, 0.4)
            shanti_pos[1] = 125 + np.random.uniform(-0.4, 0.4)

        # MOCHI (Cat #2 - Feline resting curve)
        if current_sec < 90:
            mochi_pos[0] += np.random.uniform(-1.5, 1.5)
            mochi_pos[1] += np.random.uniform(-1.5, 1.5)
        else:
            mochi_pos[0] += (190 - mochi_pos[0]) * 0.02
            mochi_pos[1] += (440 - mochi_pos[1]) * 0.02

        # Clamp positions inside pen
        buddy_pos[0] = np.clip(buddy_pos[0], 60, width - 60)
        buddy_pos[1] = np.clip(buddy_pos[1], 60, height - 60)
        shanti_pos[0] = np.clip(shanti_pos[0], 60, width - 60)
        shanti_pos[1] = np.clip(shanti_pos[1], 60, height - 60)
        mochi_pos[0] = np.clip(mochi_pos[0], 60, width - 60)
        mochi_pos[1] = np.clip(mochi_pos[1], 60, height - 60)

        # 4. Render Animals (with realistic dog/cat silhouettes & features)
        # Buddy (Golden Mix Dog)
        bx, by = int(buddy_pos[0]), int(buddy_pos[1])
        cv2.ellipse(frame, (bx, by), (32, 22), 15, 0, 360, (110, 160, 200), -1) # Body
        cv2.circle(frame, (bx + 26, by - 6), 14, (120, 175, 215), -1) # Head
        cv2.circle(frame, (bx + 34, by - 8), 3, (20, 20, 20), -1) # Eye/Snout

        # Shanti (Indie Hound Dog - Curled/Lying down in corner)
        sx, sy = int(shanti_pos[0]), int(shanti_pos[1])
        if current_sec >= 120: # Curled posture (w/h > 1.5)
            cv2.ellipse(frame, (sx, sy), (35, 18), 0, 0, 360, (70, 95, 135), -1)
            cv2.circle(frame, (sx + 24, sy - 2), 12, (80, 105, 145), -1)
        else: # Standing
            cv2.ellipse(frame, (sx, sy), (28, 20), 0, 0, 360, (70, 95, 135), -1)
            cv2.circle(frame, (sx + 22, sy - 8), 12, (80, 105, 145), -1)

        # Mochi (Calico Cat - Compact cat silhouette)
        mx, my = int(mochi_pos[0]), int(mochi_pos[1])
        cv2.ellipse(frame, (mx, my), (20, 14), 0, 0, 360, (160, 130, 150), -1)
        cv2.circle(frame, (mx + 14, my - 6), 9, (180, 150, 170), -1)
        # Cat ears
        cv2.fillPoly(frame, [np.array([[mx+10, my-13], [mx+15, my-20], [mx+18, my-13]])], (180, 150, 170))
        cv2.fillPoly(frame, [np.array([[mx+16, my-13], [mx+21, my-20], [mx+24, my-13]])], (180, 150, 170))

        # 5. CCTV Surveillance OSD Bar (Top)
        cv2.rectangle(frame, (0, 0), (width, 40), (15, 15, 18), -1)
        
        # Blinking REC dot (every 1 second)
        if int(current_sec * 2) % 2 == 0:
            cv2.circle(frame, (20, 20), 6, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (32, 24), cv2.FONT_HERSHEY_DUPLEX, 0.45, (0, 0, 255), 1)

        cv2.putText(frame, "CAM 02 - PEN 2 NORTH [SHELTER 24/7 SURVEILLANCE]", (85, 24),
                    cv2.FONT_HERSHEY_DUPLEX, 0.45, (220, 220, 220), 1)

        # Timestamp Clock
        time_str = frame_time.strftime("%Y-%m-%d  %H:%M:%S")
        cv2.putText(frame, time_str, (width - 230, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 180), 1)

        # 6. Bottom OSD Status Bar
        cv2.rectangle(frame, (0, height - 32), (width, height), (15, 15, 18), -1)
        fps_str = f"FRAME: {f+1:04d}/{total_frames}  |  15.0 FPS  |  RTX 5080 CCTV INGESTION"
        cv2.putText(frame, fps_str, (16, height - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (160, 160, 160), 1)

        # Subtle CCTV Scanlines
        if f % 2 == 0:
            frame[0:height:4, :, :] = (frame[0:height:4, :, :] * 0.94).astype(np.uint8)

        writer.write(frame)

        if (f + 1) % (fps * 30) == 0 or (f + 1) == total_frames:
            sec_done = int((f + 1) / fps)
            print(f"  Rendered {sec_done}s / {duration_sec}s ({(f+1)/total_frames*100:.1f}%) ...")

    writer.release()
    render_time = time.time() - t0
    print(f"Frame rendering complete in {render_time:.1f}s ({(total_frames/render_time):.1f} FPS)!")

    # Transcode to web-standard H.264 MP4 with FFmpeg
    print("Transcoding to H.264 MP4 with FFmpeg...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe, "-y",
        "-i", temp_avi,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_mp4
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    if os.path.exists(temp_avi):
        os.remove(temp_avi)

    size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
    print(f"🎉 Created 5-minute CCTV video: {output_mp4} ({size_mb:.2f} MB)")
    return output_mp4

if __name__ == "__main__":
    generate_5min_video()
