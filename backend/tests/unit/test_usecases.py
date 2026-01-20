"""Unit tests for use cases with mocked repositories."""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from src.domain import (
    Task,
    HouseholdMember,
    TaskCompletion,
    RecurrencePattern,
    RecurrenceType,
    Urgency,
)
from src.application import (
    CreateTask,
    UpdateTask,
    CompleteTask,
    GetAllTasks,
    GetUrgentTasks,
    DeactivateTask,
    CreateMember,
    GetAllMembers,
)


class TestCreateTask:
    def test_creates_task_with_correct_data(self):
        mock_repo = MagicMock()
        mock_repo.save.return_value = Task(
            id=1,
            name="Test Task",
            recurrence=RecurrencePattern(type=RecurrenceType.DAILY),
        )

        use_case = CreateTask(mock_repo)
        result = use_case.execute(
            name="Test Task",
            recurrence=RecurrencePattern(type=RecurrenceType.DAILY),
        )

        assert result.id == 1
        assert result.name == "Test Task"
        mock_repo.save.assert_called_once()


class TestUpdateTask:
    def test_updates_existing_task(self):
        existing_task = Task(
            id=1,
            name="Old Name",
            recurrence=RecurrencePattern(type=RecurrenceType.DAILY),
        )

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = existing_task
        mock_repo.save.return_value = existing_task

        use_case = UpdateTask(mock_repo)
        result = use_case.execute(task_id=1, name="New Name")

        assert result.name == "New Name"
        mock_repo.save.assert_called_once()

    def test_returns_none_for_nonexistent_task(self):
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None

        use_case = UpdateTask(mock_repo)
        result = use_case.execute(task_id=999, name="New Name")

        assert result is None

    def test_clears_urgency_label_when_set_to_none(self):
        """Test that urgency_label can be explicitly cleared to None."""
        existing_task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.DAILY),
            urgency_label=Urgency.HIGH,
        )

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = existing_task
        mock_repo.save.return_value = existing_task

        use_case = UpdateTask(mock_repo)
        result = use_case.execute(task_id=1, urgency_label=None)

        assert result.urgency_label is None
        mock_repo.save.assert_called_once()

    def test_clears_autocomplete_when_set_to_false(self):
        """Test that autocomplete can be explicitly set to False."""
        existing_task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.DAILY),
            autocomplete=True,
        )

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = existing_task
        mock_repo.save.return_value = existing_task

        use_case = UpdateTask(mock_repo)
        result = use_case.execute(task_id=1, autocomplete=False)

        assert result.autocomplete is False
        mock_repo.save.assert_called_once()

    def test_preserves_urgency_label_when_not_provided(self):
        """Test that urgency_label is not changed when not provided (using Ellipsis)."""
        existing_task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.DAILY),
            urgency_label=Urgency.HIGH,
        )

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = existing_task
        mock_repo.save.return_value = existing_task

        use_case = UpdateTask(mock_repo)
        # Only update name, don't pass urgency_label (uses default ...)
        result = use_case.execute(task_id=1, name="New Name")

        # urgency_label should remain HIGH
        assert result.urgency_label == Urgency.HIGH


class TestCompleteTask:
    def test_completes_task_and_updates_due_date(self):
        task = Task(
            id=1,
            name="Test Task",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY),
            next_due=date.today(),
        )

        mock_task_repo = MagicMock()
        mock_task_repo.get_by_id.return_value = task
        mock_task_repo.save.return_value = task

        mock_completion_repo = MagicMock()
        mock_completion_repo.save.return_value = TaskCompletion(
            id=1,
            task_id=1,
            completed_at=datetime.now(),
            completed_by_id=1,
        )

        use_case = CompleteTask(mock_task_repo, mock_completion_repo)
        result = use_case.execute(task_id=1, member_id=1)

        assert result is not None
        completed_task, completion = result
        assert completed_task.last_completed is not None
        mock_completion_repo.save.assert_called_once()

    def test_returns_none_for_nonexistent_task(self):
        mock_task_repo = MagicMock()
        mock_task_repo.get_by_id.return_value = None
        mock_completion_repo = MagicMock()

        use_case = CompleteTask(mock_task_repo, mock_completion_repo)
        result = use_case.execute(task_id=999, member_id=1)

        assert result is None


class TestGetAllTasks:
    def test_returns_tasks_with_calculated_urgency(self):
        tasks = [
            Task(
                id=1,
                name="Task 1",
                recurrence=RecurrencePattern(type=RecurrenceType.DAILY),
                next_due=date.today(),  # Should be HIGH urgency
            ),
            Task(
                id=2,
                name="Task 2",
                recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY),
                next_due=date.today() + __import__("datetime").timedelta(days=10),  # Should be LOW urgency
            ),
        ]

        mock_repo = MagicMock()
        mock_repo.get_all.return_value = tasks

        use_case = GetAllTasks(mock_repo)
        result = use_case.execute()

        assert len(result) == 2
        assert result[0].calculated_urgency == Urgency.HIGH
        assert result[1].calculated_urgency == Urgency.LOW


class TestGetUrgentTasks:
    def test_returns_only_high_urgency_tasks(self):
        tasks = [
            Task(
                id=1,
                name="Urgent",
                recurrence=RecurrencePattern(type=RecurrenceType.DAILY),
                next_due=date.today(),  # HIGH
            ),
            Task(
                id=2,
                name="Not Urgent",
                recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY),
                next_due=date.today() + __import__("datetime").timedelta(days=10),  # LOW
            ),
        ]

        mock_repo = MagicMock()
        mock_repo.get_all.return_value = tasks

        use_case = GetUrgentTasks(mock_repo)
        result = use_case.execute()

        assert len(result) == 1
        assert result[0].task.name == "Urgent"


class TestDeactivateTask:
    def test_deactivates_existing_task(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.DAILY),
            is_active=True,
        )

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = task
        mock_repo.save.return_value = task

        use_case = DeactivateTask(mock_repo)
        result = use_case.execute(task_id=1)

        assert result is True
        assert task.is_active is False

    def test_returns_false_for_nonexistent_task(self):
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None

        use_case = DeactivateTask(mock_repo)
        result = use_case.execute(task_id=999)

        assert result is False


class TestCreateMember:
    def test_creates_new_member(self):
        mock_repo = MagicMock()
        mock_repo.get_by_name.return_value = None
        mock_repo.save.return_value = HouseholdMember(id=1, name="John")

        use_case = CreateMember(mock_repo)
        result = use_case.execute(name="John")

        assert result.id == 1
        assert result.name == "John"

    def test_returns_existing_member(self):
        existing = HouseholdMember(id=1, name="John")
        mock_repo = MagicMock()
        mock_repo.get_by_name.return_value = existing

        use_case = CreateMember(mock_repo)
        result = use_case.execute(name="John")

        assert result.id == 1
        mock_repo.save.assert_not_called()


class TestGetAllMembers:
    def test_returns_all_members(self):
        members = [
            HouseholdMember(id=1, name="John"),
            HouseholdMember(id=2, name="Jane"),
        ]
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = members

        use_case = GetAllMembers(mock_repo)
        result = use_case.execute()

        assert len(result) == 2
