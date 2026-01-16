"""Add task assignment

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
    op.execute("ALTER TABLE tasks ADD COLUMN assigned_to_id INTEGER REFERENCES household_members(id)")
    op.execute("CREATE INDEX idx_tasks_assigned_to_id ON tasks(assigned_to_id)")


def downgrade() -> None:
    op.execute("DROP INDEX idx_tasks_assigned_to_id")
    # SQLite doesn't support DROP COLUMN directly, would need table rebuild
    # For simplicity, we leave the column in place on downgrade
