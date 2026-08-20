import enum


class GoalSourceEnum(enum.Enum):
    """Who produced this goal event."""
    MANUAL = "manual"   # a human tapped a button in the app
    CAMERA = "camera"   # the vision service detected it


class GoalStatusEnum(enum.Enum):
    """Review state of a goal event.

    PENDING_REVIEW and CONFIRMED both count towards the score - the camera
    is trusted by default so the scoreboard is correct even if nobody is
    looking at the tablet. PENDING_REVIEW just means no human has agreed
    with it yet, so the UI highlights it as correctable.
    """
    PENDING_REVIEW = "pending_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"   # a human said "that wasn't a goal" - does not score


class GoalBarEnum(enum.Enum):
    """Which rod the ball came off. UNKNOWN is a first-class answer: the
    camera usually cannot tell (the rods interleave down the table), and
    an honest 'unknown' is better than a confident guess."""
    FIVE_BAR = "5bar"
    THREE_BAR = "3bar"
    TWO_BAR = "2bar"
    GOALIE = "goalie"
    UNKNOWN = "unknown"
