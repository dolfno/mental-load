"""Rename continuous to eenmalig

Revision ID: 003
Revises: 002
Create Date: 2026-01-16

"""
from typing import Sequence, Union

from alembic import op

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE tasks SET recurrence_type = 'eenmalig' WHERE recurrence_type = 'continuous'")


def downgrade() -> None:
    op.execute("UPDATE tasks SET recurrence_type = 'continuous' WHERE recurrence_type = 'eenmalig'")
