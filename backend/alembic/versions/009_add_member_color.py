"""Add color column to household_members table

Revision ID: 009
Revises: 008
Create Date: 2026-02-15

"""
from typing import Sequence, Union

from alembic import op

revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE household_members ADD COLUMN color TEXT")


def downgrade() -> None:
    pass
