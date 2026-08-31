"""
Capture raw frames by hand.

    # Empty table, from several angles - trains the Architect (keypoints).
    python -m data_collection.record_dataset --mode table --out datasets/raw/table

    # Ad-hoc gameplay stills, when you are not running the vision service.
    python -m data_collection.record_dataset --mode gameplay --out datasets/raw/gameplay

NOTE ON GAMEPLAY MODE: prefer letting `vision_service.py` record whole
matches and then pulling stills out with
`python -m data_collection.extract_frames`. Sampling a .jpg every half
second throws away 179 of every 180 frames, and the ones it throws away
are the fast, motion-blurred ones around goals - exactly the frames the
detector most needs to learn from. This mode is for quick one-offs.

TABLE MODE is different and still the right tool: the Architect needs the
EMPTY table seen from varied angles, heights and lighting, which is not
something that falls out of ordinary match footage.
"""
import argparse
import sys
import time
from pathlib import Path

import cv2

import config
from camera.threaded_camera import ThreadedCamera


def record_table(cam, out_dir):
    print("TABLE MODE - SPACE saves a frame, 'q' quits.")
    print("Walk around the EMPTY table: each corner, low and high angles,")
    print("different distances, lights on and off. ~100 varied frames.")
    print("Variety is the whole point - 100 near-identical frames teach the")
    print("model almost nothing beyond the first one.")
    last_id, saved = -1, 0
    while True:
        frame, last_id = cam.wait_for_frame(last_id)
        if frame is None:
            continue
        preview = cv2.resize(frame, (960, int(960 * frame.shape[0] / frame.shape[1])))
        cv2.putText(preview, f"Saved: {saved}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Table capture - SPACE to save, q to quit", preview)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(" "):
            path = out_dir / f"table_{int(time.time() * 1000)}.jpg"
            cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved += 1
            print(f"saved {path.name} ({saved} total)")
        elif key == ord("q"):
            break
    cv2.destroyAllWindows()
    return saved


def record_gameplay(cam, out_dir, interval):
    print(f"GAMEPLAY MODE - sampling every {interval}s. 'q' to stop.")
    print("(Consider `vision_service.py` + `extract_frames.py` instead - see")
    print(" this file's docstring for why.)")
    last_id, saved, last_save = -1, 0, 0.0
    while True:
        frame, last_id = cam.wait_for_frame(last_id)
        if frame is None:
            continue
        now = time.time()
        preview = cv2.resize(frame, (960, int(960 * frame.shape[0] / frame.shape[1])))
        cv2.putText(preview, f"Saved: {saved}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Gameplay capture - q to stop", preview)

        if now - last_save >= interval:
            path = out_dir / f"gameplay_{int(now * 1000)}.jpg"
            cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved += 1
            last_save = now

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()
    return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["table", "gameplay"], required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--interval", type=float, default=0.5,
                        help="seconds between saved frames in gameplay mode")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    cam = ThreadedCamera().start()
    time.sleep(1.0)   # let the sensor settle
    try:
        if args.mode == "table":
            saved = record_table(cam, out_dir)
        else:
            saved = record_gameplay(cam, out_dir, args.interval)
    finally:
        cam.stop()
    print(f"Done. {saved} frames in {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
