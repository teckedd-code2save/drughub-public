from typing import AsyncGenerator, Annotated
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from google.cloud.sql.connector import Connector, IPTypes
from sqlmodel import SQLModel
from app.utils.logging_util import logger
from app.utils.config import settings
from fastapi import Depends

# Base class for SQLModel models
Base = declarative_base()

async def get_cloud_sql_connection():
    """
    Create an asyncpg connection to Cloud SQL.
    """
    try:
        connector = Connector()
        connection = connector.connect(
            settings.INSTANCE_CONNECTION_NAME,
            "asyncpg",
            user=settings.DB_USER,
            password=settings.DB_PASS,
            db=settings.DB_NAME,
            ip_type=IPTypes.PUBLIC if settings.IP_TYPE == "public" else IPTypes.PRIVATE
        )
        logger.debug(f"Connected to Cloud SQL instance: {settings.INSTANCE_CONNECTION_NAME}")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to Cloud SQL: {str(e)}")
        raise

# Create async engine
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    async_creator=get_cloud_sql_connection if settings.ENVIRONMENT == "production" else None,
    echo=settings.SQLALCHEMY_ECHO
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide an async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Dependency for injection
SessionDep = Annotated[AsyncSession, Depends(get_session)]

async def init_db():
    """
    Initialize database tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables created")

        