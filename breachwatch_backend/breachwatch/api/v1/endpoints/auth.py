
# breachwatch/api/v1/endpoints/auth.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from fastapi.security import OAuth2PasswordRequestForm # For standard login form
from sqlalchemy.orm import Session
from datetime import timedelta

from breachwatch.api.v1 import schemas
from breachwatch.storage import crud, models
from breachwatch.storage.database import get_db
from breachwatch.core import security
from breachwatch.utils.config_loader import get_settings
from breachwatch.core.security import create_access_token
from breachwatch.api.v1.dependencies import get_current_active_user # For /me endpoint

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

@router.post("/login", response_model=schemas.TokenSchema)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Logs in a user using email (as username) and password.
    Returns an access token upon successful authentication.
    """
    logger.info(f"Login attempt for user: {form_data.username}") # username field from form holds email
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        logger.warning(f"Authentication failed for user: {form_data.username}")
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
         logger.warning(f"Login attempt failed for inactive user: {form_data.username}")
         raise HTTPException(
             status_code=http_status.HTTP_400_BAD_REQUEST,
             detail="Inactive user account."
         )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": str(user.id), "role": user.role}, # Include necessary info in token
        expires_delta=access_token_expires
    )
    logger.info(f"User {user.email} logged in successfully.")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.UserSchema, status_code=http_status.HTTP_201_CREATED)
async def register_new_user(
    user_in: schemas.UserCreateSchema,
    db: Session = Depends(get_db)
):
    """
    Registers a new user.
    """
    logger.info(f"Registration attempt for email: {user_in.email}")
    db_user = crud.get_user_by_email(db, email=user_in.email)
    if db_user:
        logger.warning(f"Registration failed: Email {user_in.email} already registered.")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Ensure default role is 'user' unless explicitly set otherwise (and maybe validated)
    if user_in.role not in ["user", "admin"]: # Simple validation
        user_in.role = "user"

    created_user = crud.create_user(db=db, user_in=user_in)
    logger.info(f"User {created_user.email} registered successfully with ID {created_user.id}")
    return created_user


@router.get("/me", response_model=schemas.UserSchema)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get current logged in user details.
    """
    return current_user
