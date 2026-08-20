"""
Frame sources for the pipeline.

`ThreadedCamera` is the live one: a producer thread pulls frames off the
USB bus as fast as the sensor produces them, and consumers call
`wait_for_frame(last_seen_id)` which blocks until a *strictly newer* frame
exists. That makes it structurally impossible to process the same frame
twice ("phantom frames") no matter how the two loops' speeds drift.

`VideoFileSource` presents the exact same interface over a recorded .mp4,
so the entire pipeline can be replayed offline against footage - which is
how you tune goal lines and measure accuracy without standing at the table.
"""
import os
import sys
import time
import threading

import cv2

import config

os.environ.setdefault("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0")

# OpenCV's capture backends are OS-specific. Hardcoding CAP_MSMF (as the
# first draft did) means the camera simply never opens anywhere but Windows.
_BACKENDS = {
    "msmf": getattr(cv2, "CAP_MSMF", 0),
    "dshow": getattr(cv2, "CAP_DSHOW", 0),
    "avfoundation": getattr(cv2, "CAP_AVFOUNDATION", 0),
    "v4l2": getattr(cv2, "CAP_V4L2", 0),
    "any": getattr(cv2, "CAP_ANY", 0),
}


def resolve_backend(name: str) -> int:
    return _BACKENDS.get((name or "any").lower(), _BACKENDS["any"])


def apply_crop(frame):
    """Crop the raw sensor frame down to the table.

    Applied here, in one place, so recorded video, training stills and
    live inference all see identically framed images. If they ever
    diverge, the model is being asked about a world it never trained on.
    """
    bounds = (config.CROP_Y1, config.CROP_Y2, config.CROP_X1, config.CROP_X2)
    if any(v is None for v in bounds):
        return frame
    y1, y2, x1, x2 = bounds
    h, w = frame.shape[:2]
    y1, y2 = max(0, y1), min(h, y2)
    x1, x2 = max(0, x1), min(w, x2)
    if y2 <= y1 or x2 <= x1:
        return frame
    return frame[y1:y2, x1:x2]


class ThreadedCamera:
    def __init__(self, src=None, width=None, height=None, fps=None,
                 exposure=None, backend=None):
        # Defaulting from config rather than to literals: the old version
        # defaulted src=1 while config said 0, and its self-test hardcoded
        # yet another value.
        self.src = config.CAMERA_INDEX if src is None else src
        width = config.FRAME_WIDTH if width is None else width
        height = config.FRAME_HEIGHT if height is None else height
        fps = config.TARGET_FPS if fps is None else fps
        exposure = config.EXPOSURE if exposure is None else exposure
        backend_name = config.CAMERA_BACKEND if backend is None else backend

        self.cap = cv2.VideoCapture(self.src, resolve_backend(backend_name))
        if not self.cap.isOpened():
            raise RuntimeError(
                f"Could not open camera index {self.src} using the "
                f"'{backend_name}' backend on {sys.platform}. Try a different "
                f"FOOSGOOS_CAMERA_INDEX (0/1/2), or set FOOSGOOS_CAMERA_BACKEND "
                f"to one of: {', '.join(_BACKENDS)}."
            )

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        # Manual exposure. The magic 0.25 is MSMF/V4L2's "manual mode";
        # AVFoundation ignores both of these, which is fine - it just means
        # a Mac is for development, not for match capture.
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)

        self._cond = threading.Condition()
        self._frame = None
        self._frame_id = 0
        self._stopped = False
        self._thread = None
        self._read_failures = 0
        self._started_at = None

    # -- lifecycle -------------------------------------------------

    def start(self):
        self._started_at = time.time()
        self._thread = threading.Thread(target=self._update, daemon=True)
        self._thread.start()
        return self

    def _update(self):
        while not self._stopped:
            ok, frame = self.cap.read()
            if not ok:
                self._read_failures += 1
                # Do not spin at 100% CPU if the camera has gone away.
                time.sleep(0.005)
                continue
            frame = apply_crop(frame)
            with self._cond:
                self._frame = frame
                self._frame_id += 1
                self._cond.notify_all()

    def stop(self):
        self._stopped = True
        with self._cond:
            self._cond.notify_all()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self.cap.release()

    # -- reading ---------------------------------------------------

    def wait_for_frame(self, last_seen_id=-1, timeout=1.0):
        """Block until a frame newer than last_seen_id exists.

        Returns (frame, frame_id), or (None, last_seen_id) on timeout.
        Uses a Condition rather than an Event: an Event can be set and
        cleared between a waiter's check and its wait, losing the wakeup.
        """
        deadline = time.time() + timeout
        with self._cond:
            while True:
                if self._frame is not None and self._frame_id > last_seen_id:
                    return self._frame, self._frame_id
                if self._stopped:
                    return None, last_seen_id
                remaining = deadline - time.time()
                if remaining <= 0:
                    return None, last_seen_id
                self._cond.wait(timeout=remaining)

    def read_latest(self):
        """Non-blocking - whatever is newest right now."""
        with self._cond:
            if self._frame is None:
                return None, -1
            return self._frame, self._frame_id

    # -- diagnostics -----------------------------------------------

    @property
    def is_live(self) -> bool:
        return True

    def stats(self) -> dict:
        elapsed = max(1e-6, time.time() - (self._started_at or time.time()))
        return {
            "frames_captured": self._frame_id,
            "capture_fps": self._frame_id / elapsed,
            "read_failures": self._read_failures,
        }


