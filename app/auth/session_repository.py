"""
Session repository for database operations
Handles all session-related database queries and operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import uuid
import logging
import secrets
from fastapi import Request

from ..database.models import User, UserSession
from ..models.schemas import UserCreate, UserUpdate

from ..utils.datetime_utils import utc_now, utc_plus_timedelta, is_expired, seconds_until_expiry

logger = logging.getLogger(__name__)


class SessionRepository:
    """Repository pattern for UserSession database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def generate_session_token(self) -> str:
        """
        Generate a secure session token using cryptographically strong random data
        
        Returns:
            Secure URL-safe token string
        """
        return secrets.token_urlsafe(32)  # 256-bit token
    
    async def create_session(
        self,
        user_id: uuid.UUID,
        user_email: str,
        remember_me: bool,
        request: Request
    ) -> UserSession:
        """
        Create a new user session in the database
        
        Args:
            user_id: User's unique identifier
            user_email: User's email address (for logging)
            remember_me: Whether this is a persistent session
            request: FastAPI request object for extracting client info
            
        Returns:
            Created UserSession object
            
        Raises:
            ValueError: If session creation fails
        """
        try:
            # Calculate expiration based on remember_me flag
            if remember_me:
                expires_at = utc_plus_timedelta(timedelta(days=30))  # 30 days for persistent sessions
            else:
                expires_at = utc_plus_timedelta(timedelta(hours=8))   # 8 hours for regular sessions
            
            # Generate secure session token
            session_token = self.generate_session_token()
            
            # Extract client information
            user_agent = request.headers.get('User-Agent', 'Unknown')
            
            # Extract IP address, handling potential proxy headers
            ip_address = request.client.host if request.client else None
            if forwarded_for := request.headers.get('X-Forwarded-For'):
                ip_address = forwarded_for.split(',')[0].strip()
            elif real_ip := request.headers.get('X-Real-IP'):
                ip_address = real_ip
                        
            # Create session record
            session = UserSession(
                id=uuid.uuid4(),
                user_id=user_id,
                session_token=session_token,
                expires_at=expires_at,
                remember_me=remember_me,
                user_agent=user_agent,
                ip_address=ip_address,
                created_at=utc_now()
            )
            
            self.session.add(session)
            await self.session.flush()  # Get the ID without committing
            
            logger.info(f"Session created successfully for user {user_email}: {session.id}")
            return session
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Session creation failed for user {user_id}: {e}")
            raise ValueError(f"Session creation failed: {str(e)}")
    
    async def get_session_by_token(self, session_token: str) -> Optional[UserSession]:
        """
        Find session by token
        
        Args:
            session_token: Session token to look up
            
        Returns:
            UserSession object if found, None otherwise
        """
        try:
            stmt = select(UserSession).where(UserSession.session_token == session_token)
            result = await self.session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if session:
                logger.debug(f"Session found: {session.id}")
            else:
                logger.debug(f"Session not found for token")
            
            return session
            
        except Exception as e:
            logger.error(f"Error finding session by token: {e}")
            return None
    
    async def validate_session(self, session_token: str) -> Optional[User]:
        """
        Validate session token and return associated user if valid
        
        Args:
            session_token: Session token to validate
            
        Returns:
            User object if session is valid, None otherwise
        """
        try:
            # Get session with associated user in one query
            stmt = (
                select(UserSession, User)
                .join(User, UserSession.user_id == User.id)
                .where(
                    and_(
                        UserSession.session_token == session_token,
                        UserSession.expires_at > utc_now(),
                        User.is_active == True
                    )
                )
            )
            
            result = await self.session.execute(stmt)
            session_user = result.first()
            
            if not session_user:
                logger.debug("Session validation failed - not found or expired")
                return None
            
            session, user = session_user
            
            logger.debug(f"Session validated successfully for user: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    async def invalidate_session(self, session_token: str) -> bool:
        """
        Invalidate a specific session (logout)
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            stmt = delete(UserSession).where(UserSession.session_token == session_token)
            result = await self.session.execute(stmt)
            
            if result.rowcount > 0:
                logger.info(f"Session invalidated successfully")
                return True
            else:
                logger.warning(f"Session invalidation failed - session not found")
                return False
                
        except Exception as e:
            logger.error(f"Session invalidation failed: {e}")
            await self.session.rollback()
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from database
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            stmt = delete(UserSession).where(UserSession.expires_at <= utc_now())
            result = await self.session.execute(stmt)
            
            count = result.rowcount
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            else:
                logger.debug("No expired sessions to clean up")
            
            return count
            
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            await self.session.rollback()
            return 0
    
    async def get_user_sessions(
        self, 
        user_id: uuid.UUID,
        include_expired: bool = False
    ) -> List[UserSession]:
        """
        Get all sessions for a user
        
        Args:
            user_id: User's unique identifier
            include_expired: Whether to include expired sessions
            
        Returns:
            List of UserSession objects
        """
        try:
            stmt = select(UserSession).where(UserSession.user_id == user_id)
            
            if not include_expired:
                stmt = stmt.where(UserSession.expires_at > utc_now())
            
            stmt = stmt.order_by(UserSession.created_at.desc())
            
            result = await self.session.execute(stmt)
            sessions = result.scalars().all()
            
            logger.debug(f"Retrieved {len(sessions)} sessions for user {user_id}")
            return list(sessions)
            
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []
    
    async def invalidate_all_user_sessions(self, user_id: uuid.UUID) -> int:
        """
        Invalidate all sessions for a user (e.g., for password change, security)
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Number of sessions invalidated
        """
        try:
            stmt = delete(UserSession).where(UserSession.user_id == user_id)
            result = await self.session.execute(stmt)
            
            count = result.rowcount
            if count > 0:
                logger.info(f"Invalidated {count} sessions for user {user_id}")
            else:
                logger.debug(f"No sessions found to invalidate for user {user_id}")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to invalidate user sessions for {user_id}: {e}")
            await self.session.rollback()
            return 0
    
    async def extend_session(self, session_token: str, additional_hours: int = 8) -> bool:
        """
        Extend session expiration time
        
        Args:
            session_token: Session token to extend
            additional_hours: Hours to add to expiration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            new_expires_at = utc_plus_timedelta(timedelta(hours=additional_hours))
            
            stmt = (
                update(UserSession)
                .where(UserSession.session_token == session_token)
                .values(expires_at=new_expires_at)
            )
            
            result = await self.session.execute(stmt)
            
            if result.rowcount > 0:
                logger.info(f"Session extended successfully")
                return True
            else:
                logger.warning(f"Session extension failed - session not found")
                return False
                
        except Exception as e:
            logger.error(f"Session extension failed: {e}")
            await self.session.rollback()
            return False
    
    async def count_active_sessions(self, user_id: Optional[uuid.UUID] = None) -> int:
        """
        Count active (non-expired) sessions
        
        Args:
            user_id: Optional user ID to count sessions for specific user
            
        Returns:
            Number of active sessions
        """
        try:
            stmt = select(func.count(UserSession.id)).where(
                UserSession.expires_at > utc_now()
            )
            
            if user_id:
                stmt = stmt.where(UserSession.user_id == user_id)
            
            result = await self.session.execute(stmt)
            count = result.scalar()
            
            logger.debug(f"Active session count: {count}")
            return count or 0
            
        except Exception as e:
            logger.error(f"Error counting active sessions: {e}")
            return 0
