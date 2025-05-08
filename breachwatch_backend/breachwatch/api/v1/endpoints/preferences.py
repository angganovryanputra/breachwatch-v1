
import logging
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session
import uuid

from breachwatch.api.v1 import schemas
from breachwatch.storage import crud, models # Import crud and models
from breachwatch.storage.database import get_db
# from breachwatch.api.v1.dependencies import get_current_active_user # TODO: Implement authentication

logger = logging.getLogger(__name__)
router = APIRouter()

# In a real app, use authentication to get the current user
# current_user: models.User = Depends(get_current_active_user)

# For now, we'll pass user_id in the path, which is insecure without auth
# TODO: Replace user_id path parameter with dependency injection of current_user

@router.get("/{user_id}/preferences", response_model=schemas.UserPreferenceSchema)
async def read_user_preferences(
    user_id: uuid.UUID,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_active_user) # Use this later
):
    """
    Retrieve preferences for a specific user.
    Requires authentication in a real application.
    """
    # TODO: Add authorization check: if current_user.id != user_id and current_user.role != 'admin': raise HTTPException(...)
    
    logger.info(f"Fetching preferences for user ID: {user_id}")
    db_preferences = crud.get_user_preferences(db=db, user_id=user_id)
    if db_preferences is None:
        logger.warning(f"Preferences not found for user ID: {user_id}")
        # Option 1: Return 404
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User preferences not found")
        # Option 2: Return default preferences (consider security implications)
        # return schemas.UserPreferenceSchema(user_id=user_id, ...) # Create default response schema
        
    return db_preferences


@router.put("/{user_id}/preferences", response_model=schemas.UserPreferenceSchema)
async def update_user_preferences(
    user_id: uuid.UUID,
    preferences_in: schemas.UserPreferenceUpdateSchema,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_active_user) # Use this later
):
    """
    Update preferences for a specific user. Creates preferences if they don't exist.
    Requires authentication in a real application.
    """
    # TODO: Add authorization check: if current_user.id != user_id: raise HTTPException(...)
    
    logger.info(f"Updating preferences for user ID: {user_id}")
    
    # Check if user exists (optional but good practice)
    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        logger.warning(f"User not found when trying to update preferences: {user_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")

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
