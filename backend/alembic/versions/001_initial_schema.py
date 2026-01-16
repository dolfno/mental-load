"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            recurrence_type TEXT NOT NULL,
            recurrence_days TEXT,
            recurrence_interval INTEGER DEFAULT 1,
            time_of_day TEXT,
            urgency_label TEXT,
            last_completed TIMESTAMP,
            next_due DATE,
            is_active BOOLEAN DEFAULT 1
        )
    """)

    op.execute("""
        CREATE TABLE household_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    op.execute("""
        CREATE TABLE task_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES tasks(id),
            completed_at TIMESTAMP NOT NULL,
            completed_by_id INTEGER NOT NULL REFERENCES household_members(id)
        )
    """)

    op.execute("CREATE INDEX idx_task_completions_task_id ON task_completions(task_id)")
    op.execute("CREATE INDEX idx_task_completions_completed_by_id ON task_completions(completed_by_id)")
    op.execute("CREATE INDEX idx_tasks_next_due ON tasks(next_due)")
    op.execute("CREATE INDEX idx_tasks_is_active ON tasks(is_active)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_tasks_is_active")
    op.execute("DROP INDEX IF EXISTS idx_tasks_next_due")
    op.execute("DROP INDEX IF EXISTS idx_task_completions_completed_by_id")
    op.execute("DROP INDEX IF EXISTS idx_task_completions_task_id")
    op.execute("DROP TABLE IF EXISTS task_completions")
    op.execute("DROP TABLE IF EXISTS household_members")
    op.execute("DROP TABLE IF EXISTS tasks")
