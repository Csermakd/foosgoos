"""
Live inference loop - run this while a game is being played.

It:
  1. Pulls fresh frames from the fixed threaded camera (no phantom frames)
  2. Runs the Scout model every frame to find the ball
  3. Runs the Architect model occasionally to (re)compute the homography
  4. Converts the ball's pixel position -> normalized table position
  5. Feeds that into GameState to detect goals
  6. Calls a callback when a goal is detected - wire this to your
     FastAPI backend / websocket so the frontend pops the GoalModal
     you already built, pre-filled with a guess (team + likely bar),
     for a human to confirm or correct.

Usage:
  python -m inference.live_pipeline
"""
import time
import cv2
from ultralytics import YOLO

import config
from camera.threaded_camera import ThreadedCamera
from inference.homography import TableHomography
from inference.game_state import GameState, GoalEvent


def on_goal_detected(event: GoalEvent):
    """
    Wire this up to your real backend. For now it just prints - e.g.
    replace with a POST to your FastAPI matches router, or push over
    a websocket so the frontend opens GoalModal pre-filled with a
    guess, which the human then confirms or edits.
    """
    ts = time.strftime('%H:%M:%S', time.localtime(event.timestamp))
    print(f"[GOAL] {event.scoring_team.upper()} scored, likely off the "
          f"{event.likely_bar} ({ts})")
    # example:
    # import requests
    # requests.post(f"http://localhost:8000/matches/{match_id}/goal", json={
    #     "team": event.scoring_team, "likely_bar": event.likely_bar
    # })


def find_ball_center(scout_results):
    """Returns (px, py) of the highest-confidence 'ball' box, or None."""
    best = None
    for r in scout_results:
        if r.boxes is None:
            continue
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            if config.SCOUT_CLASSES[cls_id] != config.BALL_CLASS_NAME:
                continue
            if conf < config.SCOUT_CONF_THRESHOLD:
                continue
            if best is None or conf > best[0]:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                best = (conf, (x1 + x2) / 2, (y1 + y2) / 2)
    if best is None:
        return None
    return best[1], best[2]


def find_corners(architect_results):
    """Returns {"top_left": (x,y), ...} from the pose model output."""
    for r in architect_results:
        if r.keypoints is None or len(r.keypoints) == 0:
            continue
        kps = r.keypoints[0].xy[0].tolist()  # order must match ARCHITECT_KEYPOINTS
        if len(kps) < 4:
            continue
        return dict(zip(config.ARCHITECT_KEYPOINTS, kps))
    return None


def main():
    print("Loading models...")
    scout = YOLO(str(config.SCOUT_MODEL_PATH))
    architect = YOLO(str(config.ARCHITECT_MODEL_PATH))

    homography = TableHomography(refresh_interval_s=config.ARCHITECT_REFRESH_INTERVAL_S)
    game_state = GameState(on_goal=on_goal_detected)

    cam = ThreadedCamera(
        src=config.CAMERA_INDEX,
        width=config.FRAME_WIDTH,
        height=config.FRAME_HEIGHT,
        fps=config.TARGET_FPS,
        exposure=config.EXPOSURE,
    ).start()
    time.sleep(1.0)

    last_id = -1
    print("Live pipeline running. Press 'q' in the preview window to stop.")
    try:
        while True:
            frame, last_id = cam.wait_for_frame(last_id)
            if frame is None:
                continue

            if homography.needs_refresh():
                architect_results = architect.predict(frame, verbose=False)
                corners = find_corners(architect_results)
                if corners:
                    homography.update(corners)

            scout_results = scout.predict(frame, verbose=False)
            ball_px = find_ball_center(scout_results)

            nx = ny = None
            if ball_px is not None and homography.is_calibrated:
                nx, ny = homography.to_normalized(*ball_px)

            game_state.update(nx, ny)

            preview = cv2.resize(frame, (960, 540))
            if ball_px is not None:
                sx, sy = int(ball_px[0] / 2), int(ball_px[1] / 2)
                cv2.circle(preview, (sx, sy), 8, (0, 0, 255), 2)
            cv2.imshow("Foosgoos Live", preview)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cam.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
