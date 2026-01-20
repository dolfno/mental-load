#!/usr/bin/env python3
"""
Custom migration runner for Turso using HTTP API.

This avoids the need for sqlalchemy-libsql which has native dependencies
that don't have ARM64 Linux wheels.

Usage:
    python scripts/migrate.py          # Run all pending migrations
    python scripts/migrate.py current  # Show current version
"""

import importlib.util
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()

from infrastructure.database import TursoConnection, TURSO_URL, TURSO_TOKEN


def get_migrations() -> list[tuple[str, str, Path]]:
    """Get all migrations sorted by revision ID."""
    migrations_dir = Path(__file__).parent.parent / "alembic" / "versions"
    migrations = []

    for file in sorted(migrations_dir.glob("*.py")):
        if file.name.startswith("__"):
            continue

        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        revision = getattr(module, "revision", None)
        down_revision = getattr(module, "down_revision", None)
        if revision:
            migrations.append((revision, down_revision, file, module))

    # Sort by revision (they're numbered 001, 002, etc.)
    return sorted(migrations, key=lambda x: x[0])


def get_current_version(conn: TursoConnection) -> str | None:
    """Get current alembic version from database."""
    try:
        cursor = conn.execute(
            "SELECT version_num FROM alembic_version LIMIT 1"
        )
        row = cursor.fetchone()
        return row["version_num"] if row else None
    except Exception as e:
        if "no such table" in str(e).lower():
            return None
        raise


def ensure_version_table(conn: TursoConnection):
    """Create alembic_version table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        )
    """)


def run_migration(conn: TursoConnection, revision: str, module) -> None:
    """Run a single migration."""
    print(f"  Running migration {revision}...")

    # Create a mock op object that executes SQL directly
    class MockOp:
        @staticmethod
        def execute(sql: str):
            # Split multiple statements if needed
            for stmt in sql.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(stmt)

    # Patch the module's op reference
    module.op = MockOp()

    # Run upgrade
    module.upgrade()


def set_version(conn: TursoConnection, version: str, prev_version: str | None):
    """Update alembic_version table."""
    if prev_version:
        conn.execute(
            "UPDATE alembic_version SET version_num = ?",
            (version,)
        )
    else:
        conn.execute(
            "INSERT INTO alembic_version (version_num) VALUES (?)",
            (version,)
        )


def migrate():
    """Run all pending migrations."""
    if not TURSO_URL or not TURSO_TOKEN:
        print("Error: TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set")
        sys.exit(1)

    print(f"Connecting to Turso: {TURSO_URL}")
    conn = TursoConnection(TURSO_URL, TURSO_TOKEN)

    ensure_version_table(conn)
    current = get_current_version(conn)
    print(f"Current version: {current or '(none)'}")

    migrations = get_migrations()
    pending = []

    # Find migrations that haven't been applied
    found_current = current is None
    for revision, down_revision, path, module in migrations:
        if found_current:
            pending.append((revision, module))
        elif revision == current:
            found_current = True

    if not pending:
        print("No pending migrations.")
        return

    print(f"Pending migrations: {len(pending)}")

    prev_version = current
    for revision, module in pending:
        run_migration(conn, revision, module)
        set_version(conn, revision, prev_version)
        prev_version = revision
        print(f"  Applied {revision}")

    print(f"Done. Current version: {revision}")


def show_current():
    """Show current migration version."""
    if not TURSO_URL or not TURSO_TOKEN:
        print("Error: TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set")
        sys.exit(1)

    conn = TursoConnection(TURSO_URL, TURSO_TOKEN)
    current = get_current_version(conn)
    print(f"Current version: {current or '(none)'}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "current":
        show_current()
    else:
        migrate()
