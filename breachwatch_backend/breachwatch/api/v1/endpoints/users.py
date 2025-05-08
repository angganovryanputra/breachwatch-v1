
import logging
from fastapi import APIRouter, Depends, HTTPException, Body, status as http_status
from sqlalchemy.orm import Session
import uuid
from typing import List
from fastapi_cache.decorator import cache # Import cache decorator

from breachwatch.api.v1 import schemas
from breachwatch.storage import crud, models
from breachwatch.storage.database import get_db
from breachwatch.core.security import verify_password, get_password_hash
from breachwatch.api.v1.dependencies import get_current_active_user, require_admin_user # Import authentication dependencies

logger = logging.getLogger(__name__)
router = APIRouter()

# --- User Management Endpoints (Admin Required) ---

@router.get("", response_model=List[schemas.UserSchema], dependencies=[Depends(require_admin_user)])
@cache(expire=300) # Cache user list for 5 minutes
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
    # current_admin_user: models.User = Depends(require_admin_user) # Can optionally inject admin user if needed
):
    """
    Retrieve users. Requires admin privileges.
    """
    logger.info(f"Admin action: Fetching users list: skip={skip}, limit={limit}")
    users = crud.get_users(db=db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.UserSchema], dependencies=[Depends(require_admin_user)])
@cache(expire=300) # Cache individual user for 5 minutes
async def read_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db)
    # current_admin_user: models.User = Depends(require_admin_user) # Can optionally inject admin user
):
    """
    Retrieve a specific user by ID. Requires admin privileges.
    (Users can get their own details via /auth/me)
    """
    logger.info(f"Admin action: Fetching user ID: {user_id}")
    db_user = crud.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.put("/{user_id}/status", response_model=schemas.UserSchema, dependencies=[Depends(require_admin_user)])
async def update_user_status_endpoint(
    user_id: uuid.UUID,
    status_update: schemas.UserStatusUpdateSchema,
    db: Session = Depends(get_db),
    current_admin_user: models.User = Depends(require_admin_user) # Ensure admin is performing action
):
    """
    Update a user's active status. Requires admin privileges.
    Prevents admin from deactivating themselves.
    """
    if user_id == current_admin_user.id and not status_update.is_active:
         logger.warning(f"Admin user {current_admin_user.email} attempted to deactivate their own account.")
         raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Administrators cannot deactivate their own account.")

    logger.info(f"Admin action: Updating status for user ID: {user_id} to is_active={status_update.is_active}")
    updated_user = crud.update_user_status(db=db, user_id=user_id, is_active=status_update.is_active)
    if updated_user is None:
        db.rollback() # Ensure rollback if update failed
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found or update failed")
    # Commit the change after successful update in crud
    db.commit()
    # Invalidate cache for this user and the user list
    from fastapi_cache import FastAPICache
    await FastAPICache.clear(namespace=f"UserSchema:{user_id}")
    await FastAPICache.clear(namespace="read_users") # Invalidate entire list cache
    logger.info(f"Status updated successfully for user ID: {user_id}")
    return updated_user

@router.put("/{user_id}/role", response_model=schemas.UserSchema, dependencies=[Depends(require_admin_user)])
async def update_user_role_endpoint(
    user_id: uuid.UUID,
    role_update: schemas.UserRoleUpdateSchema,
    db: Session = Depends(get_db),
    current_admin_user: models.User = Depends(require_admin_user) # Ensure admin is performing action
):
    """
    Update a user's role. Requires admin privileges.
    Prevents admin from removing their own admin role.
    """
    if user_id == current_admin_user.id and role_update.role != "admin":
         logger.warning(f"Admin user {current_admin_user.email} attempted to remove their own admin role.")
         raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Administrators cannot remove their own admin role.")

    logger.info(f"Admin action: Updating role for user ID: {user_id} to role={role_update.role}")
    updated_user = crud.update_user_role(db=db, user_id=user_id, role=role_update.role)
    if updated_user is None:
        db.rollback()
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found or update failed")
    db.commit()
    # Invalidate cache
    from fastapi_cache import FastAPICache
    await FastAPICache.clear(namespace=f"UserSchema:{user_id}")
    await FastAPICache.clear(namespace="read_users")
    logger.info(f"Role updated successfully for user ID: {user_id}")
    return updated_user


