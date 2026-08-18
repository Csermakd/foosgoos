"""
Central configuration for the Foosgoos ML pipeline.
Edit these values to match your table, camera, and model paths.
"""
from pathlib import Path

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models"
DATASET_DIR = PROJECT_ROOT / "datasets"

ARCHITECT_MODEL_PATH = MODELS_DIR / "table_v1.pt"   # keypoint / pose model
SCOUT_MODEL_PATH = MODELS_DIR / "gameplay_v1.pt"    # object detection model

# ------------------------------------------------------------------
# Camera
# ------------------------------------------------------------------
CAMERA_INDEX = 0
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
TARGET_FPS = 90
EXPOSURE = -2          # ~1/64s. Tune per ARCHITECTURE.md guidance (-5 to -7)

# ------------------------------------------------------------------
# Camera Digital Crop (Zoom)
# Set values to slice the 1920x1080 frame. Use None to disable.
# ------------------------------------------------------------------
CROP_Y1 = 200   # Top boundary (pixels to cut from the top)
CROP_Y2 = 880   # Bottom boundary 
CROP_X1 = 400   # Left boundary (pixels to cut from the left)
CROP_X2 = 1520  # Right boundary

# ------------------------------------------------------------------
# Architect model (keypoint detector)
# ------------------------------------------------------------------
# Order matters - this MUST match the order we label in Roboflow
ARCHITECT_KEYPOINTS = ["top_left", "top_right", "bottom_right", "bottom_left"]

# How often to re-run the Architect model on a live frame, in seconds.
# The table doesn't move often, so this only needs to run occasionally
# (startup, or after a "table bumped" shift is detected).
ARCHITECT_REFRESH_INTERVAL_S = 15.0

# ------------------------------------------------------------------
# Scout model (object detector)
# ------------------------------------------------------------------
# Order MUST match Roboflow class order / data.yaml
SCOUT_CLASSES = [
    "ball",
    "player_red", "player_blue",
    "player_red_two_bar", "player_blue_two_bar",
    "player_red_three_bar", "player_blue_three_bar",
    "player_red_five_bar", "player_blue_five_bar",
    "player_red_goalie_bar", "player_blue_goalie_bar",
]
BALL_CLASS_NAME = "ball"
SCOUT_CONF_THRESHOLD = 0.35

# ------------------------------------------------------------------
# Zones / Game logic (normalized table coords, 0.0 -> 1.0 along length)
# Blue defends the x=0 end, Red defends the x=1 end (swap if
# homography maps the other way).
#
# These are starting points based on ARCHITECTURE.md's "ball_x < 5%"
# example - CALIBRATE these against your real table once the
# homography is live and you can watch normalized coordinates stream.
# ------------------------------------------------------------------
GOAL_LINE_BLUE = 0.03   # ball crossing below this -> goal for RED
GOAL_LINE_RED = 0.97    # ball crossing above this -> goal for BLUE

# Rod positions as fractions of table length, mirrored for each side.
# Used to guess which bar the ball was near right before a goal, so
# the frontend GoalModal can be pre-filled with a best guess.
ZONE_BOUNDARIES_BLUE_SIDE = {
    "goalie": (0.00, 0.08),
    "2bar":   (0.08, 0.22),
    "3bar":   (0.22, 0.45),
    "5bar":   (0.22, 0.45),
}
ZONE_BOUNDARIES_RED_SIDE = {
    "goalie": (0.92, 1.00),
    "2bar":   (0.78, 0.92),
    "5bar":   (0.55, 0.78),
}
# Anything else (midfield) defaults to "3bar" in inference/zones.py
