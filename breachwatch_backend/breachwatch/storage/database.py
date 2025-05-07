import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from breachwatch.utils.config_loader import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

DATABASE_URL = settings.DATABASE_URL
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set. Cannot connect to PostgreSQL.")
    raise ValueError("DATABASE_URL not set. Please configure it in your .env file or environment.")

logger.info(f"Database URL: {DATABASE_URL.replace(settings.DB_PASSWORD, '********') if settings.DB_PASSWORD else DATABASE_URL}")


try:
    engine = create_engine(DATABASE_URL) # Add pool_pre_ping=True for production robustness
except ImportError: # Handle case where psycopg2 might not be installed, though it's in requirements.txt
    logger.error("psycopg2-binary is not installed. Please install it: pip install psycopg2-binary")
    raise
except Exception as e:
    logger.error(f"Error creating database engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session in FastAPI routes
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to test DB connection (optional)
def test_db_connection():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        logger.info("Database connection successful.")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
    finally:
        if db:
            db.close()

# if __name__ == "__main__":
#     test_db_connection()
#     # You could also add Base.metadata.create_all(engine) here for quick table creation during dev
#     # but Alembic is preferred for production.
#     logger.info("Attempting to create tables (if not exists) for models imported so far.")
#     # Import models here to ensure they are registered with Base before create_all
#     # from . import models # This would trigger model loading
#     # Base.metadata.create_all(bind=engine)
#     # logger.info("Tables creation attempt finished.")
