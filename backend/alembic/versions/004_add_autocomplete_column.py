"""Add autocomplete column to tasks table

Revision ID: 004
Revises: 003
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE tasks ADD COLUMN autocomplete BOOLEAN DEFAULT 0")


def downgrade() -> None:
    # SQLite doesn't support DROP COLUMN, so we need to recreate the table
    op.execute("""
        CREATE TABLE tasks_new (
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
        INSERT INTO tasks_new (id, name, recurrence_type, recurrence_days, recurrence_interval,
                               time_of_day, urgency_label, last_completed, next_due, is_active)
        SELECT id, name, recurrence_type, recurrence_days, recurrence_interval,
               time_of_day, urgency_label, last_completed, next_due, is_active
        FROM tasks
    """)

    op.execute("DROP TABLE tasks")
    op.execute("ALTER TABLE tasks_new RENAME TO tasks")

    # Recreate indexes
    op.execute("CREATE INDEX idx_tasks_next_due ON tasks(next_due)")
    op.execute("CREATE INDEX idx_tasks_is_active ON tasks(is_active)")
