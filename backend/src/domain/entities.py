from dataclasses import dataclass
from datetime import datetime, date

from .value_objects import RecurrencePattern, Urgency, TimeOfDay


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
    color: str | None = None


@dataclass
class TaskCompletion:
    id: int | None
    task_id: int
    completed_at: datetime
    completed_by_id: int | None = None


@dataclass
class WeeklyRoutine:
    id: int | None
    name: str
    day_of_week: int  # 0=Mon, 6=Sun
    time_of_day: TimeOfDay
    assigned_to_id: int | None = None
    sort_order: int = 0


@dataclass
class Note:
    id: int | None
    content: str
    updated_at: datetime


@dataclass
class ChatMessage:
    id: int | None
    user_id: int
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime
