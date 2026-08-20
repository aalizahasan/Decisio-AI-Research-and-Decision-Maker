import logging
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger("db")

Base = declarative_base()

# Attempt to connect to PostgreSQL database or fallback to SQLite
DATABASE_URL = settings.DATABASE_URL
engine = None

if "postgresql" in DATABASE_URL:
    try:
        temp_engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
        with temp_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        engine = temp_engine
        logger.info("Successfully connected to PostgreSQL database.")
    except Exception as e:
        logger.warning(f"PostgreSQL connection unavailable ({e}). Falling back to local SQLite database.")

if not engine:
    is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("LAMBDA_TASK_ROOT") or not os.access(".", os.W_OK))
    sqlite_path = "/tmp/sqlite_rag.db" if is_serverless else "./sqlite_rag.db"
    sqlite_url = f"sqlite:///{sqlite_path}"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency yielding a database session.
    Ensures sessions are closed after requests complete.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initializes database tables and enables pgvector extension if using PostgreSQL.
    """
    try:
        import app.db.models  # Register SQLAlchemy ORM models with Base.metadata

        if "postgresql" in str(engine.url):
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized successfully using engine: {engine.url}")
    except Exception as err:
        logger.error(f"Error during database initialization: {err}")

