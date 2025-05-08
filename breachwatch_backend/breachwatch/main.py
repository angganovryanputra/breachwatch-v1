
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from breachwatch.api.v1 import api_router as api_router_v1
from breachwatch.storage.database import engine, Base
from breachwatch.utils.config_loader import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create database tables if they don't exist
# In a production environment, you would use Alembic migrations.
# Base.metadata.create_all(bind=engine) # Commented out: Tables should be created by models importing Base and being loaded.
                                      # This will be implicitly handled if models are imported somewhere.
                                      # For explicit creation, we can do it here or in a startup event.

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS (Cross-Origin Resource Sharing)
# Adjust origins as necessary for your frontend.
# Using ["*"] for development is convenient but less secure.
# For production, replace "*" with the actual frontend URL(s).
origins = [
    "http://localhost:9002",  # Assuming Next.js frontend runs on port 9002
    "http://127.0.0.1:9002",
    # "*" # Allow all origins - USE WITH CAUTION, preferred for local dev troubleshooting
    # Add other origins if needed (e.g., production frontend URL)
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins, # Use specific origins for better security
    allow_origins=["*"], # More permissive for local development troubleshooting
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup...")
    logger.info("Creating database tables if they don't exist (for development).")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables checked/created.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    # You can add other startup logic here, like connecting to external services.

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown...")
    # Add cleanup logic here if needed.

# Include API routers
app.include_router(api_router_v1, prefix=settings.API_V1_STR)

@app.get("/", summary="Health check endpoint")
async def root():
    """
    A simple health check endpoint.
    """
    # Basic check to see if DB connection is working at a high level
    db_status = "ok"
    try:
        # Try to get a session and perform a simple query
        from breachwatch.storage.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"

    return {"message": f"{settings.APP_NAME} is running!", "database_status": db_status}

if __name__ == "__main__":
    import uvicorn
    # This is for direct execution (e.g., debugging).
    # For production, use a process manager like Gunicorn with Uvicorn workers.
    # Use reload=True only for development.
    uvicorn.run("breachwatch.main:app", host="0.0.0.0", port=8000, reload=True)

