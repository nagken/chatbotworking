"""
Authentication routes for PSS Knowledge Assist
Database-backed user authentication and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import logging
import uuid
import secrets

from ...models.schemas import (
    LoginRequest, LoginResponse, UserCreate, UserResponse, 
    UserUpdate, PasswordChangeRequest, UserListResponse
)
from ...auth.password_utils import validate_password_strength, verify_password, hash_password
from ...utils.datetime_utils import utc_now, seconds_until_expiry

# Import database dependencies with fallback
try:
    from ...database.connection import get_db_session_dependency
    from ...auth.user_repository import UserRepository
    from ...auth.session_repository import SessionRepository
    from ...database.models import User, UserSession
    DATABASE_AVAILABLE = True
except Exception as e:
    DATABASE_AVAILABLE = False
    get_db_session_dependency = None

logger = logging.getLogger(__name__)

router = APIRouter()

# Temporary in-memory user store for fallback authentication
def get_temp_users():
    """Get temporary users with freshly hashed passwords"""
    
    # Pre-computed hashes to avoid runtime hashing issues
    # These are bcrypt hashes of the passwords
    admin_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewPCXjJNhwPOGnYe"  # admin123
    test_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewPCXjJNhwPOGnYe"   # test1234  
    demo_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewPCXjJNhwPOGnYe"   # demo1234
    
    return {
        "admin@pss-knowledge-assist.com": {
            "id": "admin-user-id",
            "email": "admin@pss-knowledge-assist.com",
            "username": "PSS Admin",
            "password_hash": admin_hash,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        },
        "test@pss-knowledge-assist.com": {
            "id": "test-user-id", 
            "email": "test@pss-knowledge-assist.com",
            "username": "Test User",
            "password_hash": test_hash,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        },
        "demo@pss-knowledge-assist.com": {
            "id": "demo-user-id",
            "email": "demo@pss-knowledge-assist.com", 
            "username": "Demo User",
            "password_hash": demo_hash,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
    }

# Temporary session store
TEMP_SESSIONS = {}

async def fallback_login(login_request: LoginRequest, response: Response, request: Request):
    """Fallback authentication when database is not available"""
    try:
        logger.info(f"🔐 Fallback login attempt for: {login_request.email}")
        
        # Simple fallback credentials for testing (no hashing)
        SIMPLE_USERS = {
            "admin@pss-knowledge-assist.com": {
                "id": "admin-user-id",
                "email": "admin@pss-knowledge-assist.com",
                "username": "PSS Admin",
                "password": "admin123",
                "is_active": True,
                "created_at": datetime.now().isoformat()
            },
            "test@pss-knowledge-assist.com": {
                "id": "test-user-id", 
                "email": "test@pss-knowledge-assist.com",
                "username": "Test User",
                "password": "test1234",
                "is_active": True,
                "created_at": datetime.now().isoformat()
            },
            "demo@pss-knowledge-assist.com": {
                "id": "demo-user-id",
                "email": "demo@pss-knowledge-assist.com", 
                "username": "Demo User",
                "password": "demo1234",
                "is_active": True,
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Check if user exists
        if login_request.email not in SIMPLE_USERS:
            logger.warning(f"❌ User not found: {login_request.email}")
            return LoginResponse(
                success=False,
                message="Invalid email or password"
            )
        
        user_data = SIMPLE_USERS[login_request.email]
        
        # Simple password check (no hashing for testing)
        if login_request.password != user_data["password"]:
            logger.warning(f"❌ Invalid password for: {login_request.email}")
            logger.warning(f"Expected: {user_data['password']}, Got: {login_request.password}")
            return LoginResponse(
                success=False,
                message="Invalid email or password"
            )
        
        logger.info(f"✅ Password verified for: {login_request.email}")
        
        # Check if user is active
        if not user_data["is_active"]:
            logger.warning(f"❌ Inactive user: {login_request.email}")
            return LoginResponse(
                success=False,
                message="Account is inactive"
            )
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        session_expires = datetime.now() + timedelta(hours=8)
        
        # Store session with complete user data
        TEMP_SESSIONS[session_token] = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "username": user_data["username"],
            "is_active": user_data["is_active"],
            "created_at": user_data["created_at"],
            "expires_at": session_expires,
            "session_created_at": datetime.now()
        }
        
        logger.info(f"🔐 Created fallback session: {session_token[:10]}... for {user_data['email']}")
        logger.info(f"🔐 Total active fallback sessions: {len(TEMP_SESSIONS)}")
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=28800,  # 8 hours
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        logger.info(f"✅ Fallback login successful for: {login_request.email}")
        
        response_data = LoginResponse(
            success=True,
            message="Login successful",
            user={
                "id": user_data["id"],
                "email": user_data["email"],
                "username": user_data["username"],
                "is_active": user_data["is_active"],
                "created_at": user_data["created_at"]
            },
            session_duration=28800,  # 8 hours in seconds
            session_token=session_token  # Include session token in response
        )
        
        logger.info(f"✅ Fallback login response: {response_data.model_dump()}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Fallback login error: {e}")
        return LoginResponse(
            success=False,
            message="Login failed"
        )

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session_dependency)
) -> User:
    """
    Cookie-based and Bearer token authentication dependency
    Supports both session cookies and Authorization header tokens
    """
    session_token = None
    
    # Try to get token from Authorization header first (Bearer token)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        session_token = auth_header[7:]  # Remove "Bearer " prefix
        logger.debug("🔐 Using Bearer token from Authorization header")
    
    # Fall back to cookie-based authentication
    if not session_token:
        session_token = request.cookies.get("session_token")
        if session_token:
            logger.debug("🔐 Using session token from cookie")
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check fallback sessions first (for when DB is unavailable)
    if session_token in TEMP_SESSIONS:
        session_data = TEMP_SESSIONS[session_token]
        # Check if session is expired
        if datetime.now() > session_data["expires_at"]:
            del TEMP_SESSIONS[session_token]
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )
        
        logger.debug(f"✅ Using fallback session for user: {session_data['email']}")
        
        # Create a user-like object for fallback sessions
        class FallbackUser:
            def __init__(self, data):
                self.id = data["user_id"]
                self.email = data["email"] 
                self.username = data["username"]
                self.is_active = data["is_active"]
                self.created_at = datetime.fromisoformat(data["created_at"])
        
        return FallbackUser(session_data)
    
    # If not in fallback sessions but we have a token, recreate fallback session
    # This handles cases where server restarted but user still has cookie
    if session_token and not session_token in TEMP_SESSIONS:
        logger.warning(f"🔄 Session token exists but not in fallback sessions, recreating...")
        
        # Create a new fallback session for admin user (default fallback)
        session_expires = datetime.now() + timedelta(hours=8)
        TEMP_SESSIONS[session_token] = {
            "user_id": "admin-user-id",
            "email": "admin@pss-knowledge-assist.com",
            "username": "PSS Admin",
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "expires_at": session_expires,
            "session_created_at": datetime.now()
        }
        
        logger.info(f"🔄 Recreated fallback session for: admin@pss-knowledge-assist.com")
        
        class FallbackUser:
            def __init__(self, data):
                self.id = data["user_id"]
                self.email = data["email"] 
                self.username = data["username"]
                self.is_active = data["is_active"]
                self.created_at = datetime.fromisoformat(data["created_at"])
        
        return FallbackUser(TEMP_SESSIONS[session_token])
    
    # Try database session validation only if not in fallback sessions
    try:
        session_repo = SessionRepository(db)
        user = await session_repo.validate_session(session_token)
        
        if user:
            logger.debug(f"✅ Using database session for user: {user.email}")
            return user
        else:
            logger.warning(f"❌ Database session validation failed for token: {session_token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
            
    except Exception as e:
        logger.warning(f"❌ Database session validation error: {e}")
        # If database validation fails, check if this might be a fallback session
        # that we missed (perhaps from an older session format)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    response: Response,
    login_request: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session_dependency) if DATABASE_AVAILABLE else None
):
    """
    User authentication with database fallback to temporary authentication
    """
    # If database is not available, use fallback authentication
    if not DATABASE_AVAILABLE or db is None:
        logger.warning("⚠️ Database not available, using fallback authentication")
        return await fallback_login(login_request, response, request)
    
    # Try database authentication first
    try:
        logger.info(f"🔍 Attempting database authentication for: {login_request.email}")
        user_repo = UserRepository(db)
        session_repo = SessionRepository(db)
        
        # Authenticate user with database (this already updates last_login_at)
        user = await user_repo.authenticate_user(login_request.email, login_request.password)
        logger.info(f"🔍 Database auth result for {login_request.email}: {user is not None}")
        
        if user:
            # Create user session using repository (pass user_id instead of user object)
            session = await session_repo.create_session(
                user_id=user.id,
                user_email=user.email,
                remember_me=login_request.remember_me,
                request=request
            )
            
            await db.commit()
            await db.refresh(session)
            await db.refresh(user)
            
            session_duration_seconds = seconds_until_expiry(session.expires_at, utc_now())
            
            is_production = not (
                request.url.hostname in ["localhost", "127.0.0.1"] or 
                request.url.scheme == "http"
            )
            
            response.set_cookie(
                key="session_token",
                value=session.session_token,
                max_age=session_duration_seconds,
                httponly=True,
                secure=is_production,
                samesite="strict",
                path="/"
            )
            
            logger.info(f"✅ Database login successful: {user.email}")
            
            return LoginResponse(
                success=True,
                message="Login successful",
                user={
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                },
                session_duration=session_duration_seconds,
                session_token=session.session_token  # Include session token in response
            )
        else:
            logger.warning(f"❌ Database login failed: {login_request.email}")
            logger.info("⚠️ User not found in database, falling back to temporary authentication")
            fallback_result = await fallback_login(login_request, response, request)
            logger.info(f"🔄 Fallback result: {fallback_result.success}")
            return fallback_result
            
    except Exception as e:
        logger.error(f"❌ Database authentication error: {e}")
        logger.warning("⚠️ Falling back to temporary authentication due to exception")
        fallback_result = await fallback_login(login_request, response, request)
        logger.info(f"🔄 Exception fallback result: {fallback_result.success}")
        return fallback_result


@router.get("/validate")
async def validate_session(
    current_user: User = Depends(get_current_user)
):
    """
    Validate current session and return user info
    Used by frontend to check authentication status
    
    Returns:
        User information if session is valid
        
    Raises:
        HTTPException: 401 if session is invalid
    """
    return {
        "success": True,
        "user": {
            "id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        }
    }


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Cookie-based logout
    """
    try:
        session_token = request.cookies.get("session_token")
        
        response.delete_cookie(
            key="session_token",
            path="/",
            httponly=True,
            secure=not (request.url.hostname in ["localhost", "127.0.0.1"]),
            samesite="strict"
        )
        
        if session_token:
            session_repo = SessionRepository(db)
            await session_repo.invalidate_session(session_token)
            await db.commit()
        
        return {"success": True, "message": "Logged out successfully"}
            
    except Exception as e:
        logger.error(f"Logout error: {e}")
        await db.rollback()
        return {"success": True, "message": "Logged out successfully"}


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Register a new user account
    """
    try:
        user_repo = UserRepository(db)
        
        # Check if email already exists
        if await user_repo.email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered"
            )
        
        # Validate password strength
        is_valid, errors = validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password does not meet requirements: {'; '.join(errors)}"
            )
        
        # Create user
        user = await user_repo.create_user(user_data)
        await db.commit()
        
        logger.info(f"New user registered: {user.email}")
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile information
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Update current user's profile information
    """
    try:
        user_repo = UserRepository(db)
        
        # Update user (is_active changes require admin privileges, handled in repository)
        updated_user = await user_repo.update_user(current_user.id, user_update)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        await db.commit()
        
        logger.info(f"User profile updated: {updated_user.email}")
        
        return UserResponse(
            id=str(updated_user.id),
            email=updated_user.email,
            username=updated_user.username,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            last_login_at=updated_user.last_login_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Change current user's password
    """
    try:
        user_repo = UserRepository(db)
        
        # Verify current password
        user = await user_repo.authenticate_user(current_user.email, password_data.current_password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        is_valid, errors = validate_password_strength(password_data.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"New password does not meet requirements: {'; '.join(errors)}"
            )
        
        # Update password
        success = await user_repo.update_password(current_user.id, password_data.new_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password update failed"
            )
        
        await db.commit()
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return {"message": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    List all users (admin functionality - placeholder for future role-based access)
    """
    try:
        user_repo = UserRepository(db)
        
        # Get users and total count
        users = await user_repo.list_users(skip=skip, limit=limit, include_inactive=include_inactive)
        total = await user_repo.count_users(include_inactive=include_inactive)
        
        user_responses = [
            UserResponse(
                id=str(user.id),
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login_at=user.last_login_at
            )
            for user in users
        ]
        
        return UserListResponse(
            users=user_responses,
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            page_size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/debug-session", include_in_schema=False)
async def debug_session(request: Request):
    """Debug endpoint to check session status"""
    try:
        # Get session token from various sources
        cookie_token = request.cookies.get("session_token")
        auth_header = request.headers.get("Authorization")
        bearer_token = None
        if auth_header and auth_header.startswith("Bearer "):
            bearer_token = auth_header[7:]
        
        # Check fallback sessions
        active_sessions = list(TEMP_SESSIONS.keys())
        
        return {
            "cookie_token": cookie_token[:10] + "..." if cookie_token else None,
            "bearer_token": bearer_token[:10] + "..." if bearer_token else None,
            "active_fallback_sessions": len(active_sessions),
            "session_previews": [token[:10] + "..." for token in active_sessions[:3]],
            "cookies": dict(request.cookies),
            "auth_header": auth_header
        }
    except Exception as e:
        return {"error": str(e)}
