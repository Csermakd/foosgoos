"""
Unit tests for the goal logic - the part that decides what gets written
into someone's stats. These run without a camera, without weights and
without a GPU: they replay synthetic ball trajectories through GameState.

Run with:  python -m pytest tests -q     (from the ml/ directory)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from inference import zones
from inference.game_state import GameState


FRAME_DT = 1 / 90.0   # the camera's frame interval


def roll(state, points, t0=1000.0, dt=FRAME_DT):
    """Feed a list of (nx, ny) - or None for 'ball not detected' - through
    GameState at a fixed frame rate. Returns every goal that fired."""
    goals = []
    t = t0
    for point in points:
        nx, ny = (None, None) if point is None else point
        goal = state.update(nx, ny, now=t)
        if goal:
            goals.append(goal)
        t += dt
    return goals


def straight_shot(x_from, x_to, ny=0.5, steps=10):
    step = (x_to - x_from) / steps
    return [(x_from + step * i, ny) for i in range(steps + 1)]


# ------------------------------------------------------------------
# crossing detector
# ------------------------------------------------------------------

def test_shot_into_blue_goal_scores_red():
    state = GameState()
    goals = roll(state, straight_shot(0.5, -0.02))
    assert len(goals) == 1
    assert goals[0].team == "red"
    assert goals[0].detector == "crossing"


def test_shot_into_red_goal_scores_blue():
    state = GameState()
    goals = roll(state, straight_shot(0.5, 1.02))
    assert len(goals) == 1
    assert goals[0].team == "blue"


def test_fast_shot_never_seen_inside_the_goal_still_scores():
    """The whole reason check_crossing exists: at 90fps the ball can jump
    from clearly-outside to clearly-past between two frames."""
    state = GameState()
    goals = roll(state, [(0.20, 0.5), (0.09, 0.5), (-0.03, 0.5)])
    assert len(goals) == 1
    assert goals[0].team == "red"


def test_midfield_play_scores_nothing():
    state = GameState()
    points = straight_shot(0.2, 0.8) + straight_shot(0.8, 0.2)
    assert roll(state, points) == []


def test_ball_along_the_end_wall_is_not_a_goal():
    """Rolling across the end of the table outside the goal mouth."""
    state = GameState()
    goals = roll(state, straight_shot(0.5, -0.02, ny=0.05))
    assert goals == []


def test_one_physical_goal_fires_once():
    """Ball crosses, then gets jostled back and forth over the goal line
    while someone fishes it out. That is one goal, not eleven."""
    state = GameState()
    points = straight_shot(0.5, -0.02) + \
             [(0.06, 0.5), (-0.02, 0.5)] * 10
    goals = roll(state, points)
    assert len(goals) == 1
    assert state.stats["goals_suppressed_by_cooldown"] >= 1


def test_two_goals_separated_by_more_than_the_cooldown():
    state = GameState()
    goals = roll(state, straight_shot(0.5, -0.02))
    # Re-serve well after the cooldown, then score at the other end.
    goals += roll(state, straight_shot(0.5, 1.02),
                  t0=1000.0 + config.GOAL_COOLDOWN_S + 2.0)
    assert [g.team for g in goals] == ["red", "blue"]


# ------------------------------------------------------------------
# disappearance detector
# ------------------------------------------------------------------

def test_ball_vanishing_in_the_goal_mouth_scores():
    """What actually happens most of the time: the ball drops out of
    sight into the return channel and is simply never seen crossing."""
    state = GameState()
    approach = [(0.20, 0.5), (0.14, 0.5), (0.08, 0.5), (0.05, 0.5)]
    blind = [None] * 120       # ~1.3s with no ball
    goals = roll(state, approach + blind)
    assert len(goals) == 1
    assert goals[0].team == "red"
    assert goals[0].detector == "disappearance"


def test_ball_vanishing_in_midfield_scores_nothing():
    """Occlusion by a hand or a rod man is not a goal."""
    state = GameState()
    goals = roll(state, [(0.5, 0.5), (0.52, 0.5)] + [None] * 200)
    assert goals == []


def test_ball_reappearing_before_the_timeout_scores_nothing():
    state = GameState()
    brief_gap = [None] * 20    # ~0.22s, under DISAPPEARANCE_TIMEOUT_S
    goals = roll(state, [(0.20, 0.5), (0.06, 0.5)] + brief_gap + [(0.20, 0.5)])
    assert goals == []


def test_disappearance_fires_only_once():
    state = GameState()
    goals = roll(state, [(0.20, 0.5), (0.05, 0.5)] + [None] * 500)
    assert len(goals) == 1


# ------------------------------------------------------------------
# plausibility gate
# ------------------------------------------------------------------

def test_teleporting_detection_is_ignored():
    """A single frame where the detector latches onto a red shirt at the
    far end must not register as a shot on goal."""
    state = GameState()
    points = [(0.50, 0.5), (0.51, 0.5), (-0.02, 0.5), (0.52, 0.5), (0.53, 0.5)]
    goals = roll(state, points)
    assert goals == []
    assert state.stats["rejected_jumps"] == 1


def test_the_gate_self_heals_and_cannot_blind_us():
    """Suppose a spurious detection becomes our reference point. The gate
    must not then reject the real ball forever - the implied speed decays
    with elapsed time, so we re-acquire within a few frames."""
    state = GameState()
    roll(state, [(0.95, 0.5)])                       # bad reference
    roll(state, [(0.05, 0.5)] * 10, t0=1000.0 + FRAME_DT)
    assert state.stats["rejected_jumps"] > 0         # first frames suppressed
    assert state._last_accepted[1] == 0.05           # ...then re-acquired


def test_a_genuinely_fast_shot_is_not_rejected():
    """A 30mph slam is ~11 table-lengths/sec and MUST survive the gate.
    The first draft's limit of 12 sat right on top of that, so real goals
    were being thrown away as implausible."""
    state = GameState()
    goals = roll(state, straight_shot(0.9, -0.02, steps=8))   # ~11.5 lengths/s
    assert state.stats["rejected_jumps"] == 0
    assert len(goals) == 1


def test_the_speed_gate_is_framerate_independent():
    """Same physical shot, sampled at 30fps instead of 90, must behave
    identically - the gate is in lengths/second, not pixels/frame."""
    state = GameState()
    goals = roll(state, straight_shot(0.9, -0.02, steps=3), dt=1 / 30.0)
    assert state.stats["rejected_jumps"] == 0
    assert len(goals) == 1


# ------------------------------------------------------------------
# rod hint
# ------------------------------------------------------------------

def test_rod_hint_looks_back_in_time_not_in_distance():
    """The first draft walked back until the ball was 0.05 from the line -
    still inside the mouth - so every goal was blamed on the goalie."""
    state = GameState()
    # Ball dwells near blue's 3-bar (x=0.72) then is slammed into red's goal.
    dwell = [(0.72, 0.5)] * 60          # ~0.67s of possession
    goals = roll(state, dwell + straight_shot(0.72, 1.02, steps=8))
    assert len(goals) == 1
    assert goals[0].bar_hint == "3bar"
    assert goals[0].bar_hint_team == "blue"


def test_ambiguous_rod_positions_report_unknown():
    """Mid-table the rods interleave, so no honest answer exists."""
    state = GameState()
    dwell = [(0.50, 0.5)] * 60
    goals = roll(state, dwell + straight_shot(0.50, 1.02, steps=10))
    assert len(goals) == 1
    assert goals[0].bar_hint == "unknown"


# ------------------------------------------------------------------
# bookkeeping
# ------------------------------------------------------------------

def test_detection_rate_tracks_missed_frames():
    state = GameState()
    roll(state, [(0.5, 0.5), None, (0.5, 0.5), None])
    assert state.detection_rate == 0.5


def test_every_goal_gets_a_unique_id():
    """The backend dedupes on event_uuid, so a collision would silently
    swallow a real goal."""
    state = GameState()
    goals = roll(state, straight_shot(0.5, -0.02))
    goals += roll(state, straight_shot(0.5, 1.02),
                  t0=1000.0 + config.GOAL_COOLDOWN_S + 2.0)
    assert len({g.event_uuid for g in goals}) == 2


def test_reset_clears_state_between_matches():
    state = GameState()
    roll(state, straight_shot(0.5, -0.02))
    state.reset()
    assert state.stats["goals_crossing"] == 0
    assert state._last_accepted is None


def test_callback_fires():
    seen = []
    state = GameState(on_goal=seen.append)
    roll(state, straight_shot(0.5, -0.02))
    assert len(seen) == 1


# ------------------------------------------------------------------
# zone maths
# ------------------------------------------------------------------

def test_rods_are_in_real_interleaved_order():
    """A regulation table alternates sides down its length. If this ever
    becomes 'all blue rods then all red rods', the layout is wrong."""
    teams = [team for team, _bar, _pos in config.ROD_POSITIONS]
    assert teams == ["blue", "blue", "red", "blue", "red", "blue", "red", "red"]
    positions = [pos for _t, _b, pos in config.ROD_POSITIONS]
    assert positions == sorted(positions)


def test_every_rod_is_reachable():
    """The first draft mapped 3bar and 5bar to the identical x range, so
    5bar could never be returned by any lookup."""
    reachable = set()
    for i in range(1001):
        team, bar, _ = zones.nearest_rod(i / 1000)
        reachable.add((team, bar))
    assert reachable == {(t, b) for t, b, _ in config.ROD_POSITIONS}
