
import logging
from passlib.context import CryptContext # type: ignore
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt, JWTError # type: ignore

from breachwatch.utils.config_loader import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Setup password hashing context
# Using bcrypt as the default hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Password Hashing ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a stored hash.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verifying password hash: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Hashes a plain password using the configured context (bcrypt).
    """
    if not password:
         raise ValueError("Password cannot be empty")
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise ValueError("Could not hash password") from e

# --- JWT Token Handling ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default expiration time (e.g., 15 minutes)
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)}) # Add expiration and issued_at claims

    if not settings.SECRET_KEY:
        logger.critical("SECRET_KEY is not set in configuration. Cannot create JWT token.")
        raise ValueError("JWT Secret Key is not configured.")
    if not settings.ALGORITHM:
         logger.critical("JWT ALGORITHM is not set in configuration. Cannot create JWT token.")
         raise ValueError("JWT Algorithm is not configured.")

    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error encoding JWT token: {e}")
        raise ValueError("Could not create access token") from e


# Example usage (for testing)
if __name__ == "__main__":
    # Password Hashing Test
    plain_pass = "mysecretpassword"
    hashed_pass = get_password_hash(plain_pass)
    print(f"Plain Password: {plain_pass}")
    print(f"Hashed Password: {hashed_pass}")

    is_valid = verify_password(plain_pass, hashed_pass)
    print(f"Verification with correct password: {is_valid}")

    is_invalid = verify_password("wrongpassword", hashed_pass)
    print(f"Verification with incorrect password: {is_invalid}")

    print(f"Is hash a bcrypt hash? {pwd_context.identify(hashed_pass)}")

    # JWT Token Test
    # Ensure SECRET_KEY and ALGORITHM are set in your .env for this to work
    if settings.SECRET_KEY and settings.ALGORITHM:
        print("\n--- JWT Test ---")
        user_data = {"user_id": "test_user_123", "role": "admin"}
        token_delta = timedelta(minutes=15)
        try:
            access_token = create_access_token(data=user_data, expires_delta=token_delta)
            print(f"Generated Access Token: {access_token[:30]}...") # Print start of token

            # Simulate decoding (requires the same key and algorithm)
            try:
                decoded_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                print(f"Decoded Payload: {decoded_payload}")
            except JWTError as jwt_err:
                print(f"Error decoding token: {jwt_err}")
        except ValueError as e:
             print(f"Could not generate token: {e}")

    else:
        print("\nSkipping JWT test: SECRET_KEY or ALGORITHM not configured in settings.")
