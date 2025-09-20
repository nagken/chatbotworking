"""
User repository for database operations
Handles all user-related database queries and operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import uuid
import logging

from ..database.models import User, UserSession
from ..models.schemas import UserCreate, UserUpdate
from .password_utils import hash_password, verify_password, needs_password_rehash
from ..utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository pattern for User database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user with hashed password
        
        Args:
            user_data: User creation data with plain text password
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If user creation fails (e.g., duplicate email)
        """
        try:
            # Hash the password
            password_hash = hash_password(user_data.password)
            
            # Create user object
            user = User(
                id=uuid.uuid4(),
                email=user_data.email.lower(),  # Store emails in lowercase
                username=user_data.username,
                password_hash=password_hash,
                is_active=True,
                created_at=utc_now(),
                updated_at=utc_now()
            )
            
            self.session.add(user)
            await self.session.flush()  # Get the ID without committing
            
            logger.info(f"User created successfully: {user.email}")
            return user
            
        except IntegrityError as e:
            await self.session.rollback()
            if "email" in str(e.orig):
                raise ValueError("Email address is already registered")
            else:
                raise ValueError("User creation failed due to data conflict")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"User creation failed: {e}")
            raise ValueError(f"User creation failed: {str(e)}")
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email address
        
        Args:
            email: User's email address
            
        Returns:
            User object if found, None otherwise
        """
        try:
            stmt = select(User).where(User.email == email.lower())
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                logger.debug(f"User found: {email}")
            else:
                logger.debug(f"User not found: {email}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}")
            return None
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Find user by ID
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User object if found, None otherwise
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                logger.debug(f"User found by ID: {user_id}")
            else:
                logger.debug(f"User not found by ID: {user_id}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error finding user by ID {user_id}: {e}")
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            user = await self.get_user_by_email(email)
            
            if not user:
                logger.debug(f"Authentication failed - user not found: {email}")
                return None
            
            if not user.is_active:
                logger.debug(f"Authentication failed - user inactive: {email}")
                return None
            
            # Verify password
            if not verify_password(password, user.password_hash):
                logger.debug(f"Authentication failed - invalid password: {email}")
                return None
            
            # Update last login time
            await self.update_last_login(user.id)
            
            # Check if password needs rehashing (security improvement)
            if needs_password_rehash(user.password_hash):
                logger.info(f"Updating password hash for user: {email}")
                await self.update_password(user.id, password)
            
            logger.info(f"User authenticated successfully: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            return None
    
    async def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        """
        Update user profile information
        
        Args:
            user_id: User's unique identifier
            user_data: Updated user data
            
        Returns:
            Updated User object if successful, None otherwise
        """
        try:
            # Build update data
            update_data = {"updated_at": utc_now()}
            
            if user_data.username is not None:
                update_data["username"] = user_data.username
            
            if user_data.is_active is not None:
                update_data["is_active"] = user_data.is_active
            
            # Execute update
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(**update_data)
                .returning(User)
            )
            
            result = await self.session.execute(stmt)
            updated_user = result.scalar_one_or_none()
            
            if updated_user:
                logger.info(f"User updated successfully: {user_id}")
            else:
                logger.warning(f"User update failed - user not found: {user_id}")
            
            return updated_user
            
        except Exception as e:
            logger.error(f"User update failed for {user_id}: {e}")
            await self.session.rollback()
            return None
    
    async def update_password(self, user_id: uuid.UUID, new_password: str) -> bool:
        """
        Update user's password
        
        Args:
            user_id: User's unique identifier
            new_password: New plain text password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Hash new password
            password_hash = hash_password(new_password)
            
            # Update password
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(
                    password_hash=password_hash,
                    updated_at=utc_now()
                )
            )
            
            result = await self.session.execute(stmt)
            
            if result.rowcount > 0:
                logger.info(f"Password updated successfully for user: {user_id}")
                return True
            else:
                logger.warning(f"Password update failed - user not found: {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Password update failed for {user_id}: {e}")
            await self.session.rollback()
            return False
    
    async def update_last_login(self, user_id: uuid.UUID) -> bool:
        """
        Update user's last login timestamp
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(last_login_at=utc_now())
            )
            
            result = await self.session.execute(stmt)
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Last login update failed for {user_id}: {e}")
            return False
    
    async def deactivate_user(self, user_id: uuid.UUID) -> bool:
        """
        Deactivate user account (soft delete)
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(
                    is_active=False,
                    updated_at=utc_now()
                )
            )
            
            result = await self.session.execute(stmt)
            
            if result.rowcount > 0:
                logger.info(f"User deactivated: {user_id}")
                return True
            else:
                logger.warning(f"User deactivation failed - user not found: {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"User deactivation failed for {user_id}: {e}")
            await self.session.rollback()
            return False
    
    async def list_users(self, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[User]:
        """
        List users with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_inactive: Whether to include inactive users
            
        Returns:
            List of User objects
        """
        try:
            stmt = select(User)
            
            if not include_inactive:
                stmt = stmt.where(User.is_active == True)
            
            stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            users = result.scalars().all()
            
            logger.debug(f"Retrieved {len(users)} users (skip={skip}, limit={limit})")
            return list(users)
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    async def count_users(self, include_inactive: bool = False) -> int:
        """
        Count total number of users
        
        Args:
            include_inactive: Whether to include inactive users
            
        Returns:
            Total number of users
        """
        try:
            stmt = select(func.count(User.id))
            
            if not include_inactive:
                stmt = stmt.where(User.is_active == True)
            
            result = await self.session.execute(stmt)
            count = result.scalar()
            
            logger.debug(f"User count: {count} (include_inactive={include_inactive})")
            return count or 0
            
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0
    
    async def email_exists(self, email: str, exclude_user_id: Optional[uuid.UUID] = None) -> bool:
        """
        Check if email address already exists
        
        Args:
            email: Email address to check
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            True if email exists, False otherwise
        """
        try:
            stmt = select(User.id).where(User.email == email.lower())
            
            if exclude_user_id:
                stmt = stmt.where(User.id != exclude_user_id)
            
            result = await self.session.execute(stmt)
            exists = result.scalar_one_or_none() is not None
            
            logger.debug(f"Email exists check for {email}: {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"Error checking email existence for {email}: {e}")
            return False
