"""
Capture raw frames for annotation in Roboflow (or CVAT).

Two modes, matching ARCHITECTURE.md Part 4:
  table    - walk around the EMPTY table, press SPACE to save a frame
             from varied angles/heights/distances. Aim for 100+ images.
             This trains the Architect (keypoint) model.
  gameplay - continuously samples frames during live play at a fixed
             interval, building a natural distribution of ball/player
             positions. Aim for 300+ images. This trains the Scout
             (object detection) model.

Usage:
  python -m data_collection.record_dataset --mode table --out datasets/raw/table
  python -m data_collection.record_dataset --mode gameplay --out datasets/raw/gameplay --interval 0.5
"""
import argparse
import time
from pathlib import Path

import cv2

from camera.threaded_camera import ThreadedCamera
import config


def record_table(cam: ThreadedCamera, out_dir: Path):
    print("TABLE MODE - press SPACE to save a frame, 'q' to quit.")
    print("Walk around the empty table: corners, low angles, high angles, "
          "different distances. You want the Architect model to generalize.")
    last_id = -1
    saved = 0
    while True:
        frame, last_id = cam.wait_for_frame(last_id)
        if frame is None:
            continue
        preview = cv2.resize(frame, (960, 540))
        cv2.putText(preview, f"Saved: {saved}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Table capture - SPACE to save, q to quit", preview)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            path = out_dir / f"table_{int(time.time() * 1000)}.jpg"
            cv2.imwrite(str(path), frame)
            saved += 1
            print(f"Saved {path.name} ({saved} total)")
        elif key == ord('q'):
            break
    cv2.destroyAllWindows()
    print(f"Done. Saved {saved} frames to {out_dir}")


def record_gameplay(cam: ThreadedCamera, out_dir: Path, interval: float):
    print(f"GAMEPLAY MODE - sampling every {interval}s during play. Press 'q' to stop.")
    last_id = -1
    saved = 0
    last_save_time = 0.0
    while True:
        frame, last_id = cam.wait_for_frame(last_id)
        if frame is None:
            continue

        now = time.time()
        preview = cv2.resize(frame, (960, 540))
        cv2.putText(preview, f"Saved: {saved}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Gameplay capture - q to stop", preview)

        if now - last_save_time >= interval:
            path = out_dir / f"gameplay_{int(now * 1000)}.jpg"
            cv2.imwrite(str(path), frame)
            saved += 1
            last_save_time = now

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()
    print(f"Done. Saved {saved} frames to {out_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["table", "gameplay"], required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--interval", type=float, default=0.5,
                         help="Seconds between saved frames in gameplay mode")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    cam = ThreadedCamera(
        src=config.CAMERA_INDEX,
        width=config.FRAME_WIDTH,
        height=config.FRAME_HEIGHT,
        fps=config.TARGET_FPS,
        exposure=config.EXPOSURE,
    ).start()
    time.sleep(1.0)  # let the sensor warm up

    try:
        if args.mode == "table":
            record_table(cam, out_dir)
        else:
            record_gameplay(cam, out_dir, args.interval)
    finally:
        cam.stop()


if __name__ == "__main__":
    main()
