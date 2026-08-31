import enum


class TeamEnum(enum.Enum):
    """A side of the table. Distinct from WinningTeamEnum, which also has
    to represent 'nobody won yet / draw'."""
    RED = "red"
    BLUE = "blue"
