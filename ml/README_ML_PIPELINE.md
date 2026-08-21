# Foosgoos ML Pipeline

Everything that turns camera frames into a `GOAL` event. It knows nothing
about the database or the UI — it watches the table and POSTs to the API.

---

## The mental model, before touching anything

```
record matches → extract frames → label in Roboflow → train on Modal → drop new best.pt in
       ↑                                                                        │
       └──────────────── play more games, look at what it got wrong ────────────┘
```

The model running during a match is **frozen**. It does not learn as it
watches. It runs inference with whatever weights we last handed it. All
learning happens offline, in that loop.

Two things do the actual thinking, and it is worth being clear about
which is which:

| | What it is | What it decides |
|---|---|---|
| **The models** | Two YOLOv8 networks | *Where is the ball, in pixels? Where are the table corners?* |
| **The logic** | Plain Python in `inference/` | *Was that a goal? For whom?* |

Nobody trains a network to understand foosball rules. Goals are `if`
statements with thresholds we measure. That is why the tests in `tests/`
can verify the goal logic with no camera, no GPU and no weights.

---

## What is in here

```
ml/
  config.py                     every tunable constant, one file
  backend_client.py             HTTP to FastAPI, with an on-disk retry queue
  vision_service.py             ** the thing you run during matches **

  camera/threaded_camera.py     live capture + VideoFileSource for replay
  recording/session_recorder.py records every match to disk, off-thread

  inference/
    homography.py               4 corners -> flat table coordinates
    zones.py                    goal lines and rod geometry
    game_state.py               ball trajectory -> debounced goal events
    pipeline.py                 the per-frame core, shared live and offline
    live_pipeline.py            watch-and-print runner, for tuning

  tools/
    calibrate_corners.py        click 4 corners, save calibration.json
    watch_ball.py               read normalized coordinates, tune goal lines

  data_collection/
    record_dataset.py           manual stills (still right for the table set)
    extract_frames.py           pull training stills out of recorded matches

  training/
    dataset_check.py            validate an export BEFORE spending GPU time
    train_scout_modal.py        ball detector
    train_architect_modal.py    table-corner keypoints

  evaluation/evaluate_goals.py  replay footage, score it against real goals
  tests/                        goal logic tests - no hardware needed
```

`ml/` never imports from `backend/`, and `backend/` never imports from
`ml/`. They talk over HTTP. Either side can be rewritten without the
other noticing.

---

## Setup (once per machine)

```bash
cd ml
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests -q       # should pass with no camera attached
```

Per-machine settings come from environment variables so this checked-in
config works everywhere:

```bash
export FOOSGOOS_API_URL=http://192.168.1.42:8000   # where uvicorn runs
export FOOSGOOS_CAMERA_INDEX=0                     # try 0, 1, 2
export FOOSGOOS_CAMERA_BACKEND=msmf                # auto-detected; override if needed
```

---

## Step 1 — Prove the camera works

```bash
python -m camera.threaded_camera
```

You want a **steady, believable** FPS that moves around a little. A
number that never changes means something is handing back stale frames.

The capture backend is now chosen by OS (`msmf` on Windows,
`avfoundation` on macOS, `v4l2` on Linux). The first draft hardcoded
Windows' backend, so the camera silently refused to open anywhere else.

If it will not open, the error message lists what to try. If frames are
**dark**, add light — do not raise `EXPOSURE` towards zero. A slower
shutter smears the ball into a streak precisely during the fast shots
that become goals, and that is much harder to fix later than a lamp.

---

## Step 2 — Calibrate the table (5 minutes, no ML)

```bash
python -m tools.calibrate_corners
```

Freeze a frame, click the four corners in order — **top-left, top-right,
bottom-right, bottom-left** — and it writes `calibration.json`. That is
the homography: the thing that converts camera pixels into flat table
coordinates where x runs 0.0 (blue goal) → 1.0 (red goal).

This unblocks everything downstream without waiting on a trained model.

**Our table moves most days**, so this goes stale. Two options: re-click
it when the table has been nudged, or train the Architect model (Step 6),
which re-finds the corners by itself every ten seconds. Start by
re-clicking; train the Architect when re-clicking gets annoying.

---

## Step 3 — Measure your goal lines

