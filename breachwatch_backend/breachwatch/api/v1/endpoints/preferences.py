
import logging
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session
import uuid

from breachwatch.api.v1 import schemas
from breachwatch.storage import crud, models # Import crud and models
from breachwatch.storage.database import get_db
from breachwatch.api.v1.dependencies import get_current_active_user # Import authentication dependency

logger = logging.getLogger(__name__)
router = APIRouter()

# Path prefix /users is defined in api/v1/__init__.py

@router.get("/me/preferences", response_model=schemas.UserPreferenceSchema)
async def read_current_user_preferences(
    current_user: models.User = Depends(get_current_active_user), # Inject authenticated user
    db: Session = Depends(get_db)
):
    """
    Retrieve preferences for the currently authenticated user.
    """
    user_id = current_user.id
    logger.info(f"Fetching preferences for current user ID: {user_id}")
    db_preferences = crud.get_user_preferences(db=db, user_id=user_id)
    if db_preferences is None:
        logger.warning(f"Preferences not found for user ID: {user_id}. Creating default preferences.")
        # If preferences don't exist, create and return defaults
        default_prefs_schema = schemas.UserPreferenceUpdateSchema() # Gets defaults
        db_preferences = crud.update_or_create_user_preferences(
             db=db, 
             user_id=user_id, 
             preferences_in=default_prefs_schema
        )
        if not db_preferences: # Handle potential error during default creation
            logger.error(f"Failed to create default preferences for user {user_id}")
            raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve or create preferences")

    return db_preferences


@router.put("/me/preferences", response_model=schemas.UserPreferenceSchema)
async def update_current_user_preferences(
    preferences_in: schemas.UserPreferenceUpdateSchema,
    current_user: models.User = Depends(get_current_active_user), # Inject authenticated user
    db: Session = Depends(get_db)
):
    """
    Update preferences for the currently authenticated user.
    Creates preferences if they don't exist.
    """
    user_id = current_user.id
    logger.info(f"Updating preferences for current user ID: {user_id}")

    # User existence is guaranteed by get_current_active_user dependency

    db_preferences = crud.update_or_create_user_preferences(
        db=db,
        user_id=user_id,
        preferences_in=preferences_in
    )

    if db_preferences is None: # Should not happen if user exists, but defensive check
        logger.error(f"Failed to update or create preferences for user ID: {user_id}")
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save preferences")

    logger.info(f"Preferences successfully updated for user ID: {user_id}")
    return db_preferences
