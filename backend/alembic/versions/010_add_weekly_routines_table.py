"""Add weekly_routines table

Revision ID: 010
Revises: 009
Create Date: 2026-02-15

"""
from typing import Sequence, Union

from alembic import op

revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE weekly_routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            day_of_week INTEGER NOT NULL,
            time_of_day TEXT NOT NULL,
            assigned_to_id INTEGER,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (assigned_to_id) REFERENCES household_members(id)
        )
    """)
    op.execute("""
        CREATE INDEX ix_weekly_routines_day_time
        ON weekly_routines (day_of_week, time_of_day)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_weekly_routines_day_time")
    op.execute("DROP TABLE IF EXISTS weekly_routines")
