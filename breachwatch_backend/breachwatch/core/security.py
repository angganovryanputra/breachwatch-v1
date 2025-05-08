
import logging
from passlib.context import CryptContext # type: ignore

logger = logging.getLogger(__name__)

# Setup password hashing context
# Using bcrypt as the default hashing algorithm
# Deprecated algorithms can be listed for verification but not for new hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a stored hash.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Hashes a plain password using the configured context (bcrypt).
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        # In a real application, handle this failure appropriately.
        # Re-raising might be suitable depending on the context.
        raise ValueError("Could not hash password") from e

# Example usage (for testing)
if __name__ == "__main__":
    plain_pass = "mysecretpassword"
    hashed_pass = get_password_hash(plain_pass)
    print(f"Plain Password: {plain_pass}")
    print(f"Hashed Password: {hashed_pass}")
    
    is_valid = verify_password(plain_pass, hashed_pass)
    print(f"Verification with correct password: {is_valid}")
    
    is_invalid = verify_password("wrongpassword", hashed_pass)
    print(f"Verification with incorrect password: {is_invalid}")

    # Example showing hash structure (bcrypt includes salt and cost factor)
    print(f"Is hash a bcrypt hash? {pwd_context.identify(hashed_pass)}")

