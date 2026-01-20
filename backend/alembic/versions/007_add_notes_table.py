"""Add notes table for notepad feature

Revision ID: 007
Revises: 006
Create Date: 2026-01-20

"""
from typing import Sequence, Union

from alembic import op

revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL
        )
    """)
    # Insert a default empty note for the household
    op.execute("""
        INSERT INTO notes (content, updated_at)
        VALUES ('', datetime('now'))
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notes")
