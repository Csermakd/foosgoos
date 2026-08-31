"""
The vision service - the thing you actually run on the camera machine.

    python -m vision_service

It sits idle until someone picks four players in the app, then for the
duration of that match it records video and reports goals. It owns the
camera and the models; it talks to the rest of the system only over HTTP.

Design notes worth knowing:

  * It POLLS the backend for the active match rather than being pushed to.
    The camera PC can reboot, lose wifi, or be started halfway through a
    game and it just picks up. No service discovery, nothing to get stale.
  * Polling happens on a background thread so an HTTP round trip never
    stalls the frame loop.
  * Models load ONCE at startup, not per match - loading YOLO weights
    takes seconds and you do not want that between games.
  * Goals it cannot deliver are queued on disk and retried. Every goal
    carries a stable uuid so retries cannot double-score.

This is ASSISTED mode: the camera proposes, a human confirms. Detected
goals land in the app as `pending_review` with no player attributed, and
someone taps to confirm or correct. Do not read a clean console here as
permission to stop watching the app.
"""
import argparse
import signal
import sys
import threading
import time

import config
from backend_client import BackendClient
from camera.threaded_camera import ThreadedCamera
from inference.pipeline import FoosballPipeline, draw_overlay
from recording.session_recorder import SessionRecorder


class SessionWatcher(threading.Thread):
    """Background poller: 'is a game being played right now?'"""

    def __init__(self, client: BackendClient, interval=None):
        super().__init__(daemon=True)
        self.client = client
        self.interval = interval or config.SESSION_POLL_INTERVAL_S
        self._match = None
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def run(self):
        while not self._stop.is_set():
            match = self.client.get_active_match()
            with self._lock:
                self._match = match
            # Piggyback the retry flush on the poll - if the backend is
            # reachable enough to answer this, it can take queued goals.
            if match is not None or self.client.pending_count:
                self.client.flush_pending()
            self._stop.wait(self.interval)

    @property
    def active_match(self):
        with self._lock:
            return self._match

    def stop(self):
        self._stop.set()


