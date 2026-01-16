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

    def test_eenmalig_task_is_low_urgency(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.EENMALIG),
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

    def test_eenmalig_returns_none(self):
        task = Task(
            id=1,
            name="Test",
            recurrence=RecurrencePattern(type=RecurrenceType.EENMALIG),
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

    # --- Late/Postponed Completion Scenarios (Sliding Schedule) ---

    def test_daily_completed_late_slides_schedule(self):
        """Daily task completed late - schedule slides from completion date."""
        # Task every 3 days, originally due Monday Jan 6, completed Tuesday Jan 7
        task = Task(
            id=1,
            name="Water plants",
            recurrence=RecurrencePattern(type=RecurrenceType.DAILY, interval=3),
        )
        # Completed 1 day late
        completed_at = datetime(2025, 1, 7, 10, 0)  # Tuesday
        next_due = calculate_next_due(task, completed_at)
        # Next due is Friday Jan 10 (3 days from completion)
        assert next_due == date(2025, 1, 10)

    def test_weekly_no_days_completed_late_slides_schedule(self):
        """Weekly task (no specific days) completed late - schedule slides."""
        # Task due every week, originally due Monday Jan 6, completed Wednesday Jan 8
        task = Task(
            id=1,
            name="Vacuum",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY, interval=1),
        )
        # Completed 2 days late
        completed_at = datetime(2025, 1, 8, 10, 0)  # Wednesday
        next_due = calculate_next_due(task, completed_at)
        # Next due is Wednesday Jan 15 (7 days from completion)
        assert next_due == date(2025, 1, 15)

    def test_weekly_specific_days_completed_late_finds_next_day(self):
        """Weekly task (specific days) completed late - finds next scheduled day."""
        # Task due Tuesdays only, originally due Tuesday Jan 7, completed Thursday Jan 9
        task = Task(
            id=1,
            name="Laundry",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY, days=(1,)),  # Tuesday
        )
        # Completed 2 days late (on Thursday)
        completed_at = datetime(2025, 1, 9, 10, 0)  # Thursday (weekday 3)
        next_due = calculate_next_due(task, completed_at)
        # Next due is Tuesday Jan 14 (next Tuesday after completion)
        assert next_due == date(2025, 1, 14)

    # --- Weekly with Specific Days Edge Cases ---

    def test_weekly_specific_days_completed_on_scheduled_day(self):
        """Weekly task completed on a scheduled day - next is the next scheduled day."""
        # Task due Tue (1) and Thu (3), completed on Tuesday Jan 7
        task = Task(
            id=1,
            name="Laundry",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY, days=(1, 3)),
        )
        completed_at = datetime(2025, 1, 7, 10, 0)  # Tuesday (weekday 1)
        next_due = calculate_next_due(task, completed_at)
        # Next due is Thursday Jan 9 (next scheduled day in same week)
        assert next_due == date(2025, 1, 9)

    def test_weekly_specific_days_completed_after_last_scheduled_day(self):
        """Weekly task completed after all scheduled days - wraps to next week."""
        # Task due Tue (1) and Thu (3), completed on Friday Jan 10
        task = Task(
            id=1,
            name="Laundry",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY, days=(1, 3)),
        )
        completed_at = datetime(2025, 1, 10, 10, 0)  # Friday (weekday 4)
        next_due = calculate_next_due(task, completed_at)
        # Next due is Tuesday Jan 14 (first scheduled day of next week)
        assert next_due == date(2025, 1, 14)

    def test_weekly_single_day_completed_on_that_day(self):
        """Weekly task with single day, completed on that day - next is same day next week."""
        # Task due Monday only, completed on Monday
        task = Task(
            id=1,
            name="Weekly meeting",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY, days=(0,)),  # Monday
        )
        completed_at = datetime(2025, 1, 6, 10, 0)  # Monday (weekday 0)
        next_due = calculate_next_due(task, completed_at)
        # Next due is Monday Jan 13
        assert next_due == date(2025, 1, 13)

    # --- Weekly with Interval > 1 and Specific Days ---

    def test_weekly_interval_2_with_specific_day(self):
        """Every 2 weeks on Tuesday."""
        task = Task(
            id=1,
            name="Biweekly laundry",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY, interval=2, days=(1,)),  # Tuesday
        )
        # Complete on Tuesday Jan 7
        completed_at = datetime(2025, 1, 7, 10, 0)  # Tuesday
        next_due = calculate_next_due(task, completed_at)
        # Next due is Tuesday Jan 21 (2 weeks later)
        assert next_due == date(2025, 1, 21)

    def test_weekly_interval_2_no_days(self):
        """Every 2 weeks (flexible)."""
        task = Task(
            id=1,
            name="Change bed sheets",
            recurrence=RecurrencePattern(type=RecurrenceType.WEEKLY, interval=2),
        )
        completed_at = datetime(2025, 1, 6, 10, 0)  # Monday
        next_due = calculate_next_due(task, completed_at)
        # Next due is Monday Jan 20 (14 days later)
        assert next_due == date(2025, 1, 20)

    # --- Monthly Edge Cases ---

    def test_monthly_end_of_month_clamps(self):
        """Monthly task on Jan 31 - clamps to Feb 28/29."""
        task = Task(
            id=1,
            name="Monthly review",
            recurrence=RecurrencePattern(type=RecurrenceType.MONTHLY),
        )
        # Complete on Jan 31
        completed_at = datetime(2025, 1, 31, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        # Feb 2025 has 28 days, so clamps to Feb 28
        assert next_due == date(2025, 2, 28)

    def test_monthly_end_of_month_leap_year(self):
        """Monthly task on Jan 31 in leap year - clamps to Feb 29."""
        task = Task(
            id=1,
            name="Monthly review",
            recurrence=RecurrencePattern(type=RecurrenceType.MONTHLY),
        )
        # Complete on Jan 31, 2024 (leap year)
        completed_at = datetime(2024, 1, 31, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        # Feb 2024 has 29 days
        assert next_due == date(2024, 2, 29)

    def test_monthly_with_interval(self):
        """Every 2 months."""
        task = Task(
            id=1,
            name="Deep clean fridge",
            recurrence=RecurrencePattern(type=RecurrenceType.MONTHLY, interval=2),
        )
        completed_at = datetime(2025, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        # Next due is March 15
        assert next_due == date(2025, 3, 15)

    # --- Yearly with Interval > 1 ---

    def test_yearly_twice_per_year(self):
        """Yearly with interval=2 means twice per year (every 6 months)."""
        task = Task(
            id=1,
            name="Seasonal cleaning",
            recurrence=RecurrencePattern(type=RecurrenceType.YEARLY, interval=2),
        )
        completed_at = datetime(2025, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        # 12/2 = 6 months later
        assert next_due == date(2025, 7, 15)

    def test_yearly_three_times_per_year(self):
        """Yearly with interval=3 means 3x per year (every 4 months)."""
        task = Task(
            id=1,
            name="Deep clean rooms",
            recurrence=RecurrencePattern(type=RecurrenceType.YEARLY, interval=3),
        )
        completed_at = datetime(2025, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        # 12/3 = 4 months later
        assert next_due == date(2025, 5, 15)

    def test_yearly_four_times_per_year(self):
        """Yearly with interval=4 means quarterly (every 3 months)."""
        task = Task(
            id=1,
            name="Quarterly task",
            recurrence=RecurrencePattern(type=RecurrenceType.YEARLY, interval=4),
        )
        completed_at = datetime(2025, 1, 15, 10, 0)
        next_due = calculate_next_due(task, completed_at)
        # 12/4 = 3 months later
        assert next_due == date(2025, 4, 15)


class TestRecurrencePattern:
    def test_days_converted_to_tuple(self):
        pattern = RecurrencePattern(type=RecurrenceType.WEEKLY, days=[0, 2, 4])
        assert isinstance(pattern.days, tuple)
        assert pattern.days == (0, 2, 4)

    def test_frozen_dataclass(self):
        pattern = RecurrencePattern(type=RecurrenceType.DAILY)
        with pytest.raises(AttributeError):
            pattern.type = RecurrenceType.WEEKLY
