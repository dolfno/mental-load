"""Add chat_messages table

Revision ID: 011
Revises: 010
Create Date: 2026-02-15

"""
from typing import Sequence, Union

from alembic import op

revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES household_members(id)
        )
    """)
    op.execute("""
        CREATE INDEX ix_chat_messages_user_id
        ON chat_messages (user_id, created_at)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chat_messages_user_id")
    op.execute("DROP TABLE IF EXISTS chat_messages")