class VisionService:
    def __init__(self, args):
        self.args = args
        self.client = BackendClient()
        self.camera = None
        self.pipeline = None
        self.watcher = None
        self.recorder = None
        self.current_match_id = None
        self._running = True
        self._last_id = -1
        self._fps_window_start = time.time()
        self._fps_window_frames = 0

    # -- setup -----------------------------------------------------

    def start(self):
        if not self.args.dry_run and not self.client.health():
            print(f"[vision] cannot reach the backend at {config.API_URL}.\n"
                  f"         Start it with `uvicorn app:app --reload` in "
                  f"backend/, or set FOOSGOOS_API_URL.\n"
                  f"         (Run with --dry-run to work without a backend.)")
            return False

        self.pipeline = FoosballPipeline(on_goal=None)
        self.camera = ThreadedCamera().start()
        time.sleep(1.0)   # let the sensor settle

        if not self.args.dry_run:
            self.watcher = SessionWatcher(self.client)
            self.watcher.start()

        print(f"[vision] ready. Watching for a match at {config.API_URL}.")
        if self.args.dry_run:
            print("[vision] DRY RUN - detections print to console, nothing is "
                  "posted and nothing is recorded.")
        return True

    # -- main loop -------------------------------------------------

    def run(self):
        if not self.start():
            return 1
        try:
            while self._running:
                match = self._current_match()
                match_id = match["id"] if match else None

                if match_id != self.current_match_id:
                    self._switch_session(match, match_id)

                if match_id is None:
                    self._idle_tick()
                    continue

                self._process_one_frame(match_id)
        except KeyboardInterrupt:
            print("\n[vision] interrupted")
        finally:
            self.shutdown()
        return 0

    def _current_match(self):
        if self.args.dry_run:
            # Pretend a match is always running so you can point this at
            # the table and watch it detect goals with no app involved.
            return {"id": 0}
        return self.watcher.active_match

    def _switch_session(self, match, match_id):
        if self.current_match_id is not None:
            self._end_session()
        self.current_match_id = match_id
        if match_id is None:
            print("[vision] no match in progress - idling")
            return

        print(f"\n[vision] === match {match_id} started ===")
        self.pipeline.reset()
        self._last_id = -1

        if config.RECORDING_ENABLED and not self.args.no_record and not self.args.dry_run:
            frame, self._last_id = self.camera.wait_for_frame(-1, timeout=3.0)
            if frame is None:
                print("[vision] no frames from the camera - not recording")
            else:
                self.recorder = SessionRecorder(match_id)
                path = self.recorder.start(frame)
                self.client.set_video_path(match_id, path)

    def _end_session(self):
        if self.recorder is not None:
            self.recorder.stop()
            self.recorder = None
        print(f"[vision] === match {self.current_match_id} ended === "
              f"{self.pipeline.summary()}\n")

    def _idle_tick(self):
        # Keep pulling frames so the camera buffer does not go stale, but
        # do no inference - there is nothing to report.
        frame, self._last_id = self.camera.wait_for_frame(self._last_id, timeout=0.5)
        if frame is not None and self.args.preview:
            self._show(frame, None)

    def _process_one_frame(self, match_id):
        frame, self._last_id = self.camera.wait_for_frame(self._last_id, timeout=1.0)
        if frame is None:
            return

        now = time.time()
        video_ts = self.recorder.elapsed_ms(now) if self.recorder else None
        result = self.pipeline.process(frame, now=now, video_ts_ms=video_ts)

        if self.recorder is not None:
            self.recorder.submit(frame, now)

        if result.goal is not None:
            self._handle_goal(match_id, result.goal)

        if self.args.preview:
            self._show(frame, result)

        self._tick_fps()

    def _handle_goal(self, match_id, goal):
        print(f"[GOAL] {goal.describe()}")
        if self.args.dry_run:
            return
        self.client.post_goal(match_id, goal)

    def _show(self, frame, result):
        import cv2
        if result is None:
            preview = cv2.resize(frame, (960, int(960 * frame.shape[0] / frame.shape[1])))
            cv2.putText(preview, "idle - no match in progress", (10, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
        else:
            preview = draw_overlay(frame, result, self.pipeline.homography)
        cv2.imshow("Foosgoos vision service  (q to quit)", preview)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            self._running = False

    def _tick_fps(self):
        self._fps_window_frames += 1
        elapsed = time.time() - self._fps_window_start
        if elapsed < 5.0:
            return
        fps = self._fps_window_frames / elapsed
        capture = self.camera.stats()["capture_fps"]
        rate = self.pipeline.game_state.detection_rate
        note = ""
        if fps < capture * 0.5:
            # Worth flagging loudly: if inference runs at a fraction of
            # capture, most frames are never looked at, and a fast shot
            # can pass the goal entirely between two processed frames.
            note = "  <- inference is far behind the camera; see the README"
        print(f"[vision] {fps:5.1f} inference fps | {capture:5.1f} capture fps | "
              f"ball seen in {rate:.0%} of frames{note}")
        self._fps_window_start = time.time()
        self._fps_window_frames = 0

    # -- teardown --------------------------------------------------

    def shutdown(self):
        if self.current_match_id is not None:
            self._end_session()
        if self.watcher is not None:
            self.watcher.stop()
        if self.camera is not None:
            self.camera.stop()
        if self.args.preview:
            import cv2
            cv2.destroyAllWindows()
        if not self.args.dry_run and self.client.pending_count:
            print(f"[vision] {self.client.pending_count} goal(s) still queued - "
                  f"they will be retried next run.")
        print("[vision] stopped.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true",
                        help="show the annotated video window (costs a few fps)")
    parser.add_argument("--no-record", action="store_true",
                        help="do not save video for this session")
    parser.add_argument("--dry-run", action="store_true",
                        help="detect and print goals without a backend")
    args = parser.parse_args()

    service = VisionService(args)
    signal.signal(signal.SIGTERM, lambda *_: setattr(service, "_running", False))
    sys.exit(service.run())


if __name__ == "__main__":
    main()
