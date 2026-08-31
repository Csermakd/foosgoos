"""
Central configuration for the Foosgoos ML pipeline.

Anything you might reasonably want to change per-machine (camera index,
backend URL) can also be set with an environment variable, so the camera
PC and a laptop can share the same checked-in file.
"""
import os
import sys
from pathlib import Path


def _env_int(name, default):
    value = os.getenv(name)
    return int(value) if value not in (None, "") else default


def _env_float(name, default):
    value = os.getenv(name)
    return float(value) if value not in (None, "") else default


def _env_bool(name, default):
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models"
DATASET_DIR = PROJECT_ROOT / "datasets"
RECORDINGS_DIR = Path(os.getenv("FOOSGOOS_RECORDINGS_DIR", PROJECT_ROOT / "recordings"))
CALIBRATION_PATH = PROJECT_ROOT / "calibration.json"

ARCHITECT_MODEL_PATH = MODELS_DIR / "table_v1.pt"   # keypoint / pose model
SCOUT_MODEL_PATH = MODELS_DIR / "gameplay_v1.pt"    # object detection model

# ------------------------------------------------------------------
# Backend
# ------------------------------------------------------------------
# The vision service talks to FastAPI over HTTP only - it never imports
# from backend/. Point this at the machine running uvicorn.
API_URL = os.getenv("FOOSGOOS_API_URL", "http://localhost:8000")
API_TIMEOUT_S = _env_float("FOOSGOOS_API_TIMEOUT", 5.0)
# How often the vision service asks "is a game running?"
SESSION_POLL_INTERVAL_S = _env_float("FOOSGOOS_POLL_INTERVAL", 2.0)

# ------------------------------------------------------------------
# Camera
# ------------------------------------------------------------------
CAMERA_INDEX = _env_int("FOOSGOOS_CAMERA_INDEX", 0)
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
TARGET_FPS = 90

# Exposure is a stop-like value on this camera: MORE negative = FASTER
# shutter = less motion blur but a darker image. ARCHITECTURE.md calls for
# -6 or -7 (~7.8ms) to freeze a 30mph ball; that needs the overhead LED on.
# If frames come out black, walk it back towards -4 and add more light -
# do not "fix" darkness by raising this, or the ball smears and the
# detector loses it exactly when a goal is being scored.
EXPOSURE = _env_float("FOOSGOOS_EXPOSURE", -6)

# OpenCV needs a different capture backend per OS. The old hardcoded
# CAP_MSMF is Windows-only and silently fails to open the camera on macOS
# and Linux, which is why this is now picked at runtime.
if sys.platform.startswith("win"):
    CAMERA_BACKEND = "msmf"
elif sys.platform == "darwin":
    CAMERA_BACKEND = "avfoundation"
else:
    CAMERA_BACKEND = "v4l2"
CAMERA_BACKEND = os.getenv("FOOSGOOS_CAMERA_BACKEND", CAMERA_BACKEND)

# ------------------------------------------------------------------
# Digital crop (zoom)
# Slices the raw frame down to just the table. Set any value to None to
# disable cropping entirely.
#
# IMPORTANT: this crop is applied inside the capture thread, so it affects
# recorded frames, training images AND live inference alike. Change it and
# every previously trained model is looking at a differently framed world.
# If you re-crop, re-collect and retrain.
# ------------------------------------------------------------------
CROP_Y1 = 200
CROP_Y2 = 880
CROP_X1 = 400
CROP_X2 = 1520

# ------------------------------------------------------------------
# Architect model (keypoint detector -> table corners)
# ------------------------------------------------------------------
# Order matters - this MUST match the order you label in Roboflow.
ARCHITECT_KEYPOINTS = ["top_left", "top_right", "bottom_right", "bottom_left"]

# Our table is NOT bolted down - it gets nudged a little every day - so
# re-finding the corners regularly is the whole point of this model.
ARCHITECT_REFRESH_INTERVAL_S = _env_float("FOOSGOOS_ARCHITECT_REFRESH", 10.0)
# A corner moving more than this many pixels means the table was bumped.
ARCHITECT_BUMP_THRESHOLD_PX = _env_float("FOOSGOOS_BUMP_THRESHOLD", 20.0)
ARCHITECT_CONF_THRESHOLD = _env_float("FOOSGOOS_ARCHITECT_CONF", 0.5)

# Until the Architect is trained, the pipeline falls back to the corners
# saved by tools/calibrate_corners.py. Set this False to require the model.
ALLOW_MANUAL_CALIBRATION = _env_bool("FOOSGOOS_ALLOW_MANUAL_CALIBRATION", True)

# ------------------------------------------------------------------
# Scout model (object detector -> ball)
# ------------------------------------------------------------------
# We look classes up by NAME from the model itself (result.names), never
# by index into a list written here - a list that silently disagrees with
# the exported data.yaml would make us track a player as if it were the
# ball. This is only the ball's name and the eventual full class list for
# reference.
BALL_CLASS_NAME = "ball"
SCOUT_CONF_THRESHOLD = _env_float("FOOSGOOS_SCOUT_CONF", 0.35)
SCOUT_IMG_SIZE = _env_int("FOOSGOOS_SCOUT_IMGSZ", 640)

# v1 trains ONE class. Labelling ten interleaved rod variants from
# overhead is slow, error-prone, and buys nothing the goal logic uses.
SCOUT_CLASSES_V1 = ["ball"]
# The eventual set, once ball detection is solid and we want rod contact:
SCOUT_CLASSES_FUTURE = [
    "ball",
    "player_red", "player_blue",
    "player_red_two_bar", "player_blue_two_bar",
    "player_red_three_bar", "player_blue_three_bar",
    "player_red_five_bar", "player_blue_five_bar",
    "player_red_goalie_bar", "player_blue_goalie_bar",
]

