import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

# Add the project root to the Python path
# Assumes env.py is in alembic/ directory, one level below project root
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Import your models' Base metadata
# Make sure the models are imported somewhere before Base is used
from breachwatch.storage.database import Base
from breachwatch.storage import models # Ensure models are imported to be registered with Base
from breachwatch.utils.config_loader import get_settings # To get DB URL

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Function to get database URL from settings or environment
def get_url():
    # Use the centralized config loader
    settings = get_settings()
    db_url = settings.DATABASE_URL
    if not db_url:
         # Fallback: try reading directly from environment if config loader fails initially
         db_url = os.getenv("DATABASE_URL")
         if not db_url:
             raise ValueError("DATABASE_URL not set in environment or .env file. Cannot connect for migrations.")
    return db_url.replace(settings.DB_PASSWORD, '********') if settings.DB_PASSWORD else db_url # Mask password in logs

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url() # Use helper to get URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True, # Detect column type changes
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get database configuration from alembic.ini or environment
    connectable_config = config.get_section(config.config_ini_section)
    # Override sqlalchemy.url with the one from our settings/env loader
    connectable_config["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        connectable_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True, # Detect column type changes
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

