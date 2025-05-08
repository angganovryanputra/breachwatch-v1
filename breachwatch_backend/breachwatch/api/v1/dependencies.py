
# breachwatch/api/v1/dependencies.py
import logging
from fastapi import Depends, HTTPException, status as http_status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt # type: ignore
import uuid

from breachwatch.storage import crud, models
from breachwatch.storage.database import get_db
from breachwatch.utils.config_loader import get_settings
from breachwatch.api.v1 import schemas # For TokenDataSchema

logger = logging.getLogger(__name__)
settings = get_settings()

# Define the OAuth2 scheme. tokenUrl should point to your login endpoint.
# This tells Swagger UI where to get the token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Dependency to get the current user from the JWT token.
    Verifies the token and fetches the user from the database.
    """
    credentials_exception = HTTPException(
        status_code=http_status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY, # Use the secret key from settings
            algorithms=[settings.ALGORITHM] # Use the algorithm from settings
        )
        # Pydantic V2 uses model_validate
        token_data = schemas.TokenDataSchema.model_validate(payload)

        if token_data.user_id is None:
            logger.warning("User ID not found in JWT token payload.")
            raise credentials_exception
        
        user_id = uuid.UUID(str(token_data.user_id)) # Convert string back to UUID

    except JWTError as e:
        logger.error(f"JWT Error during token decoding: {e}")
        raise credentials_exception
    except ValueError: # Handle potential UUID conversion error
         logger.error(f"Invalid UUID format in token: {token_data.user_id}")
         raise credentials_exception
    except Exception as e: # Catch other potential validation errors from Pydantic
        logger.error(f"Error validating token data: {e}")
        raise credentials_exception


    user = crud.get_user(db, user_id=user_id)
    if user is None:
        logger.warning(f"User with ID {user_id} from token not found in DB.")
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Dependency that ensures the user obtained from the token is active.
    """
    if not current_user.is_active:
        logger.warning(f"User {current_user.email} is inactive. Access denied.")
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def require_admin_user(
    current_user: models.User = Depends(get_current_active_user)
) -> models.User:
    """
    Dependency that ensures the current user is an active admin.
    """
    if current_user.role != "admin":
        logger.warning(f"User {current_user.email} (role: {current_user.role}) attempted admin-only action.")
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Administrator privileges required."
        )
    return current_user
