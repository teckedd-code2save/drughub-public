import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from google.cloud.sql.connector import Connector


# initialize Cloud SQL Python Connector
connector = Connector()

# create connection pool engine
engine = sqlalchemy.create_engine(
    "postgresql+asyncpg://",
    creator=lambda: connector.connect(
       "serendepify:us-central1:drughubdb", # Cloud SQL Instance Connection Name
       "asyncpg",
        user="postgres",
        password="drughubdb001122",
        db="drughubdb",
        ip_type="public"  # "private" for private IP
    ),
)

# create SQLAlchemy ORM session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

  