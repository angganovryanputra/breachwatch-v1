
import logging
from fastapi import APIRouter, Depends, HTTPException, Body, status as http_status
from sqlalchemy.orm import Session
import uuid
from typing import List

from breachwatch.api.v1 import schemas
from breachwatch.storage import crud, models
from breachwatch.storage.database import get_db
from breachwatch.core.security import verify_password, get_password_hash
# from breachwatch.api.v1.dependencies import get_current_active_user # TODO: Implement proper authentication

logger = logging.getLogger(__name__)
router = APIRouter()

# --- User Management Endpoints (typically admin-only) ---

# TODO: Add dependency injection for current_user and role checks (admin required for these)

@router.get("", response_model=List[schemas.UserSchema])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_active_user) # Use later
):
    """
    Retrieve users. Requires admin privileges.
    """
    # TODO: Check if current_user is admin
    logger.info(f"Fetching users list: skip={skip}, limit={limit}")
    users = crud.get_users(db=db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.UserSchema)
async def read_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_active_user) # Use later
):
    """
    Retrieve a specific user by ID. Requires admin privileges or user fetching their own data.
    """
    # TODO: Check permissions (is admin or is current_user fetching self)
    logger.info(f"Fetching user ID: {user_id}")
    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.put("/{user_id}/status", response_model=schemas.UserSchema)
async def update_user_status_endpoint(
    user_id: uuid.UUID,
    status_update: schemas.UserStatusUpdateSchema,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_active_user) # Use later
):
    """
    Update a user's active status. Requires admin privileges.
    """
    # TODO: Check if current_user is admin
    logger.info(f"Updating status for user ID: {user_id} to is_active={status_update.is_active}")
    updated_user = crud.update_user_status(db=db, user_id=user_id, is_active=status_update.is_active)
    if updated_user is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    logger.info(f"Status updated successfully for user ID: {user_id}")
    return updated_user
    
@router.put("/{user_id}/role", response_model=schemas.UserSchema)
async def update_user_role_endpoint(
    user_id: uuid.UUID,
    role_update: schemas.UserRoleUpdateSchema,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_active_user) # Use later
):
    """
    Update a user's role. Requires admin privileges.
    """
    # TODO: Check if current_user is admin
    # TODO: Add validation for valid roles
    logger.info(f"Updating role for user ID: {user_id} to role={role_update.role}")
    updated_user = crud.update_user_role(db=db, user_id=user_id, role=role_update.role)
    if updated_user is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    logger.info(f"Role updated successfully for user ID: {user_id}")
    return updated_user


@router.delete("/{user_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: uuid.UUID,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_active_user) # Use later
):
    """
    Delete a user. Requires admin privileges.
    """
    # TODO: Check if current_user is admin
    # TODO: Prevent admin from deleting themselves?
    logger.info(f"Attempting to delete user ID: {user_id}")
    deleted_user = crud.delete_user_by_id(db=db, user_id=user_id)
    if deleted_user is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    logger.info(f"User deleted successfully: ID {user_id}")
    return None # No content on successful deletion


# --- Password Change Endpoint (for logged-in user) ---

@router.put("/{user_id}/password", response_model=schemas.MessageResponseSchema)
async def change_user_password(
    user_id: uuid.UUID, # In real app, get user_id from token
    password_data: schemas.PasswordChangeSchema,
    db: Session = Depends(get_db)
    # current_user: models.User = Depends(get_current_active_user) # Use later
):
    """
    Allows a user to change their own password.
    Requires the user to be authenticated and provide their current password.
    """
    # TODO: Get current_user from auth dependency instead of path user_id
    # TODO: Ensure current_user.id == user_id
    
    logger.info(f"Attempting password change for user ID: {user_id}")
    
    db_user = crud.get_user(db=db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")

    # Verify current password
    if not verify_password(password_data.current_password, db_user.hashed_password):
        logger.warning(f"Password change failed for user {user_id}: Incorrect current password.")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")

    # Hash the new password
    hashed_new_password = get_password_hash(password_data.new_password)
    
    # Update the password in the database
    updated_user = crud.update_user_password(db=db, user_id=user_id, hashed_password=hashed_new_password)
    
    if not updated_user:
         # This shouldn't happen if user was found earlier, but handle defensively
        logger.error(f"Failed to update password for user {user_id} after verification.")
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update password")

    logger.info(f"Password successfully changed for user ID: {user_id}")
    return schemas.MessageResponseSchema(message="Password updated successfully")

