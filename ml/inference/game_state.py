"""
Tracks ball position over time and turns raw per-frame detections into
discrete game events (goals), with debouncing so a single physical
goal isn't reported multiple times while the ball sits in the net.
"""
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Callable

from inference import zones


@dataclass
class GoalEvent:
    scoring_team: str          # "red" or "blue"
    likely_bar: str            # "5bar" / "3bar" / "goalie" / "2bar"
    timestamp: float = field(default_factory=time.time)


class GameState:
    def __init__(self, on_goal: Callable[["GoalEvent"], None],
                 history_len: int = 60, goal_cooldown_s: float = 3.0):
        self.ball_history = deque(maxlen=history_len)  # (t, nx, ny)
        self.on_goal = on_goal
        self.goal_cooldown_s = goal_cooldown_s
        self._last_goal_time = 0.0

    def update(self, nx: Optional[float], ny: Optional[float]):
        now = time.time()
        if nx is None:
            return  # ball not detected this frame - skip

        self.ball_history.append((now, nx, ny))
        self._maybe_flag_goal(now, nx)

    def _maybe_flag_goal(self, now: float, nx: float):
        if now - self._last_goal_time < self.goal_cooldown_s:
            return  # still cooling down from the last goal

        scorer = zones.check_goal(nx)
        if scorer is None:
            return

        # Look back through recent history to find where the ball was
        # before it crossed the line, to guess which bar it came from.
        pre_goal_x = nx
        for t, hx, hy in reversed(self.ball_history):
            if abs(hx - nx) > 0.05:
                pre_goal_x = hx
                break

        _, bar = zones.get_bar_zone(pre_goal_x)
        event = GoalEvent(scoring_team=scorer, likely_bar=bar)
        self._last_goal_time = now
        self.on_goal(event)
