"""
Zone / goal math, per ARCHITECTURE.md's "Game Logic Layer (Math, not
ML)": once the ball's normalized table position is known, zones and
goals are hard-coded thresholds rather than learned.
"""
import config


def check_goal(nx: float):
    """Crossing the BLUE goal line means RED scored, and vice versa."""
    if nx <= config.GOAL_LINE_BLUE:
        return "red"
    if nx >= config.GOAL_LINE_RED:
        return "blue"
    return None


def get_bar_zone(nx: float):
    """Best guess at which bar the ball was nearest to, used to
    pre-fill the frontend GoalModal's offense/defense + goal-type
    selection (the human still confirms/edits it)."""
    for zone, (lo, hi) in config.ZONE_BOUNDARIES_BLUE_SIDE.items():
        if lo <= nx < hi:
            return "blue", zone
    for zone, (lo, hi) in config.ZONE_BOUNDARIES_RED_SIDE.items():
        if lo <= nx < hi:
            return "red", zone
    return None, "3bar"  # midfield / contested -> defaults to 3bar