```bash
python -m tools.watch_ball --no-model
```

Click points on the frozen frame; it prints their normalized
coordinates. Click the goal line at each end, then the two edges of each
goal mouth. Put what you measure into `config.py`:

```python
GOAL_LINE_BLUE = 0.03     # ball crossing below this -> RED scored
GOAL_LINE_RED  = 0.97     # ball crossing above this -> BLUE scored
GOAL_MOUTH_Y_MIN = 0.30   # the goal is not the full width of the end
GOAL_MOUTH_Y_MAX = 0.70
```

The values shipped in `config.py` are placeholders from an example in
ARCHITECTURE.md. **They are wrong for our table.** Wrong goal lines mean
missed goals or phantom ones, and no amount of model training fixes that.

---

## Step 4 — Collect data by just playing

Turn recording on and play normally:

```bash
python -m vision_service --dry-run --preview     # before any model exists
```

Better: once the app's start/finish flow is wired up (it is), every match
someone plays through the app records itself. The vision service polls
`/matches/active`, and when a game starts it records video and writes a
sidecar frame index next to it.

**Record whole matches, not sampled stills.** The old `--mode gameplay`
saved one jpg every 0.5s and discarded the other 179 frames — and the
discarded ones are the fast, motion-blurred frames around goals, which
are exactly what the detector most needs to learn. You cannot go back and
capture frames you never saved.

The one thing still worth capturing by hand is the **empty table** for
the Architect:

```bash
python -m data_collection.record_dataset --mode table --out datasets/raw/table
```

~100 frames: every corner, high and low angles, lights on and off.

---

## Step 5 — Extract and label

```bash
python -m data_collection.extract_frames --match 42
```

Pulls every 20th frame plus a dense burst around each recorded goal —
it knows where the goals were because the app stored a `video_ts_ms` on
every one of them. Free ground truth from ordinary play.

Then in Roboflow:

**"Foosgoos-Scout"** → Object Detection. Upload the extracted frames.
Label the **ball only**. One class.

> The original plan had eleven classes — the ball plus ten rod variants.
> Telling a 5-bar man from a 3-bar man from directly overhead is hard for
> a *human*, it triples the labelling time per frame, and the goal logic
> does not use it. One class gets you a working referee. Add more once
> the ball detector is solid and you want rod contact detection.

**"Foosgoos-Architect"** → Keypoint Detection. Upload `datasets/raw/table/`.
Four keypoints per image, always in the order tl → tr → br → bl. Order
must match `config.ARCHITECT_KEYPOINTS` or the homography comes out
rotated, which looks exactly like "the model is bad".

For both: 70/20/10 split, **light** augmentation only (small rotation,
brightness/contrast). The camera is fixed above the table, so heavy
geometric warping teaches situations that will never occur. Export as
YOLOv8 (choose "YOLOv8 Pose" for the Architect). Include some frames with
no ball at all — negatives teach the model what "no ball" looks like.

---

## Step 6 — Check the export, then train

```bash
python -m training.dataset_check ./scout_dataset
```

**Do this before uploading anything.** Almost every "the model came out
useless" story is a dataset problem visible in thirty seconds: an empty
split, images that never got labelled, coordinates out of range. It is
much cheaper to find out here than after an hour of GPU time.

```bash
modal token new                       # once per person

modal volume create foosgoos-scout-data
modal volume put foosgoos-scout-data ./scout_dataset /data
modal run training/train_scout_modal.py

modal volume get foosgoos-scout-weights <path it prints> ./models/gameplay_v1.pt
```

Same shape for the Architect (`--pose` on the check, `table_v1.pt` at the
end). The filenames match `config.py`; nothing else to change.

Defaults are **yolov8n at 640**, not `s` at 960. This model runs on every
frame, up to 90 times a second, on the machine bolted to the table. A
bigger model that drops inference to 12fps is *worse* than a slightly
less accurate one at 60fps, because a ball moving 15cm per frame can
cross the entire goal between two processed frames. Measure your real fps
before reaching for a bigger model.

Keep the previous weights around (`gameplay_v0.pt`). When a retrain comes
out worse on real footage — it happens — you want to roll back in one
command, not one more training run.

---

## Step 7 — Tune against recorded footage, not at the table

