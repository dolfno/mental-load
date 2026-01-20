from dataclasses import dataclass
from datetime import date, datetime, timedelta

from src.domain import (
    Task,
    TaskCompletion,
    RecurrencePattern,
    RecurrenceType,
    Urgency,
    calculate_urgency,
    calculate_next_due,
)
from .interfaces import TaskRepository, CompletionRepository


@dataclass
class TaskWithUrgency:
    task: Task
    calculated_urgency: Urgency


class CreateTask:
    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    def execute(
        self,
        name: str,
        recurrence: RecurrencePattern,
        urgency_label: Urgency | None = None,
        next_due: date | None = None,
        assigned_to_id: int | None = None,
        autocomplete: bool = False,
        description: str | None = None,
    ) -> Task:
        task = Task(
            id=None,
            name=name,
            recurrence=recurrence,
            urgency_label=urgency_label,
            next_due=next_due,
            assigned_to_id=assigned_to_id,
            autocomplete=autocomplete,
            description=description,
        )
        return self.task_repo.save(task)


class UpdateTask:
    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    def execute(
        self,
        task_id: int,
        name: str | None = None,
        recurrence: RecurrencePattern | None = None,
        urgency_label: Urgency | None = ...,
        next_due: date | None = None,
        is_active: bool | None = None,
        assigned_to_id: int | None = ...,
        autocomplete: bool | None = ...,
        description: str | None = ...,
    ) -> Task | None:
        task = self.task_repo.get_by_id(task_id)
        if task is None:
            return None

        if name is not None:
            task.name = name
        if recurrence is not None:
            task.recurrence = recurrence
        if urgency_label is not ...:
            task.urgency_label = urgency_label
        if next_due is not None:
            task.next_due = next_due
        if is_active is not None:
            task.is_active = is_active
        if assigned_to_id is not ...:
            task.assigned_to_id = assigned_to_id
        if autocomplete is not ...:
            task.autocomplete = autocomplete
        if description is not ...:
            task.description = description

        return self.task_repo.save(task)


class CompleteTask:
    def __init__(
        self,
        task_repo: TaskRepository,
        completion_repo: CompletionRepository,
    ):
        self.task_repo = task_repo
        self.completion_repo = completion_repo

    def execute(self, task_id: int, member_id: int | None = None) -> tuple[Task, TaskCompletion] | None:
        task = self.task_repo.get_by_id(task_id)
        if task is None:
            return None

        completed_at = datetime.now()

        # Create completion record
        completion = TaskCompletion(
            id=None,
            task_id=task_id,
            completed_at=completed_at,
            completed_by_id=member_id,
        )
        saved_completion = self.completion_repo.save(completion)

        # Update task with completion info and next due date
        task.last_completed = completed_at
        task.next_due = calculate_next_due(task, completed_at)

        # Deactivate one-time tasks after completion
        if task.recurrence.type == RecurrenceType.EENMALIG:
            task.is_active = False

        saved_task = self.task_repo.save(task)

        return saved_task, saved_completion


class GetAllTasks:
    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    def execute(self, active_only: bool = True) -> list[TaskWithUrgency]:
        tasks = self.task_repo.get_all(active_only=active_only)
        today = date.today()
        return [
            TaskWithUrgency(task=task, calculated_urgency=calculate_urgency(task, today))
            for task in tasks
        ]


class GetUrgentTasks:
    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    def execute(self) -> list[TaskWithUrgency]:
        tasks = self.task_repo.get_all(active_only=True)
        today = date.today()
        result = []
        for task in tasks:
            urgency = calculate_urgency(task, today)
            if urgency == Urgency.HIGH:
                result.append(TaskWithUrgency(task=task, calculated_urgency=urgency))
        return result


class GetUpcomingTasks:
    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    def execute(self, days: int = 7) -> list[TaskWithUrgency]:
        today = date.today()
        end_date = today + timedelta(days=days)
        tasks = self.task_repo.get_by_due_date_range(today, end_date)
        return [
            TaskWithUrgency(task=task, calculated_urgency=calculate_urgency(task, today))
            for task in tasks
        ]


class DeactivateTask:
    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    def execute(self, task_id: int) -> bool:
        task = self.task_repo.get_by_id(task_id)
        if task is None:
            return False

        task.is_active = False
        self.task_repo.save(task)
        return True
