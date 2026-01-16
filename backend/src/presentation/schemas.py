from datetime import date, datetime
from pydantic import BaseModel

from src.domain import RecurrenceType, Urgency, TimeOfDay


class RecurrencePatternSchema(BaseModel):
    type: RecurrenceType
    days: list[int] | None = None
    interval: int = 1
    time_of_day: TimeOfDay | None = None


class TaskCreateRequest(BaseModel):
    name: str
    recurrence: RecurrencePatternSchema
    urgency_label: Urgency | None = None
    next_due: date | None = None


class TaskUpdateRequest(BaseModel):
    name: str | None = None
    recurrence: RecurrencePatternSchema | None = None
    urgency_label: Urgency | None = None
    next_due: date | None = None
    is_active: bool | None = None


class TaskResponse(BaseModel):
    id: int
    name: str
    recurrence: RecurrencePatternSchema
    urgency_label: Urgency | None
    calculated_urgency: Urgency
    last_completed: datetime | None
    next_due: date | None
    is_active: bool


class CompleteTaskRequest(BaseModel):
    member_id: int


class MemberCreateRequest(BaseModel):
    name: str


class MemberResponse(BaseModel):
    id: int
    name: str


class TaskCompletionResponse(BaseModel):
    id: int
    task_id: int
    task_name: str | None = None
    completed_at: datetime
    completed_by_id: int
    completed_by_name: str | None = None
