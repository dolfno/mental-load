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
    assigned_to_id: int | None = None
    autocomplete: bool = False
    description: str | None = None


class TaskUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    name: str | None = None
    recurrence: RecurrencePatternSchema | None = None
    urgency_label: Urgency | None = None
    next_due: date | None = None
    is_active: bool | None = None
    assigned_to_id: int | None = None
    # Use model_fields_set to check if assigned_to_id was explicitly provided
    autocomplete: bool | None = None
    description: str | None = None


class TaskResponse(BaseModel):
    id: int
    name: str
    recurrence: RecurrencePatternSchema
    urgency_label: Urgency | None
    calculated_urgency: Urgency
    last_completed: datetime | None
    next_due: date | None
    is_active: bool
    assigned_to_id: int | None
    assigned_to_name: str | None
    autocomplete: bool
    description: str | None


class CompleteTaskRequest(BaseModel):
    member_id: int | None = None


class MemberCreateRequest(BaseModel):
    name: str


class MemberUpdateRequest(BaseModel):
    color: str | None = None


class MemberResponse(BaseModel):
    id: int
    name: str
    color: str | None = None


class TaskCompletionResponse(BaseModel):
    id: int
    task_id: int
    task_name: str | None = None
    completed_at: datetime
    completed_by_id: int | None = None
    completed_by_name: str | None = None


# Auth schemas
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


# Admin schemas
class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str


# Note schemas
class NoteUpdateRequest(BaseModel):
    content: str


class NoteResponse(BaseModel):
    id: int
    content: str
    updated_at: datetime


# Routine schemas
class RoutineCreateRequest(BaseModel):
    name: str
    days_of_week: list[int]
    time_of_day: TimeOfDay
    assigned_to_id: int | None = None


class RoutineAssignRequest(BaseModel):
    assigned_to_id: int | None = None


class RoutineResponse(BaseModel):
    id: int
    name: str
    day_of_week: int
    time_of_day: TimeOfDay
    assigned_to_id: int | None = None
    sort_order: int = 0
