
import os
from urllib.parse import quote_plus

from loguru import logger
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Database configuration from Render environment variables
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DB = os.getenv("MYSQL_DB", "neonatal_auth")

# Build the database URL safely, including passwords with special characters
DATABASE_URL = (
    f"mysql+pymysql://{quote_plus(MYSQL_USER)}:"
    f"{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:"
    f"{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
)

# Configure TLS for the hosted Aiven database
connect_args = {}

if MYSQL_HOST not in ("localhost", "127.0.0.1"):
    connect_args["ssl"] = {"check_hostname": True}

# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=5,
    pool_timeout=30,
    echo=False,
)

# Set UTF-8 character encoding on each connection
@event.listens_for(engine, "connect")
def set_charset(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SET NAMES utf8mb4")
    finally:
        cursor.close()


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Declarative base for SQLAlchemy models
class Base(DeclarativeBase):
    pass


# FastAPI database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Database connectivity check
def check_db_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Database connection successful")
        return True

    except Exception as exc:
        logger.error(f"Database connection failed: {exc}")
        return False
