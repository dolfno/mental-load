from dataclasses import dataclass
from datetime import datetime, date

from .value_objects import RecurrencePattern, Urgency


@dataclass
class Task:
    id: int | None
    name: str
    recurrence: RecurrencePattern
    urgency_label: Urgency | None = None  # manual override
    last_completed: datetime | None = None
    next_due: date | None = None
    is_active: bool = True
    assigned_to_id: int | None = None
    autocomplete: bool = False
    description: str | None = None


@dataclass
class HouseholdMember:
    id: int | None
    name: str
    email: str | None = None
    password_hash: str | None = None


@dataclass
class TaskCompletion:
    id: int | None
    task_id: int
    completed_at: datetime
    completed_by_id: int | None = None


@dataclass
class Note:
    id: int | None
    content: str
    updated_at: datetime