# ------------------------------------------------------------------
# Goal detection (normalized table coords: x in 0..1 along the LENGTH,
# y in 0..1 across the width. Blue defends x=0, red defends x=1.)
# ------------------------------------------------------------------
# CALIBRATE THESE. Roll the ball into each goal by hand with
# `python -m tools.watch_ball` and read off the numbers it prints.
GOAL_LINE_BLUE = _env_float("FOOSGOOS_GOAL_LINE_BLUE", 0.03)   # crossed -> RED scores
GOAL_LINE_RED = _env_float("FOOSGOOS_GOAL_LINE_RED", 0.97)     # crossed -> BLUE scores

# A hard shot travels ~15cm between frames at 90fps, so the ball is often
# never *seen* sitting inside the goal - it is seen just outside, then not
# at all. Hence two detectors:
#
#   1. crossing      - the segment between two consecutive ball positions
#                      intersects a goal line. Precise, needs two sightings.
#   2. disappearance - the ball was last seen inside the mouth zone and
#                      then vanished for a while. Catches what (1) misses.
DISAPPEARANCE_ENABLED = _env_bool("FOOSGOOS_DISAPPEARANCE", True)
# How deep into each end counts as "in the mouth of the goal".
GOAL_MOUTH_DEPTH = _env_float("FOOSGOOS_GOAL_MOUTH_DEPTH", 0.10)
# Ball must be unseen for this long after entering the mouth to call it.
DISAPPEARANCE_TIMEOUT_S = _env_float("FOOSGOOS_DISAPPEARANCE_TIMEOUT", 0.7)

# The goal mouth does not span the whole end wall. Restricting the
# crossing test to the middle of the width stops the ball rolling along
# the end of the table from registering as a goal. Measure yours.
GOAL_MOUTH_Y_MIN = _env_float("FOOSGOOS_GOAL_Y_MIN", 0.30)
GOAL_MOUTH_Y_MAX = _env_float("FOOSGOOS_GOAL_Y_MAX", 0.70)

# Ignore detections that imply the ball teleported - almost always a
# misdetection on a player's shirt or a reflection.
#
# Units are table-lengths per second, so this is framerate-independent:
# it means the same thing whether inference keeps up at 90fps or drops to
# 15. A 30mph slam is 13.4 m/s across a ~1.2m playing surface = about 11
# lengths/sec, and hard pro shots reach ~13. 25 leaves roughly 2x headroom
# over anything physically real while still catching gross errors (a
# full-table jump in a single 90fps frame implies 90).
#
# Note this gate self-heals: it compares against the last ACCEPTED
# position, and the implied speed falls as time passes, so even a bad
# reference point can only suppress a few frames before real detections
# look plausible again. It cannot blind the tracker permanently.
MAX_BALL_SPEED = _env_float("FOOSGOOS_MAX_BALL_SPEED", 25.0)

# One physical goal must not fire twice while the ball sits in the net.
GOAL_COOLDOWN_S = _env_float("FOOSGOOS_GOAL_COOLDOWN", 3.0)

# How far back to look to guess which rod the ball came off. The old code
# looked back only until the ball was 0.05 away from the line - still
# inside the goal mouth - so it always answered "goalie".
ROD_LOOKBACK_S = _env_float("FOOSGOOS_ROD_LOOKBACK", 0.6)

# Send the rod guess to the backend? OFF by default and it should stay off
# until measured: the rods interleave down the table (see inference/zones.py),
# so ball position alone genuinely cannot identify whose rod it was. In
# assisted mode a human taps the bar in one tap - a wrong prefill is worse
# than none.
SEND_BAR_HINT = _env_bool("FOOSGOOS_SEND_BAR_HINT", False)

# ------------------------------------------------------------------
# Recording
# ------------------------------------------------------------------
# Every match is recorded. Footage + the backend's goal log is the entire
# dataset for training and evaluation - you cannot go back and capture
# frames you never saved.
RECORDING_ENABLED = _env_bool("FOOSGOOS_RECORDING", True)
# Sampling rate for the saved file. Full 90fps is ~3x the disk and encode
# cost; 30 is plenty for pulling training stills and reviewing goals.
RECORD_FPS = _env_int("FOOSGOOS_RECORD_FPS", 30)
RECORD_FOURCC = os.getenv("FOOSGOOS_RECORD_FOURCC", "mp4v")
# Encoding runs on its own thread behind a bounded queue so a slow disk
# stalls the recording, never the goal detection.
RECORD_QUEUE_SIZE = _env_int("FOOSGOOS_RECORD_QUEUE", 120)

# ------------------------------------------------------------------
# Rod layout, for the (optional, unreliable) rod hint.
# See inference/zones.py for why this is hard.
# ------------------------------------------------------------------
# Fraction of table length from the blue goal, in real rod order. A
# regulation table alternates sides: blue's attacking 3-bar sits deep in
# red's half and vice versa.
ROD_POSITIONS = [
    ("blue", "goalie", 0.05),
    ("blue", "2bar",   0.15),
    ("red",  "3bar",   0.28),
    ("blue", "5bar",   0.41),
    ("red",  "5bar",   0.59),
    ("blue", "3bar",   0.72),
    ("red",  "2bar",   0.85),
    ("red",  "goalie", 0.95),
]
