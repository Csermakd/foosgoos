"""
Pull training stills out of recorded matches.

    # every 20th frame from one match, plus a burst around each real goal
    python -m data_collection.extract_frames --match 42

    # straight from a file, no backend involved
    python -m data_collection.extract_frames --video game.mp4 --every 20

Why this exists: the first draft saved a .jpg every 0.5s during play and
threw the other 179 frames away. That is backwards. Record everything,
then choose what to label later, offline, as many times as you like.

It matters WHICH frames you label. A model trained only on a crisp,
stationary ball loses it exactly when it matters - during the fast shot
that becomes a goal. So this deliberately over-samples the seconds around
each recorded goal, where the ball is fastest and most motion-blurred.
"""
import argparse
import shutil
import sys
from pathlib import Path

import cv2
import requests

import config
from recording.session_recorder import load_frame_index, frame_number_at


def goal_times_from_backend(match_id):
    url = f"{config.API_URL.rstrip('/')}/matches/{match_id}"
    response = requests.get(url, timeout=config.API_TIMEOUT_S)
    response.raise_for_status()
    match = response.json()
    times = [e["video_ts_ms"] for e in match.get("goal_events", [])
             if e["video_ts_ms"] is not None and e["status"] != "rejected"]
    return match, sorted(times)


def frames_to_extract(total_frames, every, goal_frames, burst):
    """Regular sampling for variety, plus a dense burst around each goal."""
    wanted = set(range(0, total_frames, max(1, every)))
    for frame_no in goal_frames:
        for offset in range(-burst, burst + 1):
            candidate = frame_no + offset
            if 0 <= candidate < total_frames:
                wanted.add(candidate)
    return sorted(wanted)


def extract(video_path, out_dir, wanted, prefix):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise SystemExit(f"Could not open {video_path}")
    out_dir.mkdir(parents=True, exist_ok=True)

    wanted_set = set(wanted)
    written = 0
    index = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if index in wanted_set:
            path = out_dir / f"{prefix}_{index:06d}.jpg"
            cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            written += 1
        index += 1
    cap.release()
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--match", type=int, help="match id (pulls video + goal times)")
    parser.add_argument("--video", help="path to a recording (overrides --match)")
    parser.add_argument("--out", default=str(config.DATASET_DIR / "raw" / "gameplay"))
    parser.add_argument("--every", type=int, default=20,
                        help="keep every Nth frame (default 20; at 30fps that "
                             "is ~1.5 per second)")
    parser.add_argument("--burst", type=int, default=15,
                        help="extra frames either side of each goal (default 15)")
    parser.add_argument("--goal-ms", type=float, nargs="*", default=None,
                        help="goal timestamps in ms, if not using --match")
    args = parser.parse_args()

    if not args.match and not args.video:
        parser.error("give --match N or --video PATH")

    goal_ms = args.goal_ms or []
    video = args.video
    if args.match and not video:
        match, goal_ms = goal_times_from_backend(args.match)
        video = match.get("video_path")
        if not video:
            raise SystemExit(f"Match {args.match} has no recorded video.")
    video_path = Path(video)
    if not video_path.exists():
        raise SystemExit(f"Video not found: {video_path}")

    # Convert goal wall-clock offsets into frame numbers using the sidecar
    # index, which is exact even when the recorder could not keep up with
    # its nominal fps.
    index_path = Path(str(video_path.with_suffix("")) + ".frames.json")
    goal_frames = []
    if goal_ms:
        if index_path.exists():
            index = load_frame_index(index_path)
            goal_frames = [frame_number_at(index, ms) for ms in goal_ms]
        else:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS) or config.RECORD_FPS
            cap.release()
            print(f"[extract] no frame index next to the video; assuming a "
                  f"constant {fps:.1f}fps, so goal alignment may drift.")
            goal_frames = [int(ms / 1000 * fps) for ms in goal_ms]

    cap = cv2.VideoCapture(str(video_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()

    wanted = frames_to_extract(total, args.every, goal_frames, args.burst)
    out_dir = Path(args.out)
    prefix = video_path.stem

    print(f"{video_path.name}: {total} frames, {len(goal_ms)} goals")
    print(f"extracting {len(wanted)} frames "
          f"({len(wanted) - len(range(0, total, max(1, args.every)))} of them "
          f"from goal bursts) -> {out_dir}")
    written = extract(video_path, out_dir, wanted, prefix)

    free_gb = shutil.disk_usage(out_dir).free / 1e9
    print(f"\nwrote {written} frames. {free_gb:.1f} GB free.")
    print("\nNext: upload these to the Roboflow 'Foosgoos-Scout' project and\n"
          "label the BALL only (see README_ML_PIPELINE.md step 3). Aim for\n"
          "300-500 varied frames in total across several matches - variety\n"
          "beats volume, and near-duplicates just cost labelling time.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
