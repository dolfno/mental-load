from dataclasses import dataclass
from enum import Enum


class RecurrenceType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CONTINUOUS = "continuous"


class Urgency(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TimeOfDay(str, Enum):
    MORNING = "morning"
    EVENING = "evening"


@dataclass(frozen=True)
class RecurrencePattern:
    type: RecurrenceType
    days: tuple[int, ...] | None = None  # for weekly: (0=Mon, 6=Sun)
    interval: int = 1  # every X days/weeks/months
    time_of_day: TimeOfDay | None = None

    def __post_init__(self):
        if self.days is not None and not isinstance(self.days, tuple):
            object.__setattr__(self, 'days', tuple(self.days))
