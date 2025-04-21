import os
from typing import Annotated
from google.cloud.sql.connector import Connector, IPTypes
import pg8000
import sqlalchemy
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlmodel import SQLModel
from app.utils.logging_util import logger
from app.utils.config import settings
from fastapi import Depends

# Set this base for models
Base = declarative_base()

# Load from env or settings (if you prefer settings.DB_USER, etc.)

ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

# Initialize Cloud SQL connector
connector = Connector()

# Define connection creator using pg8000
def getconn() -> pg8000.dbapi.Connection:
    conn: pg8000.dbapi.Connection = connector.connect(
        settings.INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=settings.DB_USER,
        password=settings.DB_PASS,
        db=settings.DB_NAME,
        ip_type=ip_type,
    )
    return conn

# Create sync SQLAlchemy engine with pg8000
engine = sqlalchemy.create_engine(
    "postgresql+pg8000://",
    creator=getconn,
    pool_pre_ping=True,
    echo=True  # or False in prod
)

# Create session factory (sync)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to provide DB session (sync)
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SessionDep = Annotated[SessionLocal, Depends(get_session)]

# Optional: init_db
def init_db():
    SQLModel.metadata.create_all(bind=engine)
    logger.info("Database tables created")
