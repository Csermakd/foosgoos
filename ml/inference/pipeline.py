"""
The frame-processing core, shared by live play and offline replay.

Everything that turns a frame into a possible goal lives here, so the
live vision service and the evaluation harness run *identical* logic.
That matters: tuning goal lines against recorded footage is only
meaningful if the thing you tuned is the thing that will run tonight.

    frame -> Scout (ball in pixels)
          -> homography (pixels -> normalized table coords)
          -> GameState (trajectory -> goal events)

The Architect model re-runs on a timer, because our table is not bolted
down and gets nudged a little every day.
"""
import time
from dataclasses import dataclass, field
from typing import Optional, Tuple

import config
from inference.homography import TableHomography
from inference.game_state import GameState, DetectedGoal
from inference import zones


@dataclass
class FrameResult:
    frame_id: int
    ball_px: Optional[Tuple[float, float]] = None
    ball_norm: Optional[Tuple[float, float]] = None
    ball_conf: Optional[float] = None
    goal: Optional[DetectedGoal] = None
    calibrated: bool = False
    timings_ms: dict = field(default_factory=dict)


class FoosballPipeline:
    def __init__(self, scout_path=None, architect_path=None,
                 on_goal=None, allow_manual_calibration=None):
        # Imported here, not at module import time, so the unit tests and
        # the calibration tools do not need torch installed.
        from ultralytics import YOLO

        scout_path = scout_path or config.SCOUT_MODEL_PATH
        architect_path = architect_path or config.ARCHITECT_MODEL_PATH
        if allow_manual_calibration is None:
            allow_manual_calibration = config.ALLOW_MANUAL_CALIBRATION

        if not str(scout_path) or not _exists(scout_path):
            raise FileNotFoundError(
                f"Scout weights not found at {scout_path}. Train the model "
                f"first (see ml/README_ML_PIPELINE.md, steps 2-5) - there is "
                f"no ball detection without it."
            )

        print(f"[pipeline] loading Scout from {scout_path}")
        self.scout = YOLO(str(scout_path))
        self.ball_class_id = _resolve_ball_class(self.scout)

        self.architect = None
        if _exists(architect_path):
            print(f"[pipeline] loading Architect from {architect_path}")
            self.architect = YOLO(str(architect_path))

        self.homography = TableHomography()
        self.game_state = GameState(on_goal=on_goal)
        self._frame_id = 0
        self._architect_failures = 0

        if self.architect is None:
            if not allow_manual_calibration:
                raise FileNotFoundError(
                    f"Architect weights not found at {architect_path} and "
                    f"manual calibration is disabled."
                )
            if self.homography.load():
                print(f"[pipeline] no Architect model - using saved corners "
                      f"from {config.CALIBRATION_PATH.name}")
                print(f"[pipeline] NOTE: the table drifts daily. Re-run "
                      f"`python -m tools.calibrate_corners` whenever it has "
                      f"been moved, or train the Architect to stop caring.")
            else:
                raise RuntimeError(
                    "No Architect model and no saved calibration. Run "
                    "`python -m tools.calibrate_corners` to click the four "
                    "table corners once, or train the Architect model."
                )

    # -- per frame -------------------------------------------------

    def process(self, frame, now=None, video_ts_ms=None) -> FrameResult:
        now = time.time() if now is None else now
        self._frame_id += 1
        result = FrameResult(frame_id=self._frame_id)
        timings = result.timings_ms

        # 1. Re-find the table, occasionally. Only meaningful if we have
        #    the Architect - with a manual calibration the corners are
        #    fixed until someone re-clicks them.
        if self.architect is not None and self.homography.needs_refresh():
            t0 = time.perf_counter()
            self._refresh_homography(frame)
            timings["architect"] = (time.perf_counter() - t0) * 1000

        result.calibrated = self.homography.is_calibrated

        # 2. Find the ball, every single frame.
        t0 = time.perf_counter()
        ball = self.detect_ball(frame)
        timings["scout"] = (time.perf_counter() - t0) * 1000

        nx = ny = None
        if ball is not None:
            result.ball_px = (ball[0], ball[1])
            result.ball_conf = ball[2]
            if self.homography.is_calibrated:
                nx, ny = self.homography.to_normalized(ball[0], ball[1])
                result.ball_norm = (nx, ny)

        # 3. Trajectory -> goals. Called EVERY frame, including frames
        #    with no ball: an absent ball is what the disappearance
        #    detector is looking for.
        if self.homography.is_calibrated:
            result.goal = self.game_state.update(nx, ny, now=now,
                                                 video_ts_ms=video_ts_ms)
        return result

    def detect_ball(self, frame):
        """Highest-confidence ball detection as (px, py, conf), or None."""
        results = self.scout.predict(
            frame, verbose=False, conf=config.SCOUT_CONF_THRESHOLD,
            imgsz=config.SCOUT_IMG_SIZE,
        )
        best = None
        for r in results:
            if r.boxes is None:
                continue
            names = r.names   # authoritative class map, straight from the
                              # weights - never a hand-written list that
                              # can silently drift from the exported
                              # data.yaml and make us track a shirt.
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if names.get(cls_id) != config.BALL_CLASS_NAME:
                    continue
                conf = float(box.conf[0])
                if best is not None and conf <= best[2]:
                    continue
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                best = ((x1 + x2) / 2, (y1 + y2) / 2, conf)
        return best

    # -- table calibration -----------------------------------------

    def _refresh_homography(self, frame):
        corners = self.find_corners(frame)
        if corners is None:
            self._architect_failures += 1
            if self._architect_failures % 30 == 1:
                print(f"[pipeline] Architect could not find the table "
                      f"({self._architect_failures} misses). Keeping the last "
                      f"good calibration.")
            return
        self._architect_failures = 0
        self.homography.update(corners, source="architect")

    def find_corners(self, frame):
        results = self.architect.predict(
            frame, verbose=False, conf=config.ARCHITECT_CONF_THRESHOLD,
        )
        for r in results:
            if r.keypoints is None or len(r.keypoints) == 0:
                continue
            points = r.keypoints[0].xy[0].tolist()
            if len(points) < len(config.ARCHITECT_KEYPOINTS):
                continue
            return dict(zip(config.ARCHITECT_KEYPOINTS, points))
        return None

    # -- misc ------------------------------------------------------

    def reset(self):
        self.game_state.reset()
        self._frame_id = 0

    def summary(self) -> dict:
        s = dict(self.game_state.stats)
        s["detection_rate"] = round(self.game_state.detection_rate, 3)
        s["calibration_source"] = self.homography.source
        s["table_bumps"] = self.homography.bump_count
        return s


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------

