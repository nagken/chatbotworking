"""
Conversation service layer
Handles business logic for conversation operations
"""

from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from ..models.schemas import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationDetailResponse, ConversationSummary, MessageSummary
)
from ..database.models import User
from ..repositories.chat_repository import ChatConversationRepository, ChatMessageRepository
from ..utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class ConversationService:
    """Service layer for conversation business logic"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversation_repo = ChatConversationRepository(session)
        self.message_repo = ChatMessageRepository(session)
    
    def _validate_uuid(self, conversation_id: str) -> uuid.UUID:
        """
        Validate and convert conversation ID string to UUID
        
        Args:
            conversation_id: Conversation ID string
            
        Returns:
            Validated UUID
            
        Raises:
            ValueError: If conversation ID is invalid
        """
        try:
            return uuid.UUID(conversation_id)
        except ValueError as e:
            logger.warning(f"Invalid conversation ID format: {conversation_id}")
            raise ValueError(f"Invalid conversation ID format: {conversation_id}")
    
    async def create_conversation(
        self,
        user: User,
        request: ConversationCreate
    ) -> ConversationResponse:
        """
        Create a new conversation for a user
        
        Args:
            user: Current user
            request: Conversation creation request
            
        Returns:
            ConversationResponse with success status and conversation details
        """
        try:
            # Generate unique conversation_id
            conversation_id = str(uuid.uuid4())
            
            # Use provided title or generate one later from first message
            title = request.title or "New Conversation"
            
            # Create the conversation
            conversation = await self.conversation_repo.create_conversation(
                user_id=user.id,
                conversation_id=conversation_id,
                title=title
            )
            
            await self.session.commit()
            
            logger.info(f"Created conversation {conversation.id} for user {user.id}")
            
            return ConversationResponse(
                success=True,
                message="Conversation created successfully",
                conversation=ConversationDetailResponse(
                    id=str(conversation.id),
                    title=conversation.title,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    message_count=0
                )
            )
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create conversation for user {user.id}: {e}")
            raise
    
    async def get_conversation(
        self,
        conversation_id: str,
        user: User
    ) -> ConversationDetailResponse:
        """
        Get detailed information about a specific conversation
        
        Args:
            conversation_id: Conversation ID string
            user: Current user
            
        Returns:
            ConversationDetailResponse with conversation details
            
        Raises:
            ValueError: If conversation ID is invalid
            PermissionError: If user doesn't own the conversation
            FileNotFoundError: If conversation doesn't exist
        """
        try:
            # Validate conversation UUID
            conversation_uuid = self._validate_uuid(conversation_id)
            
            # Validate ownership and get conversation with message count
            is_owner, conversation = await self.conversation_repo.validate_conversation_ownership(
                conversation_id=conversation_uuid,
                user_id=user.id
            )
            
            if not is_owner:
                if not conversation:
                    raise FileNotFoundError("Conversation not found")
                else:
                    raise PermissionError("Access denied to this conversation")
            
            # Get conversation with message count
            conversation, message_count = await self.conversation_repo.get_conversation_with_message_count(conversation_uuid)
            
            return ConversationDetailResponse(
                id=str(conversation.id),
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                message_count=message_count
            )
            
        except (ValueError, PermissionError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {e}")
            raise
    
    async def update_conversation(
        self,
        conversation_id: str,
        request: ConversationUpdate,
        user: User
    ) -> ConversationResponse:
        """
        Update conversation details (e.g., rename)
        
        Args:
            conversation_id: Conversation ID string
            request: Conversation update request
            user: Current user
            
        Returns:
            ConversationResponse with success status and updated conversation details
            
        Raises:
            ValueError: If conversation ID is invalid
            PermissionError: If user doesn't own the conversation
            FileNotFoundError: If conversation doesn't exist
        """
        try:
            # Validate conversation UUID
            conversation_uuid = self._validate_uuid(conversation_id)
            
            # Validate ownership
            is_owner, conversation = await self.conversation_repo.validate_conversation_ownership(
                conversation_id=conversation_uuid,
                user_id=user.id
            )
            
            if not is_owner:
                if not conversation:
                    raise FileNotFoundError("Conversation not found")
                else:
                    raise PermissionError("Access denied to this conversation")
            
            # Update the conversation
            success = await self.conversation_repo.update_conversation_title(
                conversation_id=conversation.id,
                title=request.title
            )
            
            if not success:
                raise RuntimeError("Failed to update conversation")
            
            # Refresh conversation data with message count
            conversation, message_count = await self.conversation_repo.get_conversation_with_message_count(conversation.id)
            
            return ConversationResponse(
                success=True,
                message="Conversation updated successfully",
                conversation=ConversationDetailResponse(
                    id=str(conversation.id),
                    title=conversation.title,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    message_count=message_count
                )
            )
            
        except (ValueError, PermissionError, FileNotFoundError, RuntimeError):
            raise
        except Exception as e:
            logger.error(f"Failed to update conversation {conversation_id}: {e}")
            raise
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user: User
    ) -> bool:
        """
        Delete a conversation and all its messages
        
        Args:
            conversation_id: Conversation ID string
            user: Current user
            
        Returns:
            True if deletion was successful
            
        Raises:
            ValueError: If conversation ID is invalid
            PermissionError: If user doesn't own the conversation
            FileNotFoundError: If conversation doesn't exist
        """
        try:
            # Validate conversation UUID
            conversation_uuid = self._validate_uuid(conversation_id)
            
            # Validate ownership
            is_owner, conversation = await self.conversation_repo.validate_conversation_ownership(
                conversation_id=conversation_uuid,
                user_id=user.id
            )
            
            if not is_owner:
                if not conversation:
                    raise FileNotFoundError("Conversation not found")
                else:
                    raise PermissionError("Access denied to this conversation")
            
            # Delete the conversation (cascade will handle messages)
            success = await self.conversation_repo.delete_conversation(conversation.id)
            
            if not success:
                raise RuntimeError("Failed to delete conversation")
            
            logger.info(f"Deleted conversation {conversation_id} for user {user.id}")
            return True
            
        except (ValueError, PermissionError, FileNotFoundError, RuntimeError):
            raise
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
            raise
    
    async def list_user_conversations(
        self,
        user: User,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[ConversationSummary], int]:
        """
        Get user's conversations with last message summary
        
        Args:
            user: Current user
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (conversation_summaries, total_count)
        """
        try:
            # Get user's conversations
            conversations = await self.conversation_repo.get_user_conversations(
                user_id=user.id,
                skip=skip,
                limit=limit
            )
            
            # Build response with last message summaries
            conversation_summaries = []
            
            for conversation in conversations:
                # Get the last message pair for this conversation
                last_user_message, last_assistant_message = await self.message_repo.get_last_message_pair(conversation.id)
                
                last_message_summary = None
                if last_user_message:
                    last_message_summary = MessageSummary(
                        user_message=last_user_message.content,
                        assistant_message=last_assistant_message.content if last_assistant_message else None,
                        timestamp=last_user_message.created_at
                    )
                
                conversation_summaries.append(ConversationSummary(
                    id=str(conversation.id),
                    title=conversation.title or "Untitled Conversation",
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    last_message=last_message_summary
                ))
            
            # Count total conversations for pagination
            total_count = await self.conversation_repo.count_user_conversations(user.id)
            
            return conversation_summaries, total_count
            
        except Exception as e:
            logger.error(f"Failed to list conversations for user {user.id}: {e}")
            raise
