from fastapi import APIRouter

from .endpoints import crawl, preferences, users # Import users endpoint

api_router = APIRouter()

api_router.include_router(crawl.router, prefix="/crawl", tags=["crawl"])
api_router.include_router(preferences.router, prefix="/users", tags=["preferences"]) # Keep preferences under /users path for now
api_router.include_router(users.router, prefix="/users", tags=["users"]) # Add user management router

# Add more routers as your API grows
