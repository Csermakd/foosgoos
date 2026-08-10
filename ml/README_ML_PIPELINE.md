# Foosgoos ML Pipeline

This is the brain of the ref. Everything in here is about turning raw camera
frames into a `GOAL` event. It doesn't know or care about the backend/frontend —
it just watches the table and yells when the ball goes in.

## Quick mental model before we touch anything

```
record frames → mark them up in Roboflow → train on Modal → drop new best.pt in
```

The model that's actually running during a match is frozen. It doesn't update
itself mid-game - it's just doing inference (predicting) at ~90fps using
whatever weights we last gave it. All the "learning" happens offline, in that
loop above, which we run once to get started and then again every so often as
we collect more footage.

First batch, we have to label everything by hand - YOLO is supervised, no way
around it. But once we've got a decent first model, we can use it to
pre-label new frames automatically and just fix its mistakes in Roboflow,
which is way faster than starting from a blank frame. That's the closest
thing to "continuous learning" we get, and honestly it's enough.

## Where this folder lives

Don't nest this inside `backend/`. The backend already has (or will have) a
`models/` package for the SQLAlchemy tables - this project also has a
`models/` folder, but for `.pt` weight files. Same name, totally different
thing, guaranteed to confuse someone at 1am. Keep them as siblings:

```
foosgoos/
├── backend/         (app.py, database.py, routers/, models/ = DB tables)
├── frontend/         (Home.tsx, GoalModal.tsx, etc.)
└── ml/                <- this folder goes here
    ├── config.py
    ├── camera/
    ├── data_collection/
    ├── training/
    ├── inference/
    ├── models/        <- .pt weight files land here
    └── datasets/       <- raw collected frames land here
```

`ml/` never imports from `backend/` or vice versa. They only talk over HTTP -
`on_goal_detected()` POSTs to the FastAPI matches route. Keeps things clean:
we can rip out and swap the entire vision stack without touching the API, and
vice versa.

## What's in this folder

```
ml/
  config.py                          all the tunable constants in one place
  camera/threaded_camera.py          fixed camera capture (no more phantom frames)
  data_collection/record_dataset.py  grabs frames for us to go mark up
  training/train_architect_modal.py  trains the keypoint model on Modal
  training/train_scout_modal.py      trains the object detector on Modal
  inference/homography.py            keypoints -> flat table coordinates
  inference/zones.py                 goal-line and bar-zone math
  inference/game_state.py            ball tracking -> debounced goal events
  inference/live_pipeline.py         the script we actually run during a game
  requirements.txt
```

## Setup (once, per machine)

```bash
cd ml
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 1 - Make sure the camera fix actually works

Old `fast_camera.py` had no way for the reader to know if a frame was
actually new - under load it'd hand back the same frame twice, which is
where the phantom frames came from. `camera/threaded_camera.py` fixes this
with a frame-id + blocking `wait_for_frame()`, so we structurally can't
process the same frame twice no matter how fast/slow the loops drift
relative to each other.

Test it standalone before building on top of it:

```bash
python -m camera.threaded_camera
```

We should see a steady, believable FPS number ticking in the console - not
suspiciously identical readings frame after frame. `q` to quit the preview.
If the camera won't open, check `config.CAMERA_INDEX` - it's set to `1`,
try `0` or `2` if that's wrong on your machine.

## Step 2 - Go collect data

This is the part where we actually point the camera at the table and start
generating the raw images we'll mark up later. Two modes:

```bash
# Empty table - walk it around from different angles/heights/distances.
# SPACE to save a frame, q to quit. Aim for 100+ frames.
python -m data_collection.record_dataset --mode table --out datasets/raw/table

