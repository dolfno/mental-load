import importlib.util
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

# Check for Turso environment
TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")


def run_migrations_turso() -> None:
    """Run migrations against Turso using HTTP API (no native deps needed)."""
    # Add src to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from infrastructure.database import TursoConnection

    print(f"Running migrations against Turso: {TURSO_URL}")
    conn = TursoConnection(TURSO_URL, TURSO_TOKEN)

    # Ensure alembic_version table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        )
    """)

    # Get current version
    cursor = conn.execute("SELECT version_num FROM alembic_version LIMIT 1")
    row = cursor.fetchone()
    current_version = row["version_num"] if row else None
    print(f"Current version: {current_version or '(none)'}")

    # Load all migrations
    migrations_dir = Path(__file__).parent / "versions"
    migrations = []
    for file in sorted(migrations_dir.glob("*.py")):
        if file.name.startswith("__"):
            continue
        spec = importlib.util.spec_from_file_location(file.stem, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        revision = getattr(module, "revision", None)
        if revision:
            migrations.append((revision, module))

    # Find pending migrations
    pending = []
    found_current = current_version is None
    for revision, module in migrations:
        if found_current:
            pending.append((revision, module))
        elif revision == current_version:
            found_current = True

    if not pending:
        print("No pending migrations.")
        return

    print(f"Pending migrations: {len(pending)}")

    # Mock op.execute to use TursoConnection
    class MockOp:
        @staticmethod
        def execute(sql: str):
            for stmt in sql.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(stmt)

    # Run each migration
    for revision, module in pending:
        print(f"  Running {revision}...")
        module.op = MockOp()
        module.upgrade()

        # Update version
        if current_version:
            conn.execute("UPDATE alembic_version SET version_num = ?", (revision,))
        else:
            conn.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (revision,))
        current_version = revision

    print(f"Done. Current version: {current_version}")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQLite)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (SQLite)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


# Choose migration strategy based on environment
if TURSO_URL and TURSO_TOKEN:
    run_migrations_turso()
elif context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
