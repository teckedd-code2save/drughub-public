from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel
from google.cloud.sql.connector import Connector, IPTypes
from app.utils.config import settings
from app.apis.users.models import User  # Import your models

config = context.config
fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def get_url_and_creator():
    if settings.ENVIRONMENT == "production":
        def getconn():
            connector = Connector()
            return connector.connect(
                settings.INSTANCE_CONNECTION_NAME,
                "pg8000",
                user=settings.DB_USER,
                password=settings.DB_PASS,
                db=settings.DB_NAME,
                ip_type=IPTypes.PUBLIC if settings.IP_TYPE == "public" else IPTypes.PRIVATE,
            )
        return "postgresql+pg8000://", getconn
    else:
        return f"postgresql+pg8000://{settings.DB_USER}:{settings.DB_PASS}@localhost:5433/{settings.DB_NAME}", None


def run_migrations_offline():
    url, _ = get_url_and_creator()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    url, creator = get_url_and_creator()

    if creator:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            url=url,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            creator=creator
        )
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            url=url,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool
        )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
