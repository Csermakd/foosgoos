"""
HTTP client for the FastAPI backend.

The vision service never imports from backend/ - the two halves only ever
talk over HTTP. That means the whole vision stack can be rewritten, or
run on a different machine, without the API knowing.

The one thing this client takes seriously is not losing goals. Every POST
carries a stable event_uuid, so a failed request can be retried with the
same id and the backend will recognise it rather than scoring twice. A
goal that cannot be delivered goes into an on-disk queue and is retried
until it lands - a flaky wifi router must not cost someone a point.
"""
import json
import time
from pathlib import Path
from typing import Optional

import requests

import config


class BackendClient:
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None,
                 queue_path: Optional[Path] = None):
        self.base_url = (base_url or config.API_URL).rstrip("/")
        self.timeout = timeout or config.API_TIMEOUT_S
        self.queue_path = Path(queue_path or (config.PROJECT_ROOT / "pending_goals.json"))
        self._pending = self._load_queue()
        self.stats = {"posted": 0, "queued": 0, "recovered": 0, "failures": 0}

    # -- plumbing --------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def health(self) -> bool:
        """Called once at startup so a wrong FOOSGOOS_API_URL fails loudly
        instead of silently swallowing every goal of the evening."""
        try:
            r = requests.get(self._url("/health"), timeout=self.timeout)
            return r.status_code == 200
        except requests.RequestException:
            return False

    # -- session ---------------------------------------------------

    def get_active_match(self) -> Optional[dict]:
        """The match currently being played, or None.

        Polled rather than pushed: the camera machine can reboot or be
        started halfway through a game and it will just pick up.
        """
        try:
            r = requests.get(self._url("/matches/active"), timeout=self.timeout)
            r.raise_for_status()
            return r.json() or None
        except requests.RequestException as exc:
            print(f"[backend] could not reach {self.base_url}: {exc}")
            return None

    def set_video_path(self, match_id: int, video_path: str) -> bool:
        try:
            r = requests.post(self._url(f"/matches/{match_id}/video"),
                              json={"video_path": str(video_path)},
                              timeout=self.timeout)
            return r.status_code == 200
        except requests.RequestException:
            return False

    # -- goals -----------------------------------------------------

    def post_goal(self, match_id: int, goal, send_bar_hint: Optional[bool] = None) -> bool:
        """Report a detected goal. Queues it for retry if the POST fails."""
        payload = self.goal_payload(goal, send_bar_hint)
        return self._deliver(match_id, payload, queue_on_failure=True)

    @staticmethod
    def goal_payload(goal, send_bar_hint: Optional[bool] = None) -> dict:
        """Translate a DetectedGoal into the backend's GoalEventCreate.

        Note what is deliberately NOT sent: player_id (the camera has no
        idea who is holding which handle) and, by default, the bar. Both
        are left for a human to fill in with one tap.
        """
        if send_bar_hint is None:
            send_bar_hint = config.SEND_BAR_HINT
        return {
            "event_uuid": goal.event_uuid,
            "team": goal.team,
            "source": "camera",
            "confidence": round(float(goal.confidence), 3),
            "video_ts_ms": int(goal.video_ts_ms) if goal.video_ts_ms is not None else None,
            "detector_note": goal.detector,
            "bar": goal.bar_hint if send_bar_hint else "unknown",
        }

    def _deliver(self, match_id: int, payload: dict, queue_on_failure: bool) -> bool:
        try:
            r = requests.post(self._url(f"/matches/{match_id}/events"),
                              json=payload, timeout=self.timeout)
            if r.status_code == 200:
                self.stats["posted"] += 1
                body = r.json()
                if body.get("duplicate"):
                    print(f"[backend] goal {payload['event_uuid'][:8]} was already "
                          f"recorded - retry correctly de-duplicated")
                return True
            if r.status_code == 409:
                # The match finished before this landed. Dropping it is
                # right: retrying forever would never succeed.
                print(f"[backend] match {match_id} is closed; dropping goal")
                return False
            print(f"[backend] goal rejected ({r.status_code}): {r.text[:200]}")
            self.stats["failures"] += 1
            return False
        except requests.RequestException as exc:
            print(f"[backend] goal POST failed: {exc}")
            self.stats["failures"] += 1
            if queue_on_failure:
                self._enqueue(match_id, payload)
            return False

    # -- retry queue -----------------------------------------------

    def _enqueue(self, match_id: int, payload: dict):
        self._pending.append({"match_id": match_id, "payload": payload,
                              "queued_at": time.time()})
        self.stats["queued"] += 1
        self._save_queue()
        print(f"[backend] queued goal {payload['event_uuid'][:8]} for retry "
              f"({len(self._pending)} pending)")

    def flush_pending(self) -> int:
        """Retry queued goals. Safe to call as often as you like - the
        event_uuid makes every retry idempotent."""
        if not self._pending:
            return 0
        still_pending = []
        delivered = 0
        for item in self._pending:
            if self._deliver(item["match_id"], item["payload"], queue_on_failure=False):
                delivered += 1
            else:
                still_pending.append(item)
        if delivered:
            self.stats["recovered"] += delivered
            print(f"[backend] recovered {delivered} queued goal(s)")
        self._pending = still_pending
        self._save_queue()
        return delivered

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def _load_queue(self) -> list:
        if not self.queue_path.exists():
            return []
        try:
            return json.loads(self.queue_path.read_text())
        except (json.JSONDecodeError, OSError):
            return []

    def _save_queue(self):
        try:
            if self._pending:
                self.queue_path.write_text(json.dumps(self._pending, indent=2))
            elif self.queue_path.exists():
                self.queue_path.unlink()
        except OSError as exc:
            print(f"[backend] could not persist retry queue: {exc}")