class VideoFileSource:
    """Replays a recorded match through the same interface as the camera.

    Two modes:
      realtime=False (default) - decode as fast as possible. This is what
        the evaluation harness uses; a 10 minute game replays in seconds.
      realtime=True - pace playback to the file's fps, for eyeballing.

    `timestamp_ms` exposes the position in the video, which is what lets
    detected goals be lined up against the backend's recorded goal log.
    """

    def __init__(self, path, realtime=False, apply_crop_to_frames=False):
        self.path = str(path)
        self.cap = cv2.VideoCapture(self.path)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open video file: {self.path}")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        self.realtime = realtime
        # Recordings are already cropped by the capture thread, so by
        # default we do NOT crop again. Only enable for raw footage.
        self.apply_crop_to_frames = apply_crop_to_frames

        self._frame_id = 0
        self._timestamp_ms = 0.0
        self._exhausted = False
        self._play_started = None

    def start(self):
        self._play_started = time.time()
        return self

    def wait_for_frame(self, last_seen_id=-1, timeout=1.0):
        if self._exhausted:
            return None, last_seen_id

        if self.realtime:
            target = self._frame_id / self.fps
            drift = target - (time.time() - self._play_started)
            if drift > 0:
                time.sleep(min(drift, timeout))

        # Read the position BEFORE grabbing: CAP_PROP_POS_MSEC reports the
        # position after the read, i.e. the *next* frame's timestamp.
        pos_ms = self.cap.get(cv2.CAP_PROP_POS_MSEC)
        ok, frame = self.cap.read()
        if not ok:
            self._exhausted = True
            return None, last_seen_id

        if self.apply_crop_to_frames:
            frame = apply_crop(frame)

        self._frame_id += 1
        # Some containers report 0.0 for every frame; fall back to the
        # frame index divided by the declared fps.
        self._timestamp_ms = pos_ms if pos_ms > 0 else (self._frame_id - 1) / self.fps * 1000.0
        return frame, self._frame_id

    @property
    def timestamp_ms(self) -> float:
        return self._timestamp_ms

    @property
    def exhausted(self) -> bool:
        return self._exhausted

    @property
    def is_live(self) -> bool:
        return False

    def read_latest(self):
        return self.wait_for_frame(self._frame_id)

    def stats(self) -> dict:
        return {
            "frames_read": self._frame_id,
            "total_frames": self.frame_count,
            "position_ms": self._timestamp_ms,
        }

    def stop(self):
        self.cap.release()


if __name__ == "__main__":
    # Smoke test: does the camera open, and is the FPS believable?
    # A number that never changes, or that is suspiciously round, means
    # something upstream is handing back stale frames.
    print(f"Opening camera {config.CAMERA_INDEX} via '{config.CAMERA_BACKEND}' "
          f"on {sys.platform}...")
    stream = ThreadedCamera().start()
    time.sleep(1.0)

    frames = 0
    prev_time = time.time()
    last_id = -1

    try:
        while True:
            frame, last_id = stream.wait_for_frame(last_id)
            if frame is None:
                print("timed out waiting for a frame")
                continue

            frames += 1
            now = time.time()
            elapsed = now - prev_time
            if elapsed > 1.0:
                s = stream.stats()
                print(f"consumed {frames / elapsed:5.1f} fps | "
                      f"captured {s['capture_fps']:5.1f} fps | "
                      f"read failures {s['read_failures']} | "
                      f"frame {frame.shape[1]}x{frame.shape[0]}")
                prev_time = now
                frames = 0

            preview = cv2.resize(frame, (960, 540))
            cv2.imshow("Foosgoos camera test  (q to quit)", preview)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        stream.stop()
        cv2.destroyAllWindows()
