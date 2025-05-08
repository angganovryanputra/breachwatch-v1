
import logging
from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
import sys # To check for testing environment
from slowapi import Limiter, _rate_limit_exceeded_handler # For Rate Limiting
from slowapi.util import get_remote_address # For Rate Limiting by IP
from slowapi.errors import RateLimitExceeded # For Rate Limiting

from breachwatch.api.v1 import api_router as api_router_v1
from breachwatch.storage.database import engine, Base, SessionLocal # Import SessionLocal for DB check
from breachwatch.utils.config_loader import get_settings
from breachwatch import models # Ensure models are imported so Base knows about them
from breachwatch.api.v1.endpoints import auth # Import auth for testing endpoint

logger = logging.getLogger(__name__)
settings = get_settings()

# --- Rate Limiting Setup ---
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"]) # Example: 100 requests per minute per IP

# --- FastAPI App Initialization ---
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add SlowAPI Rate Limiter State and Exception Handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- Security Headers Middleware ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY" # Or "SAMEORIGIN" if needed
    # Content-Security-Policy is complex and application-specific.
    # Start with a basic one, but this likely needs tuning.
    # response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; object-src 'none';"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Strict-Transport-Security (HSTS) - uncomment ONLY if served over HTTPS and you understand the implications.
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# --- CORS Middleware ---
# Adjust origins as necessary for your frontend.
# Using ["*"] for development is convenient but less secure.
# For production, replace "*" with the actual frontend URL(s).
if settings.ENVIRONMENT == "production":
     origins = [
        # Add your production frontend URL here
        # e.g., "https://breachwatch.yourdomain.com"
     ]
     logger.info(f"CORS configured for Production environment. Allowed origins: {origins}")
else:
     # More permissive for development/local testing
     origins = [
        "http://localhost:9002", # Default Next.js frontend port
        "http://127.0.0.1:9002",
        # You might need to add other local development origins if applicable
     ]
     # Optionally allow all for easy local dev, BUT USE WITH CAUTION
     origins.append("*") # Allow all origins for simplified local development
     logger.warning("CORS allows all origins ('*'). Ensure this is restricted in production.")


# Add CORS Middleware *after* Security Headers and Rate Limiter middleware if order matters
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Use the configured origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all standard methods
    allow_headers=["*"], # Allows all headers, consider restricting in production if needed
)

# Apply the rate limiter to all requests
app.middleware('http')(limiter.limit())

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup...")
    # Avoid creating tables during testing if using a separate test DB setup
    if "pytest" not in sys.modules:
        logger.info("Creating database tables if they don't exist (for development/production).")
        try:
            # Ensure all models are imported before calling create_all
            # Importing breachwatch.models usually does this implicitly if they subclass Base
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables checked/created.")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}", exc_info=True)
            # Depending on the severity, you might want to prevent startup
            # raise RuntimeError("Failed to initialize database tables.") from e
    else:
        logger.info("Skipping table creation during testing.")

    # You can add other startup logic here, like connecting to external services.

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown...")
    # Add cleanup logic here if needed.

# Include API routers
app.include_router(api_router_v1, prefix=settings.API_V1_STR)

@app.get("/", summary="Health check endpoint", tags=["Health"])
async def root():
    """
    A simple health check endpoint. Checks basic API availability and DB connection.
    """
    db_status = "unknown"
    db_error = None
    try:
        # Try to get a session and perform a simple query
        db = SessionLocal()
        db.execute("SELECT 1") # Use text() for SQLAlchemy 2.0 or ensure Core execution context
        db.close()
        db_status = "ok"
        logger.debug("Database health check successful.")
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=False) # Log less verbosely for health check
        db_status = "error"
        db_error = str(e)

    return {
        "message": f"{settings.APP_NAME} API is running!",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database_status": db_status,
        "database_error": db_error if db_error else None # Include error details if present
    }

# Add a simple endpoint to test authentication dependency
@app.get("/api/v1/secure-ping", summary="Test Authentication", tags=["Health"])
async def secure_ping(current_user: models.User = Depends(auth.get_current_active_user)):
    """
    An endpoint that requires authentication to access. Useful for testing tokens.
    """
    return {"message": "Pong!", "user_email": current_user.email, "user_role": current_user.role}


if __name__ == "__main__":
    import uvicorn
    # This is for direct execution (e.g., debugging).
    # For production, use a process manager like Gunicorn with Uvicorn workers.
    # Use reload=True only for development.
    uvicorn.run(
         "breachwatch.main:app",
         host="0.0.0.0",
         port=8000,
         reload=settings.ENVIRONMENT == "development", # Enable reload only in development
         log_level=settings.LOG_LEVEL.lower() # Sync uvicorn log level
     )

