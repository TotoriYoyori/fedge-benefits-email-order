from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from src.config import settings
from src.database import Base

# ----- Current tracking models -----
from src.auth.models import User
from src.google.models import GoogleOAuthCredential, GoogleOAuthState
from src.orders.models import Orders
# ------------------------------------

# ----- The Alembic Config object, provides access to the values within the alembic.ini file.
config = context.config

# ----- Interpret the config file for Python logging. This line sets up loggers basically.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# ----- Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# ----- Converting between FastAPI's async database URL to sync version for Alembic.
def get_sync_url(url: str) -> str:
    """Convert an async database URL to a sync one for Alembic."""
    if url.startswith("sqlite+aiosqlite"):
        return url.replace("sqlite+aiosqlite", "sqlite")

    if url.startswith("postgresql+asyncpg"):
        return url.replace("postgresql+asyncpg", "postgresql")
    return url


sync_url = get_sync_url(settings.DATABASE_URL)
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
