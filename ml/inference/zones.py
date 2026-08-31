"""
Goal and rod geometry. This is the "Game Logic Layer" from
ARCHITECTURE.md - deliberately hand-written maths, not learned. The
network's only job is "where is the ball"; what counts as a goal is
something we can just state.

Everything here works in normalized table coordinates from
inference/homography.py: x from 0.0 (blue goal) to 1.0 (red goal), y
from 0.0 to 1.0 across the width.
"""
import config

BLUE = "blue"
RED = "red"


# ------------------------------------------------------------------
# goals
# ------------------------------------------------------------------

def in_goal_mouth(nx: float, ny: float):
    """Is the ball inside the mouth of a goal right now?

    Returns the team that would SCORE (the ball being at blue's end means
    red scored), or None. Used by the disappearance detector: a ball that
    was here and then vanished almost certainly went in.
    """
    if not _within_goal_width(ny):
        return None
    if nx <= config.GOAL_LINE_BLUE + config.GOAL_MOUTH_DEPTH:
        return RED
    if nx >= config.GOAL_LINE_RED - config.GOAL_MOUTH_DEPTH:
        return BLUE
    return None


def check_crossing(prev_nx: float, prev_ny: float, nx: float, ny: float):
    """Did the ball cross a goal line between these two sightings?

    Tests the SEGMENT between consecutive positions, not the instantaneous
    position. At 90fps a hard shot moves ~15cm per frame, so the ball is
    frequently never observed sitting inside the goal - checking
    `if nx < 0.03` alone silently misses those, which is most of them.

    Returns the scoring team, or None.
    """
    # Crossing towards x=0 (blue's end) scores for red.
    if prev_nx > config.GOAL_LINE_BLUE >= nx:
        if _within_goal_width(_interpolate_y(prev_nx, prev_ny, nx, ny,
                                            config.GOAL_LINE_BLUE)):
            return RED
    # Crossing towards x=1 (red's end) scores for blue.
    if prev_nx < config.GOAL_LINE_RED <= nx:
        if _within_goal_width(_interpolate_y(prev_nx, prev_ny, nx, ny,
                                             config.GOAL_LINE_RED)):
            return BLUE
    return None


def _within_goal_width(ny: float) -> bool:
    if ny is None:
        return True   # no width information - do not block on it
    return config.GOAL_MOUTH_Y_MIN <= ny <= config.GOAL_MOUTH_Y_MAX


def _interpolate_y(x0, y0, x1, y1, x_at):
    """Where across the width was the ball when it crossed the line?"""
    if y0 is None or y1 is None:
        return None
    if x1 == x0:
        return y1
    t = (x_at - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)


# ------------------------------------------------------------------
# rods
# ------------------------------------------------------------------
# Why rod attribution from ball position alone is unreliable:
#
#   blue goal |  bG   b2   r3   b5   r5   b3   r2   rG  | red goal
#                                ^^^^^^^^
# A regulation table INTERLEAVES the two players' rods. Blue's attacking
# 3-bar sits deep in red's half, right next to red's 5-bar. So "the ball
# was at x=0.65" does not tell you whose rod touched it - two rods
# belonging to opposite teams are within a few centimetres of each other
# almost everywhere on the table.
#
# Doing this properly means detecting the rod men and looking for the
# velocity discontinuity when one strikes the ball - that is Phase 3 work.
# Until then `nearest_rod` returns a hint flagged with how ambiguous it
# is, and config.SEND_BAR_HINT is False so we do not act on it.

def nearest_rod(nx: float):
    """Closest rod to this x position.

    Returns (team, bar, ambiguity) where ambiguity is the gap to the
    second-closest rod in normalized units - small means "two rods are
    basically equally likely, do not trust this".
    """
    distances = sorted(
        ((abs(nx - pos), team, bar) for team, bar, pos in config.ROD_POSITIONS),
        key=lambda d: d[0],
    )
    best_dist, team, bar = distances[0]
    runner_up = distances[1][0] if len(distances) > 1 else float("inf")
    return team, bar, runner_up - best_dist


def rod_hint(nx: float, min_ambiguity: float = 0.04):
    """A rod guess, or ("unknown") when two rods are too close to call.

    Honest 'unknown' beats a confident wrong answer: in assisted mode a
    human taps the right bar in one tap, but they have to notice a bad
    prefill first, and they will not.
    """
    team, bar, ambiguity = nearest_rod(nx)
    if ambiguity < min_ambiguity:
        return None, "unknown"
    return team, bar


# Kept for backwards compatibility with the first-draft call sites.
def check_goal(nx: float):
    """Instantaneous position test. Prefer check_crossing - this one
    misses fast shots that are never observed inside the goal."""
    if nx <= config.GOAL_LINE_BLUE:
        return RED
    if nx >= config.GOAL_LINE_RED:
        return BLUE
    return None
