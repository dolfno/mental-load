from datetime import date, datetime, timedelta
from calendar import monthrange

from .entities import Task
from .value_objects import RecurrenceType, Urgency


def calculate_urgency(task: Task, today: date | None = None) -> Urgency:
    """Calculate the urgency level of a task based on its due date and label."""
    if today is None:
        today = date.today()

    # Manual override takes precedence for high/medium
    if task.urgency_label == Urgency.HIGH:
        return Urgency.HIGH

    # Continuous tasks are always low urgency (they're always visible)
    if task.recurrence.type == RecurrenceType.CONTINUOUS:
        return task.urgency_label or Urgency.LOW

    # No due date - use label or default to low
    if task.next_due is None:
        return task.urgency_label or Urgency.LOW

    days_until_due = (task.next_due - today).days

    # Overdue or due today = high
    if days_until_due <= 0:
        return Urgency.HIGH

    # Manual medium override
    if task.urgency_label == Urgency.MEDIUM:
        return Urgency.MEDIUM

    # Due in 1-3 days = medium
    if days_until_due <= 3:
        return Urgency.MEDIUM

    # Everything else is low
    return task.urgency_label or Urgency.LOW


def calculate_next_due(task: Task, completed_at: datetime | None = None) -> date | None:
    """Calculate the next due date for a task after completion."""
    if completed_at is None:
        completed_at = datetime.now()

    recurrence = task.recurrence
    base_date = completed_at.date()

    if recurrence.type == RecurrenceType.CONTINUOUS:
        return None

    if recurrence.type == RecurrenceType.DAILY:
        return base_date + timedelta(days=recurrence.interval)

    if recurrence.type == RecurrenceType.WEEKLY:
        if recurrence.days:
            # Find next occurrence of one of the specified days
            return _next_weekday(base_date, recurrence.days, recurrence.interval)
        else:
            # Simple weekly interval
            return base_date + timedelta(weeks=recurrence.interval)

    if recurrence.type == RecurrenceType.BIWEEKLY:
        return base_date + timedelta(weeks=2)

    if recurrence.type == RecurrenceType.MONTHLY:
        return _add_months(base_date, recurrence.interval)

    if recurrence.type == RecurrenceType.QUARTERLY:
        return _add_months(base_date, 3)

    if recurrence.type == RecurrenceType.YEARLY:
        if recurrence.interval > 1:
            # X times per year = every 12/X months
            months = 12 // recurrence.interval
            return _add_months(base_date, months)
        else:
            return _add_months(base_date, 12)

    return None


def _next_weekday(base_date: date, weekdays: tuple[int, ...], week_interval: int = 1) -> date:
    """Find the next occurrence of one of the specified weekdays."""
    current_weekday = base_date.weekday()

    # Find next weekday in current week
    for day in sorted(weekdays):
        if day > current_weekday:
            return base_date + timedelta(days=day - current_weekday)

    # Next occurrence is in a future week
    days_to_first_weekday = (min(weekdays) - current_weekday) % 7
    if days_to_first_weekday == 0:
        days_to_first_weekday = 7

    # Add week interval if needed
    if week_interval > 1:
        days_to_first_weekday += (week_interval - 1) * 7

    return base_date + timedelta(days=days_to_first_weekday)


def _add_months(base_date: date, months: int) -> date:
    """Add months to a date, handling month-end edge cases."""
    month = base_date.month - 1 + months
    year = base_date.year + month // 12
    month = month % 12 + 1
    day = min(base_date.day, monthrange(year, month)[1])
    return date(year, month, day)