def _exists(path) -> bool:
    from pathlib import Path
    try:
        return Path(path).exists()
    except (TypeError, OSError):
        return False


def _resolve_ball_class(model) -> Optional[int]:
    """Check the weights actually contain a 'ball' class, and say so
    clearly if they do not - a silent mismatch here looks exactly like
    'the model is bad' when really it is looking for the wrong label."""
    names = getattr(model, "names", None) or {}
    by_name = {v: k for k, v in names.items()}
    if config.BALL_CLASS_NAME in by_name:
        return by_name[config.BALL_CLASS_NAME]
    if len(names) == 1:
        only_id, only_name = next(iter(names.items()))
        print(f"[pipeline] WARNING: model's single class is '{only_name}', not "
              f"'{config.BALL_CLASS_NAME}'. Treating it as the ball.")
        config.BALL_CLASS_NAME = only_name
        return only_id
    raise ValueError(
        f"These weights have no '{config.BALL_CLASS_NAME}' class - they know "
        f"about {sorted(names.values())}. Check you exported the right "
        f"Roboflow project, or set BALL_CLASS_NAME in config.py."
    )


def draw_overlay(frame, result: FrameResult, homography=None, scale=None):
    """Debug overlay. Scale is computed from the actual frame size rather
    than assuming a fixed 2x, which is what made the first draft draw the
    ball marker in the wrong place once the crop was enabled."""
    import cv2

    height, width = frame.shape[:2]
    target_w = 960
    scale = scale if scale is not None else target_w / width
    preview = cv2.resize(frame, (int(width * scale), int(height * scale)))

    if homography is not None and homography.is_calibrated:
        for line_x, colour in ((config.GOAL_LINE_BLUE, (255, 160, 0)),
                               (config.GOAL_LINE_RED, (0, 80, 255))):
            try:
                p1 = homography.to_pixels(line_x, config.GOAL_MOUTH_Y_MIN)
                p2 = homography.to_pixels(line_x, config.GOAL_MOUTH_Y_MAX)
            except RuntimeError:
                continue
            cv2.line(preview,
                     (int(p1[0] * scale), int(p1[1] * scale)),
                     (int(p2[0] * scale), int(p2[1] * scale)), colour, 2)

    if result.ball_px is not None:
        cx, cy = int(result.ball_px[0] * scale), int(result.ball_px[1] * scale)
        cv2.circle(preview, (cx, cy), 10, (0, 0, 255), 2)
        if result.ball_norm is not None:
            cv2.putText(preview,
                        f"({result.ball_norm[0]:.3f}, {result.ball_norm[1]:.3f})",
                        (cx + 14, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 255), 1)

    status = "CALIBRATED" if result.calibrated else "NO TABLE CALIBRATION"
    cv2.putText(preview, status, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0) if result.calibrated else (0, 0, 255), 2)
    return preview
