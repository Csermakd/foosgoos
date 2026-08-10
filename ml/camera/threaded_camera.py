"""
Producer/consumer camera capture that avoids "phantom frames" - i.e.
the consumer accidentally processing the same frame twice because it
read faster than the camera actually produced a new one.

WHY YOUR OLD fast_camera.py PHANTOM-FRAMES:
Its update() thread writes self.frame in a tight loop with no signal
for "this is new." Your ARCHITECTURE.md describes a boolean "fresh
frame" flag as part of the design, but the actual code never
implemented it - read() just hands back whatever self.frame currently
is. If your inference loop is ever faster than the camera's real
capture rate (very possible - Scout inference vs. USB/MJPEG decode
timing drift), you get the exact same frame object handed back two+
times in a row, and the pipeline treats it as two different
observations: duplicate ball positions, doubled velocity estimates,
and potentially double-counted goal events.

THE FIX:
Every captured frame gets a monotonically increasing frame_id. The
consumer calls wait_for_frame(last_seen_id), which blocks until a
strictly newer frame_id exists. That makes it structurally impossible
to process the same frame twice, no matter how the two loops' speeds
drift relative to each other.
"""
import os
import time
import threading
import cv2

os.environ.setdefault("OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS", "0")


class ThreadedCamera:
    def __init__(self, src=1, width=1920, height=1080, fps=90, exposure=-6):
        self.cap = cv2.VideoCapture(src, cv2.CAP_MSMF)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # manual mode (MSMF)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)

        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera at index {src}")

        self._lock = threading.Lock()
        self._new_frame_event = threading.Event()
        self._frame = None
        self._frame_id = 0
        self._stopped = False
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._update, daemon=True)
        self._thread.start()
        return self

    def _update(self):
        while not self._stopped:
            ret, frame = self.cap.read()
            if not ret:
                continue
            with self._lock:
                self._frame = frame
                self._frame_id += 1
            self._new_frame_event.set()

    def wait_for_frame(self, last_seen_id=-1, timeout=1.0):
        """
        Blocks until a frame strictly newer than last_seen_id exists.
        Returns (frame, frame_id), or (None, last_seen_id) on timeout.

        This is what your inference loop should call every iteration -
        it guarantees you never process the same frame twice and never
        silently skip past a stale/duplicate result.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if self._frame is not None and self._frame_id > last_seen_id:
                    return self._frame.copy(), self._frame_id
            self._new_frame_event.wait(timeout=0.05)
            self._new_frame_event.clear()
        return None, last_seen_id

    def read_latest(self):
        """Non-blocking - just grabs whatever is newest right now."""
        with self._lock:
            if self._frame is None:
                return None, -1
            return self._frame.copy(), self._frame_id

    def stop(self):
        self._stopped = True
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self.cap.release()


if __name__ == "__main__":
    # Quick smoke test / FPS check, same spirit as your old fast_camera.py
    print("Starting fixed threaded camera stream...")
    stream = ThreadedCamera(src=1).start()
    time.sleep(1.0)

    frames = 0
    prev_time = time.time()
    last_id = -1

    while True:
        frame, last_id = stream.wait_for_frame(last_id)
        if frame is None:
            continue

        frames += 1
        now = time.time()
        elapsed = now - prev_time
        if elapsed > 1.0:
            print(f"True (no-duplicate) FPS: {frames / elapsed:.1f}")
            prev_time = now
            frames = 0

        cv2.imshow("Fixed Camera Stream", cv2.resize(frame, (960, 540)))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    stream.stop()
    cv2.destroyAllWindows()
