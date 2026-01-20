import json
from datetime import date, datetime

from src.domain import (
    Task,
    HouseholdMember,
    TaskCompletion,
    RecurrencePattern,
    RecurrenceType,
    Urgency,
    TimeOfDay,
)
from src.application import TaskRepository, MemberRepository, CompletionRepository
from .database import Database


class SQLiteTaskRepository(TaskRepository):
    def __init__(self, db: Database):
        self.db = db

    def _row_to_task(self, row) -> Task:
        recurrence_days = None
        if row["recurrence_days"]:
            recurrence_days = tuple(json.loads(row["recurrence_days"]))

        time_of_day = None
        if row["time_of_day"]:
            time_of_day = TimeOfDay(row["time_of_day"])

        recurrence = RecurrencePattern(
            type=RecurrenceType(row["recurrence_type"]),
            days=recurrence_days,
            interval=row["recurrence_interval"] or 1,
            time_of_day=time_of_day,
        )

        urgency_label = None
        if row["urgency_label"]:
            urgency_label = Urgency(row["urgency_label"])

        last_completed = None
        if row["last_completed"]:
            last_completed = datetime.fromisoformat(row["last_completed"])

        next_due = None
        if row["next_due"]:
            next_due = date.fromisoformat(row["next_due"])

        return Task(
            id=row["id"],
            name=row["name"],
            recurrence=recurrence,
            urgency_label=urgency_label,
            last_completed=last_completed,
            next_due=next_due,
            is_active=bool(row["is_active"]),
            assigned_to_id=row["assigned_to_id"],
            autocomplete=bool(row["autocomplete"]) if row["autocomplete"] is not None else False,
        )

    def get_all(self, active_only: bool = True) -> list[Task]:
        query = "SELECT * FROM tasks"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY next_due ASC NULLS LAST"

        rows = self.db.execute(query)
        return [self._row_to_task(row) for row in rows]

    def get_by_id(self, task_id: int) -> Task | None:
        rows = self.db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not rows:
            return None
        return self._row_to_task(rows[0])

    def get_by_due_date_range(self, start: date, end: date) -> list[Task]:
        rows = self.db.execute(
            """SELECT * FROM tasks
               WHERE is_active = 1 AND next_due >= ? AND next_due <= ?
               ORDER BY next_due ASC""",
            (start.isoformat(), end.isoformat()),
        )
        return [self._row_to_task(row) for row in rows]

    def save(self, task: Task) -> Task:
        recurrence_days = None
        if task.recurrence.days:
            recurrence_days = json.dumps(list(task.recurrence.days))

        time_of_day = None
        if task.recurrence.time_of_day:
            time_of_day = task.recurrence.time_of_day.value

        urgency_label = None
        if task.urgency_label:
            urgency_label = task.urgency_label.value

        last_completed = None
        if task.last_completed:
            last_completed = task.last_completed.isoformat()

        next_due = None
        if task.next_due:
            next_due = task.next_due.isoformat()

        if task.id is None:
            task_id = self.db.execute_returning_id(
                """INSERT INTO tasks
                   (name, recurrence_type, recurrence_days, recurrence_interval,
                    time_of_day, urgency_label, last_completed, next_due, is_active,
                    assigned_to_id, autocomplete)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task.name,
                    task.recurrence.type.value,
                    recurrence_days,
                    task.recurrence.interval,
                    time_of_day,
                    urgency_label,
                    last_completed,
                    next_due,
                    1 if task.is_active else 0,
                    task.assigned_to_id,
                    1 if task.autocomplete else 0,
                ),
            )
            task.id = task_id
        else:
            self.db.execute(
                """UPDATE tasks SET
                   name = ?, recurrence_type = ?, recurrence_days = ?,
                   recurrence_interval = ?, time_of_day = ?, urgency_label = ?,
                   last_completed = ?, next_due = ?, is_active = ?, assigned_to_id = ?,
                   autocomplete = ?
                   WHERE id = ?""",
                (
                    task.name,
                    task.recurrence.type.value,
                    recurrence_days,
                    task.recurrence.interval,
                    time_of_day,
                    urgency_label,
                    last_completed,
                    next_due,
                    1 if task.is_active else 0,
                    task.assigned_to_id,
                    1 if task.autocomplete else 0,
                    task.id,
                ),
            )
        return task

    def delete(self, task_id: int) -> bool:
        self.db.execute("UPDATE tasks SET is_active = 0 WHERE id = ?", (task_id,))
        return True

    def count_by_assigned_member(self, member_id: int) -> int:
        rows = self.db.execute(
            "SELECT COUNT(*) as count FROM tasks WHERE assigned_to_id = ?",
            (member_id,),
        )
        return rows[0]["count"] if rows else 0

    def clear_member_assignments(self, member_id: int) -> int:
        """Set assigned_to_id to NULL for all tasks assigned to this member. Returns count of affected rows."""
        count = self.count_by_assigned_member(member_id)
        self.db.execute(
            "UPDATE tasks SET assigned_to_id = NULL WHERE assigned_to_id = ?",
            (member_id,),
        )
        return count


class SQLiteMemberRepository(MemberRepository):
    def __init__(self, db: Database):
        self.db = db

    def _row_to_member(self, row) -> HouseholdMember:
        return HouseholdMember(
            id=row["id"],
            name=row["name"],
            email=row["email"] if "email" in row.keys() else None,
            password_hash=row["password_hash"] if "password_hash" in row.keys() else None,
        )

    def get_all(self) -> list[HouseholdMember]:
        rows = self.db.execute("SELECT * FROM household_members ORDER BY name")
        return [self._row_to_member(row) for row in rows]

    def get_by_id(self, member_id: int) -> HouseholdMember | None:
        rows = self.db.execute(
            "SELECT * FROM household_members WHERE id = ?", (member_id,)
        )
        if not rows:
            return None
        return self._row_to_member(rows[0])

    def get_by_name(self, name: str) -> HouseholdMember | None:
        rows = self.db.execute(
            "SELECT * FROM household_members WHERE name = ?", (name,)
        )
        if not rows:
            return None
        return self._row_to_member(rows[0])

    def get_by_email(self, email: str) -> HouseholdMember | None:
        rows = self.db.execute(
            "SELECT * FROM household_members WHERE email = ?", (email,)
        )
        if not rows:
            return None
        return self._row_to_member(rows[0])

    def save(self, member: HouseholdMember) -> HouseholdMember:
        if member.id is None:
            member_id = self.db.execute_returning_id(
                "INSERT INTO household_members (name, email, password_hash) VALUES (?, ?, ?)",
                (member.name, member.email, member.password_hash),
            )
            member.id = member_id
        else:
            self.db.execute(
                "UPDATE household_members SET name = ?, email = ?, password_hash = ? WHERE id = ?",
                (member.name, member.email, member.password_hash, member.id),
            )
        return member

    def delete(self, member_id: int) -> bool:
        self.db.execute("DELETE FROM household_members WHERE id = ?", (member_id,))
        return True


class SQLiteCompletionRepository(CompletionRepository):
    def __init__(self, db: Database):
        self.db = db

    def _row_to_completion(self, row) -> TaskCompletion:
        return TaskCompletion(
            id=row["id"],
            task_id=row["task_id"],
            completed_at=datetime.fromisoformat(row["completed_at"]),
            completed_by_id=row["completed_by_id"],
        )

    def get_all(self, limit: int | None = None) -> list[TaskCompletion]:
        query = "SELECT * FROM task_completions ORDER BY completed_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        rows = self.db.execute(query)
        return [self._row_to_completion(row) for row in rows]

    def get_by_task(self, task_id: int) -> list[TaskCompletion]:
        rows = self.db.execute(
            "SELECT * FROM task_completions WHERE task_id = ? ORDER BY completed_at DESC",
            (task_id,),
        )
        return [self._row_to_completion(row) for row in rows]

    def get_by_member(self, member_id: int) -> list[TaskCompletion]:
        rows = self.db.execute(
            "SELECT * FROM task_completions WHERE completed_by_id = ? ORDER BY completed_at DESC",
            (member_id,),
        )
        return [self._row_to_completion(row) for row in rows]

    def count_by_member(self, member_id: int) -> int:
        rows = self.db.execute(
            "SELECT COUNT(*) as count FROM task_completions WHERE completed_by_id = ?",
            (member_id,),
        )
        return rows[0]["count"] if rows else 0

    def clear_member_references(self, member_id: int) -> int:
        """Set completed_by_id to NULL for all completions by this member. Returns count of affected rows."""
        count = self.count_by_member(member_id)
        self.db.execute(
            "UPDATE task_completions SET completed_by_id = NULL WHERE completed_by_id = ?",
            (member_id,),
        )
        return count

    def save(self, completion: TaskCompletion) -> TaskCompletion:
        if completion.id is None:
            completion_id = self.db.execute_returning_id(
                """INSERT INTO task_completions
                   (task_id, completed_at, completed_by_id)
                   VALUES (?, ?, ?)""",
                (
                    completion.task_id,
                    completion.completed_at.isoformat(),
                    completion.completed_by_id,
                ),
            )
            completion.id = completion_id
        return completion
