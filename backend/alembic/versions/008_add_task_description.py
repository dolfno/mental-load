"""Add description column to tasks table

Revision ID: 008
Revises: 007
Create Date: 2026-01-20

"""
from typing import Sequence, Union

from alembic import op

revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE tasks ADD COLUMN description TEXT")


def downgrade() -> None:
    # SQLite doesn't support DROP COLUMN directly, would need table rebuild
    # For simplicity, we leave the column in place on downgrade
    pass
