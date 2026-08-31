"""
Records every match to disk, on a background thread.

Why this exists at all: you cannot go back and capture frames you never
saved. Footage plus the backend's goal log IS the dataset - for training
the next model, for tuning the goal lines, and for settling arguments.
Storage is cheap; a game you did not record is gone.

Encoding runs behind a bounded queue on its own thread, so a slow disk
degrades the recording (dropped frames, counted and reported) rather than
stalling goal detection.

Alongside the .mp4 we write a sidecar .frames.json mapping each written
frame to the wall-clock milliseconds since recording started. That is
what makes "jump to the frame where the 3rd goal happened" exact, even
when the pipeline cannot keep up with the nominal record fps and the
video ends up time-compressed.
"""
import json
import queue
import threading
import time
from pathlib import Path

import cv2

import config


class SessionRecorder:
    def __init__(self, match_id, out_dir=None, fps=None, fourcc=None,
                 queue_size=None):
        self.match_id = match_id
        self.out_dir = Path(out_dir or config.RECORDINGS_DIR)
        self.fps = fps or config.RECORD_FPS
        self.fourcc = fourcc or config.RECORD_FOURCC
        self.queue_size = queue_size or config.RECORD_QUEUE_SIZE

        self.video_path = None
        self.index_path = None
        self.started_at = None

        self._writer = None
        self._queue = None
        self._thread = None
        self._stopping = False
        self._last_sample_time = 0.0
        self._frame_times = []
        self.frames_written = 0
        self.frames_dropped = 0

    # -- lifecycle -------------------------------------------------

    def start(self, frame):
        height, width = frame.shape[:2]
        self.out_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        base = self.out_dir / f"match_{self.match_id:05d}_{stamp}"
        self.video_path = base.with_suffix(".mp4")
        self.index_path = Path(str(base) + ".frames.json")

        writer = cv2.VideoWriter(
            str(self.video_path),
            cv2.VideoWriter_fourcc(*self.fourcc),
            self.fps, (width, height),
        )
        if not writer.isOpened():
            raise RuntimeError(
                f"Could not open a VideoWriter for {self.video_path} using "
                f"fourcc '{self.fourcc}'. Try FOOSGOOS_RECORD_FOURCC=avc1 or "
                f"XVID (with a .avi extension)."
            )

        self._writer = writer
        self._queue = queue.Queue(maxsize=self.queue_size)
        self._stopping = False
        self.started_at = time.time()
        self._last_sample_time = 0.0
        self._thread = threading.Thread(target=self._drain, daemon=True)
        self._thread.start()
        print(f"[recorder] recording match {self.match_id} -> "
              f"{self.video_path.name} ({width}x{height} @ {self.fps}fps)")
        return self.video_path

    def submit(self, frame, now=None):
        """Offer a frame. Sampled down to `fps`; extra frames are ignored
        rather than queued, so the file stays a sane size."""
        if self._writer is None:
            return False
        now = time.time() if now is None else now
        if now - self._last_sample_time < 1.0 / self.fps:
            return False
        self._last_sample_time = now

        try:
            self._queue.put_nowait((frame.copy(), now - self.started_at))
            return True
        except queue.Full:
            # Disk cannot keep up. Losing recording frames is acceptable;
            # blocking the inference loop is not.
            self.frames_dropped += 1
            if self.frames_dropped % 100 == 1:
                print(f"[recorder] encoder is behind - dropped "
                      f"{self.frames_dropped} frames so far")
            return False

    def _drain(self):
        while True:
            try:
                item = self._queue.get(timeout=0.2)
            except queue.Empty:
                if self._stopping:
                    return
                continue
            if item is None:
                return
            frame, elapsed_s = item
            self._writer.write(frame)
            self._frame_times.append(round(elapsed_s * 1000, 1))
            self.frames_written += 1

    def stop(self):
        """Flush, close, and write the frame index. Returns the video path."""
        if self._writer is None:
            return None
        self._stopping = True
        if self._thread is not None:
            self._thread.join(timeout=10.0)
        self._writer.release()
        self._writer = None

        duration = max(1e-6, time.time() - self.started_at)
        index = {
            "match_id": self.match_id,
            "video": self.video_path.name,
            "started_at": self.started_at,
            "nominal_fps": self.fps,
            "effective_fps": round(self.frames_written / duration, 2),
            "frames_written": self.frames_written,
            "frames_dropped": self.frames_dropped,
            # elapsed wall-clock ms for each written frame, in order. Use
            # this - not frame_index / fps - to line a goal's video_ts_ms
            # up with a frame.
            "frame_times_ms": self._frame_times,
        }
        self.index_path.write_text(json.dumps(index))
        print(f"[recorder] wrote {self.frames_written} frames "
              f"({index['effective_fps']}fps effective) to {self.video_path.name}"
              + (f", dropped {self.frames_dropped}" if self.frames_dropped else ""))
        return self.video_path

    # -- helpers ---------------------------------------------------

    def elapsed_ms(self, now=None) -> int:
        """Milliseconds since recording started - what we send to the
        backend as a goal's video_ts_ms."""
        if self.started_at is None:
            return 0
        now = time.time() if now is None else now
        return int((now - self.started_at) * 1000)


def load_frame_index(index_path):
    """Read a .frames.json written by SessionRecorder."""
    return json.loads(Path(index_path).read_text())


def frame_number_at(index: dict, elapsed_ms: float) -> int:
    """Which frame of the recorded file corresponds to this wall-clock
    offset? Used to pull training stills from around a known goal."""
    times = index.get("frame_times_ms") or []
    if not times:
        fps = index.get("nominal_fps") or config.RECORD_FPS
        return int(elapsed_ms / 1000 * fps)
    best_i, best_gap = 0, abs(times[0] - elapsed_ms)
    for i, t in enumerate(times):
        gap = abs(t - elapsed_ms)
        if gap < best_gap:
            best_i, best_gap = i, gap
        elif t > elapsed_ms:
            break
    return best_i
