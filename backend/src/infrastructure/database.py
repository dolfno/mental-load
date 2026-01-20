import logging
import os
import sqlite3
from contextlib import contextmanager
from urllib.request import urlopen, Request
import json

from dotenv import load_dotenv

# Only load .env if not in test environment
if not os.getenv("PYTEST_CURRENT_TEST"):
    load_dotenv()

logger = logging.getLogger(__name__)

# Use Turso HTTP API when TURSO_DATABASE_URL is set
TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")


class TursoConnection:
    """HTTP-based connection to Turso database."""

    def __init__(self, base_url: str, auth_token: str):
        # Convert libsql:// to https:// for HTTP API
        # Handle various URL formats: trailing slashes, existing paths, etc.
        url = base_url.replace("libsql://", "https://")
        # Strip trailing slashes and any path components
        url = url.rstrip("/")
        # Remove any existing path (e.g., /v2/pipeline if already included)
        if "/v2/pipeline" in url:
            url = url.split("/v2/pipeline")[0]
        self.base_url = url
        self.auth_token = auth_token

    def _request(self, statements: list[dict]) -> list[dict]:
        """Execute statements via Turso HTTP API."""
        url = f"{self.base_url}/v2/pipeline"
        payload = {"requests": [{"type": "execute", "stmt": s} for s in statements]}
        payload["requests"].append({"type": "close"})

        req = Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json",
            },
        )

        with urlopen(req) as response:
            result = json.loads(response.read())

        return result.get("results", [])

    def execute(self, sql: str, params: tuple = ()):
        """Execute a single SQL statement."""
        stmt = {"sql": sql}
        if params:
            stmt["args"] = [
                {"type": "null", "value": None} if p is None
                else {"type": "text" if isinstance(p, str) else "integer", "value": str(p)}
                for p in params
            ]

        results = self._request([stmt])
        return TursoCursor(results[0] if results else {})

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class TursoCursor:
    """Cursor-like wrapper for Turso results."""

    def __init__(self, result: dict):
        self.result = result
        self._rows = self._parse_rows()
        self.lastrowid = result.get("response", {}).get("result", {}).get("last_insert_rowid")

    def _parse_rows(self) -> list:
        """Parse Turso response into row dicts."""
        response = self.result.get("response", {})
        result = response.get("result", {})
        cols = result.get("cols", [])
        rows = result.get("rows", [])

        parsed = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(cols):
                col_name = col.get("name", f"col_{i}")
                cell = row[i] if i < len(row) else None
                row_dict[col_name] = self._parse_cell(cell)
            parsed.append(TursoRow(row_dict))
        return parsed

    def _parse_cell(self, cell) -> any:
        """Parse a Turso cell value, converting to appropriate Python type."""
        if not isinstance(cell, dict):
            return cell

        cell_type = cell.get("type")
        value = cell.get("value")

        if cell_type == "null" or value is None:
            return None
        if cell_type == "integer":
            return int(value)
        if cell_type == "float":
            return float(value)
        # text, blob, etc. stay as strings
        return value

    def fetchall(self) -> list:
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class TursoRow:
    """Row that supports both index and key access."""

    def __init__(self, data: dict):
        self._data = data
        self._keys = list(data.keys())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[self._keys[key]]
        return self._data[key]

    def keys(self):
        return self._keys


class Database:
    def __init__(self, db_path: str = "aivin.db", use_turso: bool | None = None):
        self.db_path = db_path
        # Allow explicit override, otherwise auto-detect from env
        if use_turso is not None:
            self.use_turso = use_turso
        else:
            self.use_turso = bool(TURSO_URL and TURSO_TOKEN)
        if self.use_turso:
            logger.info("Database: Using Turso at %s", TURSO_URL)
        else:
            logger.info("Database: Using local SQLite at %s", db_path)

    def _create_connection(self):
        if self.use_turso:
            return TursoConnection(TURSO_URL, TURSO_TOKEN)
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

    @contextmanager
    def get_connection(self):
        conn = self._create_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = ()) -> list:
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
