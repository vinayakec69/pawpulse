"""
PawPulse Desktop Live AI Media Player
Plays shelter CCTV footage with real-time RT-DETR-L (best.pt) detection on NVIDIA RTX 5080.

Controls:
  [Space] : Play / Pause
  [R]     : Rewind to Start
  [Q]/ESC : Exit Player
"""

import sys
import time
import cv2
from ultralytics import RTDETR

def main():
    video_path = "dashboard/assets/cctv_5min_shelter_pen2.mp4"
    model_path = "best.pt"

    print("=" * 60)
    print("🐾 PawPulse Desktop Live AI Media Player")
    print("🚀 Initializing best.pt on NVIDIA RTX 5080 GPU...")
    print("=" * 60)

    model = RTDETR(model_path)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error: Could not open video file '{video_path}'")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    delay_ms = max(1, int(1000 / fps))

    window_name = "PawPulse Live AI Player — RT-DETR-L (best.pt) Detection"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1080, 610)

    print("\n🟢 Media Player Active!")
    print("👉 Controls:")
    print("   [Space] : Pause / Resume playback")
    print("   [R]     : Restart video")
    print("   [Q]     : Close player\n")

    paused = False
    cur_annotated = None

    while True:
        if not paused:
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            cur_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

            # Run best.pt model prediction
            results = model.predict(source=frame, device=0, conf=0.25, verbose=False)
            cur_annotated = results[0].plot()

            # Top clinical banner
            proc_time = (time.time() - t0) * 1000.0
            inf_fps = 1000.0 / max(1.0, proc_time)
            cv2.rectangle(cur_annotated, (0, 0), (cur_annotated.shape[1], 40), (24, 21, 29), -1)
            cv2.putText(
                cur_annotated,
                f"PAWPULSE LIVE AI • best.pt (RT-DETR-L) • {inf_fps:.1f} FPS • Frame {cur_frame}/{total_frames}",
                (14, 26),
                cv2.FONT_HERSHEY_DUPLEX,
                0.48,
                (242, 140, 96),
                1,
                cv2.LINE_AA
            )
            cv2.putText(
                cur_annotated,
                "[Space]: Pause  [R]: Restart  [Q]: Exit",
                (cur_annotated.shape[1] - 320, 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                (122, 166, 77),
                1,
                cv2.LINE_AA
            )

            cv2.imshow(window_name, cur_annotated)

        key = cv2.waitKey(delay_ms if not paused else 50) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord(' '):
            paused = not paused
            if paused and cur_annotated is not None:
                pause_frame = cur_annotated.copy()
                cv2.putText(
                    pause_frame,
                    "⏸ PAUSED — Press [Space] to Resume",
                    (pause_frame.shape[1] // 2 - 190, pause_frame.shape[0] // 2),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.75,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA
                )
                cv2.imshow(window_name, pause_frame)
        elif key == ord('r'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    cap.release()
    cv2.destroyAllWindows()
    print("👋 Player closed.")

if __name__ == '__main__':
    main()
