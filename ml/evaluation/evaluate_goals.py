"""
Does the camera actually see the goals? Measure it, offline.

    python -m evaluation.evaluate_goals --match 42
    python -m evaluation.evaluate_goals --video recordings/match_00042_*.mp4 \
                                        --truth truth.json

This is the single most useful thing in the repo once you have footage.
It replays a recorded match through the exact same pipeline that runs
live, then compares what the camera called against what the humans
actually recorded in the app - and prints precision, recall and latency.

Every goal in the app is stored with a video_ts_ms, so the ground truth
comes for free from ordinary play. Nobody has to label anything: just use
the app normally in manual/assisted mode and the evaluation set builds
itself, one game at a time.

Read the numbers like this:
  recall    - of the real goals, how many did we catch? Misses are the
              failure people notice and forgive least.
  precision - of the goals we called, how many were real? Phantom goals
              are worse than misses: they put points on the board that
              somebody has to notice and undo.
  latency   - how long after the real goal did we call it? Anything over
              a second or two feels broken at the table.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

import config
from camera.threaded_camera import VideoFileSource
from inference.pipeline import FoosballPipeline

# A detection within this many seconds of a real goal is the same goal.
MATCH_WINDOW_S = 5.0


def load_truth_from_backend(match_id: int):
    """Ground truth = the goal log the humans confirmed in the app."""
    url = f"{config.API_URL.rstrip('/')}/matches/{match_id}"
    response = requests.get(url, timeout=config.API_TIMEOUT_S)
    response.raise_for_status()
    match = response.json()

    events = []
    for event in match.get("goal_events", []):
        if event["status"] == "rejected":
            continue   # a human said this was not a goal
        if event["video_ts_ms"] is None:
            continue   # cannot be aligned to the footage
        events.append({"ts_s": event["video_ts_ms"] / 1000.0,
                       "team": event["team"],
                       "source": event["source"]})
    return match, sorted(events, key=lambda e: e["ts_s"])


def load_truth_from_file(path):
    data = json.loads(Path(path).read_text())
    events = data["events"] if isinstance(data, dict) else data
    return None, sorted(
        [{"ts_s": e["ts_s"] if "ts_s" in e else e["video_ts_ms"] / 1000.0,
          "team": e["team"], "source": e.get("source", "manual")} for e in events],
        key=lambda e: e["ts_s"],
    )


def replay(video_path):
    """Run the real pipeline over the footage as fast as it will go."""
    pipeline = FoosballPipeline(on_goal=None)
    source = VideoFileSource(video_path).start()
    detections = []
    frames = 0
    t0 = time.time()
    # The video's own timeline drives the clock, so cooldowns and
    # disappearance timeouts mean the same thing here as they do live.
    epoch = time.time()

    while True:
        frame, _ = source.wait_for_frame(frames - 1, timeout=1.0)
        if frame is None:
            break
        frames += 1
        ts_s = source.timestamp_ms / 1000.0
        result = pipeline.process(frame, now=epoch + ts_s,
                                  video_ts_ms=source.timestamp_ms)
        if result.goal is not None:
            detections.append({"ts_s": ts_s, "team": result.goal.team,
                               "detector": result.goal.detector,
                               "confidence": result.goal.confidence})
    source.stop()
    return detections, frames, time.time() - t0, pipeline.summary()


def align(truth, detections, window=MATCH_WINDOW_S):
    """Greedy nearest-in-time matching, earliest truth first."""
    unmatched = list(detections)
    hits, misses = [], []
    for real in truth:
        candidates = [d for d in unmatched if abs(d["ts_s"] - real["ts_s"]) <= window]
        if not candidates:
            misses.append(real)
            continue
        best = min(candidates, key=lambda d: abs(d["ts_s"] - real["ts_s"]))
        unmatched.remove(best)
        hits.append((real, best))
    return hits, misses, unmatched


def report(truth, detections, hits, misses, false_alarms, frames, elapsed, summary):
    print("\n" + "=" * 62)
    print("GOAL DETECTION EVALUATION")
    print("=" * 62)
    print(f"{frames} frames replayed in {elapsed:.1f}s "
          f"({frames / max(elapsed, 1e-6):.0f} fps offline)")
    print(f"real goals: {len(truth)}   |   detections: {len(detections)}")

    recall = len(hits) / len(truth) if truth else 0.0
    precision = len(hits) / len(detections) if detections else 0.0
    print(f"\n  recall     {recall:6.1%}   ({len(hits)}/{len(truth)} real goals found)")
    print(f"  precision  {precision:6.1%}   ({len(hits)}/{len(detections)} calls were real)")

    if hits:
        latencies = [d["ts_s"] - r["ts_s"] for r, d in hits]
        wrong_team = [(r, d) for r, d in hits if r["team"] != d["team"]]
        print(f"  latency    median {sorted(latencies)[len(latencies) // 2]:+.2f}s  "
              f"(min {min(latencies):+.2f}s, max {max(latencies):+.2f}s)")
        print(f"  team correct on {len(hits) - len(wrong_team)}/{len(hits)}")
        by_detector = {}
        for _r, d in hits:
            by_detector[d["detector"]] = by_detector.get(d["detector"], 0) + 1
        print(f"  found by: " + ", ".join(f"{k} {v}" for k, v in sorted(by_detector.items())))

    if misses:
        print(f"\n  MISSED ({len(misses)}) - watch the footage at these times:")
        for m in misses:
            print(f"    {m['ts_s']:8.1f}s  {m['team']}")
    if false_alarms:
        print(f"\n  PHANTOM GOALS ({len(false_alarms)}) - these would have put "
              f"points on the board:")
        for f in false_alarms:
            print(f"    {f['ts_s']:8.1f}s  {f['team']}  via {f['detector']} "
                  f"(conf {f['confidence']:.2f})")

    print(f"\n  pipeline: {summary}")
    print("\nWhat to do with this:")
    print("  low recall, misses clustered at one end -> that goal line is wrong")
    print("  low recall, ball rarely seen            -> Scout needs more data")
    print("  phantom goals in midfield               -> tighten GOAL_MOUTH_Y_*")
    print("  phantom goals right after a real one    -> raise GOAL_COOLDOWN_S")
    print("=" * 62 + "\n")
    return recall, precision


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--match", type=int,
                        help="match id - pulls both the video path and the "
                             "ground-truth goal log from the backend")
    parser.add_argument("--video", help="path to the recording (overrides --match)")
    parser.add_argument("--truth", help="ground-truth JSON instead of the backend")
    parser.add_argument("--window", type=float, default=MATCH_WINDOW_S,
                        help="seconds within which a detection counts as the "
                             "same goal (default 5)")
    args = parser.parse_args()

    if not args.match and not (args.video and args.truth):
        parser.error("give either --match N, or both --video and --truth")

    if args.truth:
        match, truth = load_truth_from_file(args.truth)
    else:
        match, truth = load_truth_from_backend(args.match)

    video = args.video or (match or {}).get("video_path")
    if not video:
        raise SystemExit(
            f"Match {args.match} has no video_path recorded. Either it was "
            f"played before recording was switched on, or the vision service "
            f"was not running."
        )
    if not Path(video).exists():
        raise SystemExit(f"Video not found: {video}")

    print(f"replaying {video}")
    print(f"ground truth: {len(truth)} goals")

    detections, frames, elapsed, summary = replay(video)
    hits, misses, false_alarms = align(truth, detections, args.window)
    recall, precision = report(truth, detections, hits, misses, false_alarms,
                               frames, elapsed, summary)
    # Non-zero exit if it is not good enough to trust, so this can sit in
    # a script later.
    return 0 if (recall >= 0.9 and precision >= 0.9) else 1


if __name__ == "__main__":
    sys.exit(main())
