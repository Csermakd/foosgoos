"""
Turns a stream of per-frame ball positions into discrete goal events.

This is the piece that decides what the app actually records, and it is
worth understanding before trusting it:

  * Goals are detected from the ball's TRAJECTORY, not from a single
    frame's position. At 90fps a hard shot moves ~15cm between frames, so
    the ball frequently is never photographed inside the goal.
  * A second detector fires when the ball vanishes in the mouth of a goal
    and stays vanished, which is what actually happens on most real goals
    (the ball drops out of sight into the return channel).
  * Detections that imply the ball teleported are dropped - those are
    almost always the detector latching onto a red shirt or a reflection.

Nothing here is learned. Every threshold is in config.py and every one of
them needs calibrating against your own table.
"""
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

import config
from inference import zones


@dataclass
class DetectedGoal:
    """One goal, as seen by the camera. Deliberately mirrors the backend's
    GoalEventCreate schema so posting it is a field-for-field copy."""
    team: str                       # "red" | "blue"
    detector: str                   # "crossing" | "disappearance"
    confidence: float
    event_uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    video_ts_ms: Optional[int] = None
    bar_hint: str = "unknown"
    bar_hint_team: Optional[str] = None
    track: List[Tuple[float, float, float]] = field(default_factory=list)

    def describe(self) -> str:
        when = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        bar = "" if self.bar_hint == "unknown" else f", maybe off the {self.bar_hint}"
        return (f"{self.team.upper()} scored{bar} "
                f"[{self.detector}, conf {self.confidence:.2f}, {when}]")


class GameState:
    def __init__(self,
                 on_goal: Optional[Callable[[DetectedGoal], None]] = None,
                 history_len: int = 240,
                 goal_cooldown_s: Optional[float] = None):
        self.on_goal = on_goal
        self.goal_cooldown_s = (config.GOAL_COOLDOWN_S if goal_cooldown_s is None
                                else goal_cooldown_s)

        # (t, nx, ny) for roughly the last few seconds of play.
        self.ball_history = deque(maxlen=history_len)

        self._last_accepted = None      # (t, nx, ny) that passed the speed gate
        self._last_goal_time = 0.0

        # Disappearance detector state.
        self._mouth_team = None         # team that would score
        self._mouth_since = None        # when the ball entered the mouth

        # Counters worth watching while tuning.
        self.stats = {
            "frames_with_ball": 0,
            "frames_without_ball": 0,
            "rejected_jumps": 0,
            "goals_crossing": 0,
            "goals_disappearance": 0,
            "goals_suppressed_by_cooldown": 0,
        }

    # -- main entry point ------------------------------------------

    def update(self, nx: Optional[float], ny: Optional[float],
               now: Optional[float] = None,
               video_ts_ms: Optional[int] = None) -> Optional[DetectedGoal]:
        """Feed one frame's worth of information.

        Call this EVERY frame, including frames where the ball was not
        detected - passing nx=None is what drives the disappearance
        detector. Returns a DetectedGoal on the frame a goal is called.
        """
        now = time.time() if now is None else now

        if nx is None:
            self.stats["frames_without_ball"] += 1
            return self._check_disappearance(now, video_ts_ms)

        self.stats["frames_with_ball"] += 1

        if not self._accept(now, nx):
            return None

        prev = self._last_accepted
        self._last_accepted = (now, nx, ny)
        self.ball_history.append((now, nx, ny))

        self._update_mouth_state(now, nx, ny)

        if prev is None:
            return None

        scorer = zones.check_crossing(prev[1], prev[2], nx, ny)
        if scorer is None:
            return None
        return self._fire(scorer, "crossing", 0.85, now, video_ts_ms)

    # -- plausibility ----------------------------------------------

    def _accept(self, now: float, nx: float) -> bool:
        """Reject detections implying an impossible ball speed.

        See config.MAX_BALL_SPEED for the arithmetic. Because the check
        is against the last ACCEPTED position and the implied speed decays
        as time passes, a wrong reference point suppresses only a handful
        of frames and then the tracker re-acquires by itself - there is no
        way for this gate to go permanently blind.
        """
        if self._last_accepted is None:
            return True

        prev_t, prev_nx, _ = self._last_accepted
        dt = now - prev_t
        if dt <= 0:
            return True
        speed = abs(nx - prev_nx) / dt
        if speed <= config.MAX_BALL_SPEED:
            return True

        self.stats["rejected_jumps"] += 1
        return False

    # -- disappearance detector ------------------------------------

    def _update_mouth_state(self, now: float, nx: float, ny: Optional[float]):
        team = zones.in_goal_mouth(nx, ny)
        if team is None:
            self._mouth_team = None
            self._mouth_since = None
        elif team != self._mouth_team:
            self._mouth_team = team
            self._mouth_since = now

    def _check_disappearance(self, now: float,
                             video_ts_ms: Optional[int]) -> Optional[DetectedGoal]:
        if not config.DISAPPEARANCE_ENABLED:
            return None
        if self._mouth_team is None or self._last_accepted is None:
            return None

        unseen_for = now - self._last_accepted[0]
        if unseen_for < config.DISAPPEARANCE_TIMEOUT_S:
            return None

        team = self._mouth_team
        # Consume the state so this fires once, not on every subsequent
        # ball-less frame.
        self._mouth_team = None
        self._mouth_since = None
        self._last_accepted = None
        return self._fire(team, "disappearance", 0.60, now, video_ts_ms)

    # -- firing ----------------------------------------------------

    def _fire(self, team: str, detector: str, confidence: float,
              now: float, video_ts_ms: Optional[int]) -> Optional[DetectedGoal]:
        if now - self._last_goal_time < self.goal_cooldown_s:
            # Still cooling down: the ball sitting in the net, or being
            # fished out, must not score again.
            self.stats["goals_suppressed_by_cooldown"] += 1
            return None

        self._last_goal_time = now
        self.stats[f"goals_{detector}"] += 1

        bar_team, bar = self._rod_hint(now)
        goal = DetectedGoal(
            team=team,
            detector=detector,
            confidence=confidence,
            timestamp=now,
            video_ts_ms=video_ts_ms,
            bar_hint=bar,
            bar_hint_team=bar_team,
            track=list(self.ball_history)[-30:],
        )
        if self.on_goal is not None:
            self.on_goal(goal)
        return goal

    def _rod_hint(self, now: float):
        """Where was the ball shortly BEFORE it went in?

        The first draft walked back only until the ball was 0.05 away from
        the goal line - still inside the goal mouth - so it answered
        "goalie" for essentially every goal. Look back a fixed slice of
        time instead.
        """
        cutoff = now - config.ROD_LOOKBACK_S
        candidate = None
        for t, hx, _hy in reversed(self.ball_history):
            if t <= cutoff:
                candidate = hx
                break
        if candidate is None:
            if not self.ball_history:
                return None, "unknown"
            candidate = self.ball_history[0][1]
        return zones.rod_hint(candidate)

    # -- misc ------------------------------------------------------

    def reset(self):
        """Between matches."""
        self.ball_history.clear()
        self._last_accepted = None
        self._last_goal_time = 0.0
        self._mouth_team = None
        self._mouth_since = None
        for key in self.stats:
            self.stats[key] = 0

    @property
    def detection_rate(self) -> float:
        """Fraction of frames the ball was found in. Below ~0.6 during
        active play means the Scout model needs more training data."""
        seen = self.stats["frames_with_ball"]
        total = seen + self.stats["frames_without_ball"]
        return seen / total if total else 0.0
