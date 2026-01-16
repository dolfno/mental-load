"""Make completed_by_id nullable

Revision ID: 002
Revises: 001
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
    op.execute("""
        CREATE TABLE task_completions_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES tasks(id),
            completed_at TIMESTAMP NOT NULL,
            completed_by_id INTEGER REFERENCES household_members(id)
        )
    """)

    op.execute("""
        INSERT INTO task_completions_new (id, task_id, completed_at, completed_by_id)
        SELECT id, task_id, completed_at, completed_by_id FROM task_completions
    """)

    op.execute("DROP TABLE task_completions")
    op.execute("ALTER TABLE task_completions_new RENAME TO task_completions")

    # Recreate indexes
    op.execute("CREATE INDEX idx_task_completions_task_id ON task_completions(task_id)")
    op.execute("CREATE INDEX idx_task_completions_completed_by_id ON task_completions(completed_by_id)")


def downgrade() -> None:
    # Note: This will fail if there are NULL values in completed_by_id
    op.execute("""
        CREATE TABLE task_completions_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES tasks(id),
            completed_at TIMESTAMP NOT NULL,
            completed_by_id INTEGER NOT NULL REFERENCES household_members(id)
        )
    """)

    op.execute("""
        INSERT INTO task_completions_new (id, task_id, completed_at, completed_by_id)
        SELECT id, task_id, completed_at, completed_by_id FROM task_completions
        WHERE completed_by_id IS NOT NULL
    """)

    op.execute("DROP TABLE task_completions")
    op.execute("ALTER TABLE task_completions_new RENAME TO task_completions")

    op.execute("CREATE INDEX idx_task_completions_task_id ON task_completions(task_id)")
    op.execute("CREATE INDEX idx_task_completions_completed_by_id ON task_completions(completed_by_id)")
