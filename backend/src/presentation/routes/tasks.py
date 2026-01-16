from fastapi import APIRouter, HTTPException, Depends

from src.domain import RecurrencePattern
from src.application import (
    CreateTask,
    UpdateTask,
    CompleteTask,
    GetAllTasks,
    GetUrgentTasks,
    GetUpcomingTasks,
    DeactivateTask,
    TaskWithUrgency,
)
from src.infrastructure import (
    get_database,
    SQLiteTaskRepository,
    SQLiteCompletionRepository,
    SQLiteMemberRepository,
)
from ..schemas import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    CompleteTaskRequest,
    RecurrencePatternSchema,
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def get_task_repo():
    db = get_database()
    return SQLiteTaskRepository(db)


def get_completion_repo():
    db = get_database()
    return SQLiteCompletionRepository(db)


def get_member_repo():
    db = get_database()
    return SQLiteMemberRepository(db)


def task_with_urgency_to_response(
    twu: TaskWithUrgency,
    member_repo: SQLiteMemberRepository | None = None,
) -> TaskResponse:
    task = twu.task
    assigned_to_name = None
    if task.assigned_to_id and member_repo:
        member = member_repo.get_by_id(task.assigned_to_id)
        if member:
            assigned_to_name = member.name

    return TaskResponse(
        id=task.id,
        name=task.name,
        recurrence=RecurrencePatternSchema(
            type=task.recurrence.type,
            days=list(task.recurrence.days) if task.recurrence.days else None,
            interval=task.recurrence.interval,
            time_of_day=task.recurrence.time_of_day,
        ),
        urgency_label=task.urgency_label,
        calculated_urgency=twu.calculated_urgency,
        last_completed=task.last_completed,
        next_due=task.next_due,
        is_active=task.is_active,
        assigned_to_id=task.assigned_to_id,
        assigned_to_name=assigned_to_name,
        autocomplete=task.autocomplete,
    )


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    active_only: bool = True,
    task_repo: SQLiteTaskRepository = Depends(get_task_repo),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
):
    from src.domain import auto_advance_due_date

    use_case = GetAllTasks(task_repo)
    tasks = use_case.execute(active_only=active_only)

    # Auto-advance overdue autocomplete tasks
    for twu in tasks:
        new_due = auto_advance_due_date(twu.task)
        if new_due:
            twu.task.next_due = new_due
            task_repo.save(twu.task)

    return [task_with_urgency_to_response(t, member_repo) for t in tasks]


@router.get("/urgent", response_model=list[TaskResponse])
def list_urgent_tasks(
    task_repo: SQLiteTaskRepository = Depends(get_task_repo),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
):
    use_case = GetUrgentTasks(task_repo)
    tasks = use_case.execute()
    return [task_with_urgency_to_response(t, member_repo) for t in tasks]


@router.get("/upcoming", response_model=list[TaskResponse])
def list_upcoming_tasks(
    days: int = 7,
    task_repo: SQLiteTaskRepository = Depends(get_task_repo),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
):
    use_case = GetUpcomingTasks(task_repo)
    tasks = use_case.execute(days=days)
    return [task_with_urgency_to_response(t, member_repo) for t in tasks]


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    request: TaskCreateRequest,
    task_repo: SQLiteTaskRepository = Depends(get_task_repo),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
):
    recurrence = RecurrencePattern(
        type=request.recurrence.type,
        days=tuple(request.recurrence.days) if request.recurrence.days else None,
        interval=request.recurrence.interval,
        time_of_day=request.recurrence.time_of_day,
    )

    use_case = CreateTask(task_repo)
    task = use_case.execute(
        name=request.name,
        recurrence=recurrence,
        urgency_label=request.urgency_label,
        next_due=request.next_due,
        assigned_to_id=request.assigned_to_id,
        autocomplete=request.autocomplete,
    )

    from src.domain import calculate_urgency

    urgency = calculate_urgency(task)
    return task_with_urgency_to_response(TaskWithUrgency(task=task, calculated_urgency=urgency), member_repo)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    request: TaskUpdateRequest,
    task_repo: SQLiteTaskRepository = Depends(get_task_repo),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
):
    recurrence = None
    if request.recurrence:
        recurrence = RecurrencePattern(
            type=request.recurrence.type,
            days=tuple(request.recurrence.days) if request.recurrence.days else None,
            interval=request.recurrence.interval,
            time_of_day=request.recurrence.time_of_day,
        )

    # Use model_fields_set to check if assigned_to_id was explicitly provided
    # This allows distinguishing between "not provided" and "set to null"
    assigned_to_id = ... if "assigned_to_id" not in request.model_fields_set else request.assigned_to_id

    use_case = UpdateTask(task_repo)
    task = use_case.execute(
        task_id=task_id,
        name=request.name,
        recurrence=recurrence,
        urgency_label=request.urgency_label,
        next_due=request.next_due,
        is_active=request.is_active,
        assigned_to_id=assigned_to_id,
        autocomplete=request.autocomplete,
    )

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    from src.domain import calculate_urgency

    urgency = calculate_urgency(task)
    return task_with_urgency_to_response(TaskWithUrgency(task=task, calculated_urgency=urgency), member_repo)


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: int,
    request: CompleteTaskRequest | None = None,
    task_repo: SQLiteTaskRepository = Depends(get_task_repo),
    completion_repo: SQLiteCompletionRepository = Depends(get_completion_repo),
    member_repo: SQLiteMemberRepository = Depends(get_member_repo),
):
    use_case = CompleteTask(task_repo, completion_repo)
    member_id = request.member_id if request else None
    result = use_case.execute(task_id=task_id, member_id=member_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task, _ = result
    from src.domain import calculate_urgency

    urgency = calculate_urgency(task)
    return task_with_urgency_to_response(TaskWithUrgency(task=task, calculated_urgency=urgency), member_repo)


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    task_repo: SQLiteTaskRepository = Depends(get_task_repo),
):
    use_case = DeactivateTask(task_repo)
    success = use_case.execute(task_id=task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
