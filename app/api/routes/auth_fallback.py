"""
Temporary fallback authentication for PSS Knowledge Assist
This provides basic login functionality without requiring PostgreSQL
"""

from fastapi import APIRouter, HTTPException, status, Response
from datetime import datetime, timedelta
import logging
import uuid
import secrets

from ...models.schemas import LoginRequest, LoginResponse
from ...auth.password_utils import verify_password, hash_password

logger = logging.getLogger(__name__)

# Temporary in-memory user store (for testing without database)
TEMP_USERS = {
    "admin@pss-knowledge-assist.com": {
        "id": "admin-user-id",
        "email": "admin@pss-knowledge-assist.com",
        "username": "PSS Admin",
        "password_hash": hash_password("admin123"),
        "is_active": True,
        "created_at": datetime.now().isoformat()
    },
    "test@pss-knowledge-assist.com": {
        "id": "test-user-id", 
        "email": "test@pss-knowledge-assist.com",
        "username": "Test User",
        "password_hash": hash_password("test123"),
        "is_active": True,
        "created_at": datetime.now().isoformat()
    },
    "demo@pss-knowledge-assist.com": {
        "id": "demo-user-id",
        "email": "demo@pss-knowledge-assist.com", 
        "username": "Demo User",
        "password_hash": hash_password("demo123"),
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
}

# Temporary session store
TEMP_SESSIONS = {}

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login_fallback(
    login_data: LoginRequest,
    response: Response
):
    """
    Temporary fallback login endpoint that works without database
    """
    try:
        logger.info(f"🔐 Fallback login attempt for: {login_data.email}")
        
        # Check if user exists
        if login_data.email not in TEMP_USERS:
            logger.warning(f"❌ User not found: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user_data = TEMP_USERS[login_data.email]
        
        # Verify password
        if not verify_password(login_data.password, user_data["password_hash"]):
            logger.warning(f"❌ Invalid password for: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user_data["is_active"]:
            logger.warning(f"❌ Inactive user: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        session_expires = datetime.now() + timedelta(hours=8)
        
        # Store session
        TEMP_SESSIONS[session_token] = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "expires_at": session_expires,
            "created_at": datetime.now()
        }
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            expires=session_expires,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        logger.info(f"✅ Fallback login successful for: {login_data.email}")
        
        return LoginResponse(
            success=True,
            message="Login successful",
            user={
                "id": user_data["id"],
                "email": user_data["email"],
                "username": user_data["username"],
                "is_active": user_data["is_active"],
                "created_at": user_data["created_at"]
            },
            session_token=session_token,
            session_duration=28800  # 8 hours in seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Fallback login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout")
async def logout_fallback(
    response: Response,
    session_token: str = None
):
    """
    Temporary fallback logout endpoint
    """
    try:
        # Remove session cookie
        response.delete_cookie(
            key="session_token",
            httponly=True,
            secure=False,
            samesite="lax"
        )
        
        # Remove from session store if exists
        if session_token and session_token in TEMP_SESSIONS:
            del TEMP_SESSIONS[session_token]
        
        logger.info("✅ Fallback logout successful")
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"❌ Fallback logout error: {e}")
        return {"success": True, "message": "Logged out"}  # Always succeed for logout
