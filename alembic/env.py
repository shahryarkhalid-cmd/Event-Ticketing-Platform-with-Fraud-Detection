from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context


import os
import sys
from dotenv import load_dotenv
from sqlmodel import SQLModel
import sqlmodel 

# Add your project root to the path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

# Import your models here so Alembic knows about them
from app.models.Users import User


from app.models.Event import Event
from app.models.Ticket import TicketTier

load_dotenv()
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


# --- ADD THIS FUNCTION HERE ---
def render_item(type_, obj, autogen_context):
    if type_ == "type" and isinstance(obj, sqlmodel.sql.sqltypes.AutoString):
        autogen_context.imports.add("import sqlmodel")
    return False 


def run_migrations_offline() -> None:
    url = os.getenv("DATABASE_URL")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,         
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": os.getenv("DATABASE_URL")},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,    
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()