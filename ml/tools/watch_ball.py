"""
Watch normalized table coordinates stream by, to calibrate the goal lines.

    python -m tools.watch_ball                  # live camera
    python -m tools.watch_ball --video foo.mp4  # a recorded match
    python -m tools.watch_ball --no-model       # no Scout needed: just click

The numbers in config.py - GOAL_LINE_BLUE, GOAL_LINE_RED, GOAL_MOUTH_*,
ROD_POSITIONS - are placeholders copied from an example. They are almost
certainly wrong for our table, and wrong goal lines mean either missed
goals or phantom ones. This is how you replace them with measurements.

Two ways to use it:

  With the Scout trained: roll the ball slowly into each goal by hand and
  read off the x value where it crosses the line. That is your goal line.

  Before the Scout is trained (--no-model): click anywhere on the frozen
  frame and it prints that point's normalized coordinates. Click the goal
  line, click the edges of the goal mouth, click each rod. That is enough
  to fill in every constant without any trained model at all.
"""
import argparse
import sys
import time

import cv2

import config
from camera.threaded_camera import ThreadedCamera, VideoFileSource
from inference.homography import TableHomography


def build_homography():
    homography = TableHomography()
    if homography.load():
        print(f"Using saved corners from {config.CALIBRATION_PATH.name} "
              f"(source: {homography.source})")
        return homography
    raise SystemExit(
        "No calibration found. Run `python -m tools.calibrate_corners` first."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--video", help="read from a recorded match")
    parser.add_argument("--no-model", action="store_true",
                        help="skip the Scout; click points to read coordinates")
    parser.add_argument("--print-every", type=int, default=10,
                        help="print every Nth ball sighting (default 10)")
    args = parser.parse_args()

    homography = build_homography()

    detector = None
    if not args.no_model:
        try:
            from inference.pipeline import FoosballPipeline
            detector = FoosballPipeline(on_goal=None)
            detector.homography = homography
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"\nNo Scout model ({exc}).\nFalling back to click mode - "
                  f"click points on the frame to read their coordinates.\n")
            args.no_model = True

    source = (VideoFileSource(args.video, realtime=True).start() if args.video
              else ThreadedCamera().start())
    if not args.video:
        time.sleep(1.0)

    clicked = []

    def on_mouse(event, x, y, _flags, param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        scale = param["scale"]
        nx, ny = homography.to_normalized(x / scale, y / scale)
        clicked.append((nx, ny))
        print(f"  clicked -> normalized x={nx:.4f}  y={ny:.4f}")

    window = "watch_ball  (click to measure, q to quit)"
    cv2.namedWindow(window)
    mouse_param = {"scale": 1.0}
    cv2.setMouseCallback(window, on_mouse, mouse_param)

    print("\nx runs 0.0 (blue goal) -> 1.0 (red goal); y runs across the width.")
    print("Roll the ball into each goal and note where x crosses.\n")

    last_id = -1
    seen = 0
    try:
        while True:
            frame, last_id = source.wait_for_frame(last_id, timeout=1.0)
            if frame is None:
                if args.video and getattr(source, "exhausted", False):
                    break
                continue

            height, width = frame.shape[:2]
            scale = 1280 / width if width > 1280 else 1.0
            mouse_param["scale"] = scale
            preview = cv2.resize(frame, (int(width * scale), int(height * scale)))

            if detector is not None:
                ball = detector.detect_ball(frame)
                if ball is not None:
                    nx, ny = homography.to_normalized(ball[0], ball[1])
                    seen += 1
                    if seen % max(1, args.print_every) == 0:
                        print(f"  ball -> x={nx:.4f}  y={ny:.4f}  (conf {ball[2]:.2f})")
                    cx, cy = int(ball[0] * scale), int(ball[1] * scale)
                    cv2.circle(preview, (cx, cy), 10, (0, 0, 255), 2)
                    cv2.putText(preview, f"{nx:.3f}, {ny:.3f}", (cx + 14, cy),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # Draw the CURRENT config values so you can see how far off
            # they are before changing anything.
            for value, colour, label in (
                (config.GOAL_LINE_BLUE, (255, 160, 0), "GOAL_LINE_BLUE"),
                (config.GOAL_LINE_RED, (0, 80, 255), "GOAL_LINE_RED"),
            ):
                p1 = homography.to_pixels(value, config.GOAL_MOUTH_Y_MIN)
                p2 = homography.to_pixels(value, config.GOAL_MOUTH_Y_MAX)
                cv2.line(preview, (int(p1[0] * scale), int(p1[1] * scale)),
                         (int(p2[0] * scale), int(p2[1] * scale)), colour, 2)
                cv2.putText(preview, label, (int(p1[0] * scale) + 6,
                            int(p1[1] * scale) + 16),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 1)

            cv2.imshow(window, preview)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        source.stop()
        cv2.destroyAllWindows()

    if clicked:
        xs = [p[0] for p in clicked]
        ys = [p[1] for p in clicked]
        print(f"\n{len(clicked)} points clicked.")
        print(f"  x range: {min(xs):.4f} .. {max(xs):.4f}")
        print(f"  y range: {min(ys):.4f} .. {max(ys):.4f}")
        print("\nPut the numbers you measured into ml/config.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
