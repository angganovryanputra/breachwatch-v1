from fastapi import APIRouter

from .endpoints import crawl, preferences # Import preferences endpoint
# Import other endpoint modules here
# from .endpoints import settings
# from .endpoints import results

api_router = APIRouter()

api_router.include_router(crawl.router, prefix="/crawl", tags=["crawl"])
api_router.include_router(preferences.router, prefix="/users", tags=["users", "preferences"]) # Add preferences router
# api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
# api_router.include_router(results.router, prefix="/results", tags=["results"])

# Add more routers as your API grows