@router.delete("/{user_id}", status_code=http_status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_user)])
async def delete_user_endpoint(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin_user: models.User = Depends(require_admin_user) # Ensure admin is performing action
):
    """
    Delete a user. Requires admin privileges.
    Prevents admin from deleting themselves.
    """
    if user_id == current_admin_user.id:
        logger.warning(f"Admin user {current_admin_user.email} attempted to delete their own account.")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Administrators cannot delete their own account.")

    logger.info(f"Admin action: Attempting to delete user ID: {user_id}")
    deleted_user = crud.delete_user_by_id(db=db, user_id=user_id)
    if deleted_user is None:
        db.rollback()
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found or deletion failed")
    db.commit()
    # Invalidate cache
    from fastapi_cache import FastAPICache
    await FastAPICache.clear(namespace=f"UserSchema:{user_id}")
    await FastAPICache.clear(namespace="read_users")
    logger.info(f"User deleted successfully: ID {user_id}")
    return None # No content on successful deletion


# --- Password Change Endpoint (for logged-in user) ---

@router.put("/me/password", response_model=schemas.MessageResponseSchema)
async def change_current_user_password(
    password_data: schemas.PasswordChangeSchema,
    current_user: models.User = Depends(get_current_active_user), # Get user from token
    db: Session = Depends(get_db)
):
    """
    Allows the currently authenticated user to change their own password.
    Requires the user to provide their current password correctly.
    """
    user_id = current_user.id
    logger.info(f"Attempting password change for current user ID: {user_id}")

    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        logger.warning(f"Password change failed for user {user_id}: Incorrect current password.")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")

    # Check if new password is the same as the old one (optional, but good practice)
    if verify_password(password_data.new_password, current_user.hashed_password):
        logger.warning(f"Password change failed for user {user_id}: New password cannot be the same as the old password.")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="New password cannot be the same as the current password.")


    # Hash the new password
    hashed_new_password = get_password_hash(password_data.new_password)

    # Update the password in the database
    updated_user = crud.update_user_password(db=db, user_id=user_id, hashed_password=hashed_new_password)

    if not updated_user:
         # This shouldn't happen if user was found earlier, but handle defensively
        db.rollback()
        logger.error(f"Failed to update password for user {user_id} after verification.")
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update password")

    db.commit()
    # Optionally invalidate user cache if password change should affect cached user data (unlikely for basic reads)
    # from fastapi_cache import FastAPICache
    # await FastAPICache.clear(namespace=f"UserSchema:{user_id}")
    logger.info(f"Password successfully changed for user ID: {user_id}")
    return schemas.MessageResponseSchema(message="Password updated successfully")

# --- User Preferences Endpoints (for logged-in user) ---

@router.get("/me/preferences", response_model=schemas.UserPreferenceSchema)
@cache(namespace="UserPreferenceSchema", expire=300) # Cache preferences for 5 minutes, namespace by user? (Needs custom key builder)
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
            db.rollback()
            logger.error(f"Failed to create default preferences for user {user_id}")
            raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve or create preferences")
        db.commit() # Commit the newly created preferences

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
        db.rollback()
        logger.error(f"Failed to update or create preferences for user ID: {user_id}")
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save preferences")

    db.commit() # Commit the update/creation
    # Invalidate cache for this user's preferences
    from fastapi_cache import FastAPICache
    await FastAPICache.clear(namespace="UserPreferenceSchema") # Clear entire namespace or use specific key if possible
    logger.info(f"Preferences successfully updated for user ID: {user_id}")
    return db_preferences