# During a real game - auto-saves every 0.5s while we play. Aim for 300+.
python -m data_collection.record_dataset --mode gameplay --out datasets/raw/gameplay --interval 0.5
```

Run the `gameplay` command any time we're about to play - just leave it
running in the background, play normally, hit `q` when we're done. Frames
pile up as `.jpg` files in `datasets/raw/gameplay/`. Lower `--interval` for
faster/more chaotic games, but don't go too low - near-duplicate frames just
bloat the amount we have to mark up later without adding real variety.

## Step 3 - Marking it up (this part's not code, it's Roboflow)

Head to roboflow.com and set up **two separate projects** - matches the
two-model split in ARCHITECTURE.md:

1. **"Foosgoos-Architect"** -> project type **Keypoint Detection**.
   Upload everything from `datasets/raw/table/`. On each image, place 4
   points, always in this exact order: `top-left -> top-right -> bottom-right
   -> bottom-left`. Order has to match `config.ARCHITECT_KEYPOINTS` exactly
   or the homography math downstream will be scrambled.

2. **"Foosgoos-Scout"** -> project type **Object Detection**.
   Upload everything from `datasets/raw/gameplay/`. Draw a tight box around
   the ball and around each visible player piece per frame - use the class
   names already sitting in `config.SCOUT_CLASSES`, don't invent new ones.

For both projects: generate a version with a 70/20/10 train/val/test split,
keep augmentation light (small rotation, small brightness/contrast shifts
only - the camera's bolted down, so heavy geometric augmentation just
teaches the model for situations it'll never actually see). Export as
**YOLOv8** (pick "YOLOv8 Pose" for Architect specifically). Download the zip.

## Step 4 - Train it on Modal (cloud GPU, not our laptops)

```bash
modal token new                    # one-time auth, once per person's machine

modal volume create foosgoos-architect-data
modal volume put foosgoos-architect-data ./architect_dataset /data   # the Roboflow export, unzipped
modal run training/train_architect_modal.py

modal volume create foosgoos-scout-data
modal volume put foosgoos-scout-data ./scout_dataset /data
modal run training/train_scout_modal.py
```

Each one trains on an A10G in the cloud and prints a path to `best.pt` when
it's done. Give it a while - go get lunch, don't babysit the terminal.

## Step 5 - Pull the trained weights down

```bash
modal volume get foosgoos-architect-weights <path from step 4> ./models/table_v1.pt
modal volume get foosgoos-scout-weights <path from step 4> ./models/gameplay_v1.pt
```

These filenames already match `config.ARCHITECT_MODEL_PATH` /
`config.SCOUT_MODEL_PATH` - no code changes needed, just drop them in.

## Step 6 - Run it live

```bash
python -m inference.live_pipeline
```

This is the actual ref running. It loads both models, runs Architect once at
startup (and again every `ARCHITECT_REFRESH_INTERVAL_S` seconds, in case the
table gets bumped) to build the homography, runs Scout every single frame to
track the ball, and prints `[GOAL]` to the console the moment the ball
crosses a goal line - plus a guess at which bar it came off of.

**Don't trust it blind in a real match yet.** The goal-line and zone values
in `config.py` are placeholders based on the "5% of table width" example
from ARCHITECTURE.md - they're not calibrated to our actual table. Add a
quick `print(nx, ny)` in `live_pipeline.py`, watch a few normalized ball
positions stream by as we roll the ball around by hand, and adjust
`GOAL_LINE_BLUE`, `GOAL_LINE_RED`, and the `ZONE_BOUNDARIES_*` dicts in
`config.py` until they line up with reality.

Heads up: this step will crash on `YOLO(...)` load if `models/table_v1.pt`
and `models/gameplay_v1.pt` don't exist yet - steps 2 through 5 have to
happen at least once before this works.

## Step 7 - Wire goals into the actual app

Right now `on_goal_detected()` in `inference/live_pipeline.py` just prints
to console. Next step is replacing that with a real call into the FastAPI
backend - either a new endpoint on the `matches` router, or a websocket
push - so the frontend can pop the `GoalModal` we already built, pre-filled
with the guessed team + bar, and someone just taps to confirm or correct it
instead of filling it out from scratch.

## Step 8 - The retraining loop, ongoing

Once we're actually playing games with the camera rolling regularly:

1. Periodically save the interesting/failure-case frames - misses, weird
   angles, new lighting - into `datasets/raw/gameplay/`.
2. Re-upload the growing dataset to Roboflow, let our current model
   pre-label it, and just fix whatever it got wrong.
3. Re-run the Modal training scripts from Step 4.
4. Swap in the new `best.pt` files from Step 5.
