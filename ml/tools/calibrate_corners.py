"""
Click the four corners of the table, once, and save them.

    python -m tools.calibrate_corners                 # from the live camera
    python -m tools.calibrate_corners --video foo.mp4 # from a recording
    python -m tools.calibrate_corners --image foo.jpg

This produces ml/calibration.json, which the pipeline falls back to when
the Architect keypoint model has not been trained yet. It unblocks
everything downstream - goal lines, zone tuning, the whole live pipeline -
without waiting on a second dataset and a second training run.

Our table gets nudged most days, so a saved calibration goes stale. Two
options: re-run this whenever it has been moved, or train the Architect
model, which re-finds the corners by itself every few seconds. The second
is the real fix; this is the thing that lets you make progress today.

Click order is fixed and matters:  top-left -> top-right -> bottom-right
-> bottom-left, where "top" is whatever the camera sees as the top edge.
Get it wrong and every coordinate downstream is mirrored or rotated.
"""
import argparse
import sys
import time

import cv2

import config
from camera.threaded_camera import ThreadedCamera, VideoFileSource, apply_crop
from inference.homography import TableHomography, CORNER_ORDER

INSTRUCTIONS = [
    "Click the TOP-LEFT corner of the playing surface",
    "Click the TOP-RIGHT corner",
    "Click the BOTTOM-RIGHT corner",
    "Click the BOTTOM-LEFT corner",
]


def grab_frame(args):
    if args.image:
        frame = cv2.imread(args.image)
        if frame is None:
            raise SystemExit(f"Could not read image: {args.image}")
        return apply_crop(frame) if args.crop else frame

    if args.video:
        source = VideoFileSource(args.video, apply_crop_to_frames=args.crop).start()
        frame, _ = source.wait_for_frame(-1)
        source.stop()
        if frame is None:
            raise SystemExit(f"Could not read a frame from {args.video}")
        return frame

    cam = ThreadedCamera().start()
    try:
        time.sleep(1.0)
        print("Press SPACE to freeze a frame to click on (q to quit).")
        last_id = -1
        while True:
            frame, last_id = cam.wait_for_frame(last_id)
            if frame is None:
                continue
            preview = cv2.resize(frame, (960, int(960 * frame.shape[0] / frame.shape[1])))
            cv2.putText(preview, "SPACE to freeze this frame", (10, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("Calibrate - pick a frame", preview)
            key = cv2.waitKey(1) & 0xFF
            if key == ord(" "):
                cv2.destroyAllWindows()
                return frame
            if key == ord("q"):
                cv2.destroyAllWindows()
                raise SystemExit("cancelled")
    finally:
        cam.stop()


def pick_corners(frame):
    height, width = frame.shape[:2]
    scale = 1280 / width if width > 1280 else 1.0
    canvas = cv2.resize(frame, (int(width * scale), int(height * scale)))
    display = canvas.copy()
    points = []

    def on_mouse(event, x, y, _flags, _param):
        if event != cv2.EVENT_LBUTTONDOWN or len(points) >= 4:
            return
        # Store in ORIGINAL frame pixels - the homography must be built in
        # the same coordinate space the detector reports ball positions in.
        points.append((x / scale, y / scale))
        cv2.circle(display, (x, y), 6, (0, 255, 0), -1)
        cv2.putText(display, f"{len(points)}: {CORNER_ORDER[len(points) - 1]}",
                    (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        if len(points) > 1:
            prev = points[-2]
            cv2.line(display, (int(prev[0] * scale), int(prev[1] * scale)),
                     (x, y), (0, 200, 0), 1)

    window = "Click the 4 corners  (u = undo, q = cancel)"
    cv2.namedWindow(window)
    cv2.setMouseCallback(window, on_mouse)

    while True:
        shown = display.copy()
        if len(points) < 4:
            cv2.putText(shown, INSTRUCTIONS[len(points)], (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        else:
            cv2.putText(shown, "ENTER to save, u to undo, q to cancel", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow(window, shown)

        key = cv2.waitKey(20) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            return None
        if key == ord("u") and points:
            points.pop()
            display = canvas.copy()
            for i, (px, py) in enumerate(points):
                sx, sy = int(px * scale), int(py * scale)
                cv2.circle(display, (sx, sy), 6, (0, 255, 0), -1)
                cv2.putText(display, f"{i + 1}: {CORNER_ORDER[i]}", (sx + 10, sy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        if key in (13, 10) and len(points) == 4:
            cv2.destroyAllWindows()
            return points


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--video", help="calibrate from a recorded match instead")
    parser.add_argument("--image", help="calibrate from a still image instead")
    parser.add_argument("--crop", action="store_true",
                        help="apply config's crop to the source (only for RAW "
                             "footage - recordings are already cropped)")
    parser.add_argument("--out", default=None, help="where to write calibration.json")
    args = parser.parse_args()

    frame = grab_frame(args)
    print(f"Frame is {frame.shape[1]}x{frame.shape[0]}.")
    corners = pick_corners(frame)
    if corners is None:
        print("Cancelled - nothing saved.")
        return 1

    homography = TableHomography()
    mapping = dict(zip(CORNER_ORDER, corners))
    if not homography.update(mapping, source="manual"):
        print("Those four points do not form a sensible quadrilateral "
              "(too close together, or clicked out of order). Try again.")
        return 1

    path = homography.save(args.out)
    print(f"\nSaved {path}")
    for name, (px, py) in mapping.items():
        nx, ny = homography.to_normalized(px, py)
        print(f"  {name:<13} pixel ({px:7.1f}, {py:7.1f}) -> normalized ({nx:.3f}, {ny:.3f})")
    print("\nSanity check: those normalized values should be very close to "
          "(0,0) (1,0) (1,1) (0,1) in that order.")
    print("Next: `python -m tools.watch_ball` to calibrate the goal lines.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