```bash
python -m inference.live_pipeline --source recordings/match_00042_*.mp4
```

Replays a real game through the exact same code that runs live and prints
what it calls. Change a goal line, re-run, see whether the same twelve
goals still fire. You do not need the table, the camera, or to be in the
building. A ten-minute game replays in seconds.

Then measure it properly:

```bash
python -m evaluation.evaluate_goals --match 42
```

It compares what the camera called against what the humans actually
recorded in the app, and prints precision, recall and latency:

```
  recall     91.7%   (11/12 real goals found)
  precision  84.6%   (11/13 calls were real)
  latency    median +0.31s
```

Read it like this:
- **low recall, misses at one end** → that goal line is wrong
- **low recall, ball rarely seen** → the Scout needs more training data
- **phantom goals in midfield** → tighten `GOAL_MOUTH_Y_*`
- **phantom goals right after a real one** → raise `GOAL_COOLDOWN_S`

---

## Step 8 — Run it for real

```bash
python -m vision_service            # add --preview to watch it
```

It idles until someone picks four players in the app, then records and
reports goals for that match. It polls the backend rather than being
pushed to, so it can reboot or start mid-game and just pick up.

This is **assisted** mode. Detected goals land in the app already counted
but marked `pending_review` with nobody attributed, and a human taps to
say who scored — or that it was not a goal. Do not read a clean console
as permission to stop watching the app.

---

## How the goal logic actually works

Two detectors, because one is not enough:

**1. Line crossing.** Tests the *segment* between two consecutive ball
positions against the goal line. Checking `if ball_x < 0.03` alone silently
misses fast shots, because at 90fps a hard shot moves ~15cm per frame and
the ball is frequently never photographed inside the goal.

**2. Disappearance.** The ball was last seen inside the mouth of a goal
and then vanished for `DISAPPEARANCE_TIMEOUT_S`. This catches what most
real goals actually look like: the ball drops out of sight into the
return channel and is never seen crossing anything.

Plus a **plausibility gate**: detections implying the ball moved faster
than `MAX_BALL_SPEED` (25 table-lengths/sec — roughly twice a hard slam)
are dropped as the detector latching onto a shirt or a reflection. The
units are lengths/second, not pixels/frame, so it means the same thing
whether inference runs at 90fps or 15.

And a **cooldown**, so one physical goal cannot fire eleven times while
the ball is jostled in the net.

### Why we do not report which rod scored

The rods interleave down the table:

```
blue goal |  bG   b2   r3   b5   r5   b3   r2   rG  | red goal
```

Blue's attacking 3-bar sits deep in red's half, right next to red's
5-bar. "The ball was at x=0.65" does not tell you whose rod touched it —
two rods belonging to opposite teams are within a few centimetres of each
other almost everywhere. `zones.rod_hint()` returns `"unknown"` whenever
two rods are too close to call, and `config.SEND_BAR_HINT` is `False`, so
we do not send a guess at all. In assisted mode a human taps the right
bar in one tap; a wrong prefill is worse than none, because they have to
notice it first, and they will not.

Doing this properly means detecting rod men and watching for the velocity
discontinuity when one strikes the ball. That is a later phase.

---

## When something is wrong

| Symptom | Look at |
|---|---|
| camera will not open | `FOOSGOOS_CAMERA_INDEX` (0/1/2), `FOOSGOOS_CAMERA_BACKEND` |
| dark or streaky frames | more light, then `EXPOSURE` towards `-7` |
| "inference is far behind the camera" | smaller model, `SCOUT_IMG_SIZE=480`, drop `--preview` |
| ball seen in <60% of frames | the Scout needs more varied training data |
| goals missed at one end only | `GOAL_LINE_*` for that end is wrong |
| phantom goals | `GOAL_MOUTH_Y_*`, `MAX_BALL_SPEED`, `GOAL_COOLDOWN_S` |
| coordinates look rotated/mirrored | corners clicked or labelled out of order |
| "No Architect model and no saved calibration" | run `tools.calibrate_corners` |
| goals detected but not in the app | check `pending_goals.json` and `FOOSGOOS_API_URL` |

Every threshold above is in `config.py`, and every one of them can be
overridden with an environment variable for a quick experiment without
editing the file.
