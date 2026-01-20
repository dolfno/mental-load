import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add src to path so we can import infrastructure modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

# Check for Turso environment variables
TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_with_turso() -> None:
    """Run migrations using Turso HTTP API."""
    from infrastructure.database import TursoConnection

    print(f"Running Alembic migrations against Turso: {TURSO_URL}")
    connection = TursoConnection(TURSO_URL, TURSO_TOKEN)

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        dialect_name="sqlite",
        transactional_ddl=False,  # Turso doesn't support DDL in transactions
    )

    context.run_migrations()
    connection.close()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with local SQLite."""
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


if context.is_offline_mode():
    run_migrations_offline()
elif TURSO_URL and TURSO_TOKEN:
    run_migrations_with_turso()
else:
    run_migrations_online()
