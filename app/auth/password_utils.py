"""
Password hashing and verification utilities using bcrypt
Provides secure password handling for user authentication
"""

from passlib.context import CryptContext
import re
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Create password context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password strength requirements
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 255

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string suitable for database storage
        
    Raises:
        ValueError: If password is invalid
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must be no more than {MAX_PASSWORD_LENGTH} characters long")
    
    try:
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise ValueError("Failed to hash password")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    if not plain_password or not hashed_password:
        return False
    
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"Password verification result: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False


def validate_password_strength(password: str) -> Tuple[bool, list[str]]:
    """
    Validate password strength according to security requirements
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Length check
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    
    if len(password) > MAX_PASSWORD_LENGTH:
        errors.append(f"Password must be no more than {MAX_PASSWORD_LENGTH} characters long")
    
    # Character requirements
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character")
    
    # Common password patterns to avoid
    common_patterns = [
        r"123456",
        r"password",
        r"qwerty",
        r"abc123",
        r"admin"
    ]
    
    password_lower = password.lower()
    for pattern in common_patterns:
        if pattern in password_lower:
            errors.append("Password contains common patterns that are not secure")
            break
    
    is_valid = len(errors) == 0
    return is_valid, errors


def needs_password_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be updated (e.g., due to changed hashing parameters)
    
    Args:
        hashed_password: Stored password hash
        
    Returns:
        True if hash should be updated, False otherwise
    """
    try:
        return pwd_context.needs_update(hashed_password)
    except Exception as e:
        logger.error(f"Error checking password rehash status: {e}")
        return False


def generate_password_reset_token() -> str:
    """
    Generate a secure random token for password reset
    
    Returns:
        Random token string suitable for password reset
    """
    import secrets
    import string
    
    # Generate a 32-character random token
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    logger.debug("Password reset token generated")
    return token


# Password strength meter for frontend
def get_password_strength_score(password: str) -> dict:
    """
    Get a password strength score for frontend display
    
    Args:
        password: Password to score
        
    Returns:
        Dictionary with score (0-100) and feedback
    """
    score = 0
    feedback = []
    
    # Length scoring
    if len(password) >= MIN_PASSWORD_LENGTH:
        score += 20
    else:
        feedback.append(f"Add {MIN_PASSWORD_LENGTH - len(password)} more characters")
    
    # Character variety scoring
    if re.search(r"[a-z]", password):
        score += 15
    else:
        feedback.append("Add lowercase letters")
    
    if re.search(r"[A-Z]", password):
        score += 15
    else:
        feedback.append("Add uppercase letters")
    
    if re.search(r"\d", password):
        score += 15
    else:
        feedback.append("Add numbers")
    
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 15
    else:
        feedback.append("Add special characters")
    
    # Length bonus
    if len(password) >= 12:
        score += 10
        
    if len(password) >= 16:
        score += 10
    
    # Determine strength level
    if score >= 85:
        strength = "Very Strong"
    elif score >= 70:
        strength = "Strong"
    elif score >= 50:
        strength = "Medium"
    elif score >= 30:
        strength = "Weak"
    else:
        strength = "Very Weak"
    
    return {
        "score": min(score, 100),
        "strength": strength,
        "feedback": feedback
    }
