import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, db_path: str = "aivin.db"):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def execute_returning_id(self, query: str, params: tuple = ()) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.lastrowid


_db_instance: Database | None = None


def get_database(db_path: str | None = None) -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path or "aivin.db")
    return _db_instance


def set_database(db: Database) -> None:
    global _db_instance
    _db_instance = db
