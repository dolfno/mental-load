"""Unit tests for domain layer."""

from datetime import date, datetime, timedelta

import pytest

from src.domain import (
    Task,
    RecurrencePattern,
    RecurrenceType,
    Urgency,
    TimeOfDay,
    calculate_urgency,
    calculate_next_due,
)


class TestCalculateUrgency:
    def test_manual_high_urgency_overrides(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY),
            urgency_label=Urgency.HIGH,
            next_due=date.today() + timedelta(days=30),
        )
        assert calculate_urgency(task) == Urgency.HIGH

    def test_overdue_is_high_urgency(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY),
            next_due=date.today() - timedelta(days=1),
        )
        assert calculate_urgency(task) == Urgency.HIGH

    def test_due_today_is_high_urgency(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY),
            next_due=date.today(),
        )
        assert calculate_urgency(task) == Urgency.HIGH

    def test_due_in_1_to_3_days_is_medium_urgency(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY),
            next_due=date.today() + timedelta(days=2),
        )
        assert calculate_urgency(task) == Urgency.MEDIUM

    def test_due_in_more_than_3_days_is_low_urgency(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY),
            next_due=date.today() + timedelta(days=7),
        )
        assert calculate_urgency(task) == Urgency.LOW

    def test_continuous_task_is_low_urgency(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.CONTINUOUS),
        )
        assert calculate_urgency(task) == Urgency.LOW

    def test_no_due_date_defaults_to_low(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY),
            next_due=None,
        )
        assert calculate_urgency(task) == Urgency.LOW


class TestCalculateNextDue:
    def test_daily_recurrence(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.DAILY),
        )
        completed_at = datetime(2024, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        assert next_due == date(2024, 1, 16)

    def test_daily_with_interval(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.DAILY, interval=3),
        )
        completed_at = datetime(2024, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        assert next_due == date(2024, 1, 18)

    def test_weekly_recurrence(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY),
        )
        completed_at = datetime(2024, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        assert next_due == date(2024, 1, 22)

    def test_biweekly_recurrence(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.BIWEEKLY),
        )
        completed_at = datetime(2024, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        assert next_due == date(2024, 1, 29)

    def test_monthly_recurrence(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.MONTHLY),
        )
        completed_at = datetime(2024, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        assert next_due == date(2024, 2, 15)

    def test_quarterly_recurrence(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.QUARTERLY),
        )
        completed_at = datetime(2024, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        assert next_due == date(2024, 4, 15)

    def test_yearly_recurrence(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.YEARLY),
        )
        completed_at = datetime(2024, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        assert next_due == date(2025, 1, 15)

    def test_continuous_returns_none(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.CONTINUOUS),
        )
        completed_at = datetime(2024, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        assert next_due is None

    def test_weekly_with_specific_days(self):
        # If completed on Monday (weekday 0) and we need Tuesday (1) and Thursday (3)
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY, days=(1, 3)),
        )
        # January 15, 2024 is a Monday (weekday 0)
        completed_at = datetime(2024, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        # Next should be Tuesday, Jan 16
        assert next_due == date(2024, 1, 16)


class TestRecurrencePattern:
    def test_days_converted_to_tuple(self):
        pattern = RecurrencePattern(type=RecurrenceType.WEEKLY, days=[0, 2, 4])
        assert isinstance(pattern.days, tuple)
        assert pattern.days == (0, 2, 4)

    def test_frozen_dataclass(self):
        pattern = RecurrencePattern(type=RecurrenceType.DAILY)
        with pytest.raises(AttributeError):
            pattern.type = RecurrenceType.WEEKLY
