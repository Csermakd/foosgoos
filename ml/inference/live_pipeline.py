"""
Watch-and-print runner. No backend, no recording, no side effects.

    python -m inference.live_pipeline                    # live camera
    python -m inference.live_pipeline --source game.mp4  # a recorded match
    python -m inference.live_pipeline --headless         # no video window

Use this while tuning: point it at the table (or replay a recording) and
watch what it calls. When the goals it prints match the goals you saw,
run `python -m vision_service` instead - that is the one that records
video and actually posts into the app.

Replaying a recording is the fast way to tune config.py: change a goal
line, re-run, see immediately whether the same 12 goals still fire. You
do not need the table, or a camera, or even to be in the building.
"""
import argparse
import sys
import time

import config
from inference.pipeline import FoosballPipeline, draw_overlay


def build_source(args):
    if args.source:
        from camera.threaded_camera import VideoFileSource
        return VideoFileSource(args.source, realtime=args.realtime).start()
    from camera.threaded_camera import ThreadedCamera
    camera = ThreadedCamera().start()
    time.sleep(1.0)
    return camera


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", help="path to a recorded .mp4 (default: live camera)")
    parser.add_argument("--realtime", action="store_true",
                        help="with --source, play at the recording's real speed")
    parser.add_argument("--headless", action="store_true", help="no preview window")
    args = parser.parse_args()

    goals = []
    pipeline = FoosballPipeline(on_goal=goals.append)
    print(f"[live] calibration source: {pipeline.homography.source}")
    print(f"[live] goal lines: blue<={config.GOAL_LINE_BLUE}  "
          f"red>={config.GOAL_LINE_RED}  mouth y {config.GOAL_MOUTH_Y_MIN}"
          f"-{config.GOAL_MOUTH_Y_MAX}")

    source = build_source(args)
    is_file = not source.is_live
    last_id = -1
    frames = 0
    started = time.time()
    window_start = started
    window_frames = 0

    try:
        while True:
            frame, last_id = source.wait_for_frame(last_id, timeout=1.0)
            if frame is None:
                if is_file and source.exhausted:
                    break
                continue

            frames += 1
            # Replaying a file: drive the clock from the VIDEO's timeline,
            # not the wall clock, or every timing threshold in GameState
            # (cooldowns, disappearance timeouts) means something different
            # than it will at the table.
            now = (started + source.timestamp_ms / 1000.0) if is_file else time.time()
            video_ts = source.timestamp_ms if is_file else None

            result = pipeline.process(frame, now=now, video_ts_ms=video_ts)
            if result.goal is not None:
                where = (f" at {result.goal.video_ts_ms / 1000:.1f}s"
                         if result.goal.video_ts_ms is not None else "")
                print(f"[GOAL] {result.goal.describe()}{where}")

            if not args.headless:
                import cv2
                cv2.imshow("Foosgoos live (q to quit)",
                           draw_overlay(frame, result, pipeline.homography))
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            window_frames += 1
            if time.time() - window_start > 5.0:
                fps = window_frames / (time.time() - window_start)
                print(f"[live] {fps:.1f} fps processed | ball seen in "
                      f"{pipeline.game_state.detection_rate:.0%} of frames")
                window_start = time.time()
                window_frames = 0
    except KeyboardInterrupt:
        print("\n[live] interrupted")
    finally:
        source.stop()
        if not args.headless:
            import cv2
            cv2.destroyAllWindows()

    elapsed = time.time() - started
    print(f"\n--- {frames} frames in {elapsed:.1f}s ({frames / max(elapsed, 1e-6):.1f} fps) ---")
    print(f"goals detected: {len(goals)}")
    for i, goal in enumerate(goals, 1):
        stamp = (f"{goal.video_ts_ms / 1000:7.1f}s" if goal.video_ts_ms is not None
                 else time.strftime("%H:%M:%S", time.localtime(goal.timestamp)))
        print(f"  {i:2}. {stamp}  {goal.team:<4}  {goal.detector:<14} "
              f"conf {goal.confidence:.2f}  bar hint: {goal.bar_hint}")
    for key, value in pipeline.summary().items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
