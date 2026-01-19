"""Add auth fields to household_members

Revision ID: 006
Revises: 005
Create Date: 2026-01-19

"""
from typing import Sequence, Union

from alembic import op

revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE household_members ADD COLUMN email TEXT")
    op.execute("ALTER TABLE household_members ADD COLUMN password_hash TEXT")
    op.execute("CREATE UNIQUE INDEX idx_household_members_email ON household_members(email)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_household_members_email")
    # SQLite doesn't support DROP COLUMN directly, would need table rebuild
    # For simplicity, we leave the columns in place on downgrade
