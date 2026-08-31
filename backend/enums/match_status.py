import enum


class MatchStatusEnum(enum.Enum):
    """Lifecycle of a match row.

    A match is now created when the players are picked (IN_PROGRESS), not
    when it ends - the vision service and the goal_events table both need
    something to attach to while the game is still being played.
    """
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
