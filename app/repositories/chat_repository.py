"""
Chat repositories for database operations
Handles all chat-related database queries and operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid
import logging

from ..database.models import ChatConversation, ChatMessage, ChatResponse, User, MessageType
from ..models.schemas import ChatResponseExtract
from ..utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class ChatConversationRepository:
    """Repository pattern for ChatConversation database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: str,
        title: Optional[str] = None
    ) -> ChatConversation:
        """
        Create a new chat conversation
        
        Args:
            user_id: User's unique identifier
            conversation_id: Conversation identifier (e.g., "cvs-rebate-conversation")
            title: Optional conversation title
            
        Returns:
            Created ChatConversation object
            
        Raises:
            ValueError: If conversation creation fails
        """
        try:
            conversation = ChatConversation(
                id=uuid.uuid4(),
                user_id=user_id,
                conversation_id=conversation_id,
                title=title,
                created_at=utc_now(),
                updated_at=utc_now()
            )
            
            self.session.add(conversation)
            await self.session.flush()  # Get the ID without committing
            
            logger.info(f"Conversation created successfully: {conversation.id}")
            return conversation
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Conversation creation failed: {e}")
            raise ValueError(f"Conversation creation failed: {str(e)}")
    
    async def get_conversation_by_id(self, conversation_id: uuid.UUID) -> Optional[ChatConversation]:
        """
        Find conversation by ID
        
        Args:
            conversation_id: Conversation's unique identifier
            
        Returns:
            ChatConversation object if found, None otherwise
        """
        try:
            stmt = select(ChatConversation).where(ChatConversation.id == conversation_id)
            result = await self.session.execute(stmt)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                logger.debug(f"Conversation found: {conversation_id}")
            else:
                logger.debug(f"Conversation not found: {conversation_id}")
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error finding conversation by ID {conversation_id}: {e}")
            return None
    
    async def get_conversation_with_message_count(
        self,
        conversation_id: uuid.UUID
    ) -> tuple[Optional[ChatConversation], int]:
        """
        Get conversation by ID along with its message count
        
        Args:
            conversation_id: Conversation's unique identifier
            
        Returns:
            Tuple of (ChatConversation, message_count) or (None, 0) if not found
        """
        try:
            conversation = await self.get_conversation_by_id(conversation_id)
            if not conversation:
                return None, 0
            
            # Count messages in conversation
            stmt = (
                select(func.count(ChatMessage.id))
                .where(ChatMessage.conversation_id == conversation_id)
            )
            result = await self.session.execute(stmt)
            message_count = result.scalar() or 0
            
            logger.debug(f"Retrieved conversation {conversation_id} with {message_count} messages")
            return conversation, message_count
            
        except Exception as e:
            logger.error(f"Error getting conversation with message count {conversation_id}: {e}")
            return None, 0
    
    async def validate_conversation_ownership(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> tuple[bool, Optional[ChatConversation]]:
        """
        Validate if a user owns a conversation
        
        Args:
            conversation_id: Conversation's unique identifier
            user_id: User's unique identifier
            
        Returns:
            Tuple of (is_owner, conversation) where is_owner is True if user owns the conversation
        """
        try:
            conversation = await self.get_conversation_by_id(conversation_id)
            if not conversation:
                return False, None
            
            is_owner = conversation.user_id == user_id
            logger.debug(f"Ownership validation for conversation {conversation_id}: user {user_id} is_owner={is_owner}")
            return is_owner, conversation
            
        except Exception as e:
            logger.error(f"Error validating conversation ownership {conversation_id}: {e}")
            return False, None
    
    async def get_or_create_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: str,
        title: Optional[str] = None
    ) -> ChatConversation:
        """
        Get existing conversation or create new one
        
        Args:
            user_id: User's unique identifier
            conversation_id: Conversation identifier
            title: Optional conversation title for new conversations
            
        Returns:
            ChatConversation object
        """
        try:
            # Try to find existing conversation
            stmt = select(ChatConversation).where(
                and_(
                    ChatConversation.user_id == user_id,
                    ChatConversation.conversation_id == conversation_id
                )
            )
            result = await self.session.execute(stmt)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                logger.debug(f"Found existing conversation: {conversation.id}")
                return conversation
            
            # Create new conversation if not found
            return await self.create_conversation(user_id, conversation_id, title)
            
        except Exception as e:
            logger.error(f"Error getting or creating conversation: {e}")
            raise ValueError(f"Failed to get or create conversation: {str(e)}")
    
    async def update_conversation_title(self, conversation_id: uuid.UUID, title: str) -> bool:
        """
        Update conversation title
        
        Args:
            conversation_id: Conversation's unique identifier
            title: New title
            
        Returns:
            True if successful, False otherwise
        """
        try:
            stmt = (
                update(ChatConversation)
                .where(ChatConversation.id == conversation_id)
                .values(title=title, updated_at=utc_now())
            )
            
            result = await self.session.execute(stmt)
            
            if result.rowcount > 0:
                logger.info(f"Conversation title updated: {conversation_id}")
                return True
            else:
                logger.warning(f"Conversation title update failed - not found: {conversation_id}")
                return False
                
        except Exception as e:
            logger.error(f"Conversation title update failed for {conversation_id}: {e}")
            await self.session.rollback()
            return False
    
    async def get_user_conversations(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[ChatConversation]:
        """
        Get user's conversations with pagination
        
        Args:
            user_id: User's unique identifier
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ChatConversation objects
        """
        try:
            stmt = (
                select(ChatConversation)
                .where(ChatConversation.user_id == user_id)
                .order_by(ChatConversation.updated_at.desc())
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            conversations = result.scalars().all()
            
            logger.debug(f"Retrieved {len(conversations)} conversations for user {user_id}")
            return list(conversations)
            
        except Exception as e:
            logger.error(f"Error getting user conversations for {user_id}: {e}")
            return []

    async def count_user_conversations(self, user_id: uuid.UUID) -> int:
        """
        Count total conversations for a user
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Total number of conversations for the user
        """
        try:
            stmt = (
                select(func.count(ChatConversation.id))
                .where(ChatConversation.user_id == user_id)
            )
            result = await self.session.execute(stmt)
            count = result.scalar() or 0
            
            logger.debug(f"Counted {count} conversations for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error counting conversations for user {user_id}: {e}")
            return 0

    async def delete_conversation(self, conversation_id: uuid.UUID) -> bool:
        """
        Delete a conversation and all its associated messages
        
        Args:
            conversation_id: Conversation's unique identifier
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Find the conversation
            stmt = select(ChatConversation).where(ChatConversation.id == conversation_id)
            result = await self.session.execute(stmt)
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found for deletion")
                return False
            
            # Delete the conversation (cascade will handle messages and responses)
            await self.session.delete(conversation)
            await self.session.commit()
            
            logger.info(f"Successfully deleted conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            await self.session.rollback()
            return False


class ChatMessageRepository:
    """Repository pattern for ChatMessage database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        message_type: MessageType,
        content: str,
        superclient: Optional[str] = None,
        enhanced_message: Optional[str] = None,
        sql_query: Optional[str] = None,
        chart_config: Optional[Dict[str, Any]] = None,
        ai_insights: Optional[str] = None,
        response_metadata: Optional[Dict[str, Any]] = None,
        result_schema: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Create a new chat message
        
        Args:
            conversation_id: Conversation's unique identifier
            user_id: User's unique identifier
            message_type: Type of message (user or assistant)
            content: Message content
            superclient: SuperClient context
            enhanced_message: Enhanced message with context
            sql_query: Generated SQL query for re-execution
            chart_config: Chart configuration without data values
            ai_insights: AI insights about the data analysis
            response_metadata: Additional response metadata
            result_schema: Schema for result data (stored once per message)
            
        Returns:
            Created ChatMessage object
            
        Raises:
            ValueError: If message creation fails
        """
        try:
            message = ChatMessage(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                user_id=user_id,
                message_type=message_type,
                content=content,
                superclient=superclient,
                enhanced_message=enhanced_message,
                sql_query=sql_query,
                chart_config=chart_config,
                ai_insights=ai_insights,
                response_metadata=response_metadata,
                result_schema=result_schema,
                created_at=utc_now()
            )
            
            self.session.add(message)
            await self.session.flush()  # Get the ID without committing
            
            logger.info(f"Message created successfully: {message.id}")
            return message
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Message creation failed: {e}")
            raise ValueError(f"Message creation failed: {str(e)}")
    
    async def get_message_by_id(self, message_id: uuid.UUID) -> Optional[ChatMessage]:
        """
        Find message by ID
        
        Args:
            message_id: Message's unique identifier
            
        Returns:
            ChatMessage object if found, None otherwise
        """
        try:
            stmt = select(ChatMessage).where(ChatMessage.id == message_id)
            result = await self.session.execute(stmt)
            message = result.scalar_one_or_none()
            
            if message:
                logger.debug(f"Message found: {message_id}")
            else:
                logger.debug(f"Message not found: {message_id}")
            
            return message
            
        except Exception as e:
            logger.error(f"Error finding message by ID {message_id}: {e}")
            return None
    
    async def get_conversation_messages(
        self,
        conversation_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatMessage]:
        """
        Get messages in a conversation with pagination
        
        Args:
            conversation_id: Conversation's unique identifier
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ChatMessage objects ordered by creation time
        """
        try:
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at.asc())
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            messages = result.scalars().all()
            
            logger.debug(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
            return list(messages)
            
        except Exception as e:
            logger.error(f"Error getting conversation messages for {conversation_id}: {e}")
            return []
    
    async def get_all_conversation_messages(
        self,
        conversation_id: uuid.UUID
    ) -> List[ChatMessage]:
        """
        Get all messages in a conversation ordered by creation time
        
        Args:
            conversation_id: Conversation's unique identifier
            
        Returns:
            List of ChatMessage objects ordered chronologically
        """
        try:
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at.asc())
            )
            
            result = await self.session.execute(stmt)
            messages = result.scalars().all()
            
            logger.debug(f"Retrieved all {len(messages)} messages for conversation {conversation_id}")
            return list(messages)
            
        except Exception as e:
            logger.error(f"Error getting all conversation messages for {conversation_id}: {e}")
            return []
    
    async def get_recent_conversation_messages(
        self,
        conversation_id: uuid.UUID,
        limit: int = 50
    ) -> List[ChatMessage]:
        """
        Get the most recent messages in a conversation
        
        Args:
            conversation_id: Conversation's unique identifier
            limit: Maximum number of recent messages to return
            
        Returns:
            List of ChatMessage objects ordered by creation time (oldest first)
        """
        try:
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            messages = result.scalars().all()
            
            # Reverse to get chronological order (oldest first)
            messages = list(messages)[::-1]
            
            logger.debug(f"Retrieved {len(messages)} recent messages for conversation {conversation_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting recent conversation messages for {conversation_id}: {e}")
            return []
    
    async def get_last_message_pair(
        self,
        conversation_id: uuid.UUID
    ) -> tuple[Optional[ChatMessage], Optional[ChatMessage]]:
        """
        Get the last user message and assistant response pair for a conversation
        
        Args:
            conversation_id: Conversation's unique identifier
            
        Returns:
            Tuple of (last_user_message, last_assistant_message) or (None, None) if not found
        """
        try:
            # Get the most recent messages to find the last pair
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(20)  # Get more messages to ensure we find the pair
            )
            
            result = await self.session.execute(stmt)
            recent_messages = result.scalars().all()
            
            if not recent_messages:
                return None, None
            
            # Find the last user message and corresponding assistant response
            last_user_message = None
            last_assistant_message = None
            
            for message in recent_messages:
                if message.message_type == MessageType.USER and not last_user_message:
                    last_user_message = message
                elif (message.message_type == MessageType.ASSISTANT and 
                      not last_assistant_message and 
                      last_user_message):
                    last_assistant_message = message
                    break
            
            logger.debug(f"Retrieved last message pair for conversation {conversation_id}")
            return last_user_message, last_assistant_message
            
        except Exception as e:
            logger.error(f"Error getting last message pair for conversation {conversation_id}: {e}")
            return None, None
    
    async def count_conversation_messages(self, conversation_id: uuid.UUID) -> int:
        """
        Count total messages in a conversation
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            Total message count
        """
        try:
            result = await self.session.execute(
                select(func.count(ChatMessage.id))
                .where(ChatMessage.conversation_id == conversation_id)
            )
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to count messages for conversation {conversation_id}: {e}")
            return 0
    
    async def get_message_by_id(self, message_id: uuid.UUID) -> Optional[ChatMessage]:
        """
        Get a specific message by ID
        
        Args:
            message_id: Message UUID
            
        Returns:
            ChatMessage object or None if not found
        """
        try:
            result = await self.session.execute(
                select(ChatMessage)
                .where(ChatMessage.id == message_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get message {message_id}: {e}")
            return None
    
    async def get_user_messages(
        self,
        user_id: uuid.UUID,
        superclient: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatMessage]:
        """
        Get user's messages with optional SuperClient filtering
        
        Args:
            user_id: User's unique identifier
            superclient: Optional SuperClient filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ChatMessage objects
        """
        try:
            stmt = select(ChatMessage).where(ChatMessage.user_id == user_id)
            
            if superclient:
                stmt = stmt.where(ChatMessage.superclient == superclient)
            
            stmt = stmt.order_by(ChatMessage.created_at.desc()).offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            messages = result.scalars().all()
            
            logger.debug(f"Retrieved {len(messages)} messages for user {user_id}")
            return list(messages)
            
        except Exception as e:
            logger.error(f"Error getting user messages for {user_id}: {e}")
            return []
    

    
    async def update_message_schema(
        self,
        message_id: uuid.UUID,
        schema: Dict[str, Any]
    ) -> bool:
        """
        Update the result_schema field of a ChatMessage
        
        Args:
            message_id: Message's unique identifier
            schema: Schema data to store
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            stmt = (
                update(ChatMessage)
                .where(ChatMessage.id == message_id)
                .values(result_schema=schema)
            )
            
            result = await self.session.execute(stmt)
            await self.session.flush()
            
            if result.rowcount > 0:
                logger.info(f"Updated schema for message {message_id}")
                return True
            else:
                logger.warning(f"No message found to update schema for {message_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating schema for message {message_id}: {e}")
            return False
    
    # Message Feedback Methods
    async def add_feedback(
        self,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        is_positive: bool,
        feedback_comment: Optional[str] = None
    ) -> bool:
        """
        Add user feedback to an assistant message
        
        Args:
            message_id: Message's unique identifier
            user_id: User providing feedback
            is_positive: True for thumbs up, False for thumbs down
            feedback_comment: Optional feedback comment
            
        Returns:
            True if feedback added successfully, False otherwise
            
        Raises:
            ValueError: If feedback already exists or message not found/not assistant type
        """
        try:
            # First, verify the message exists and is an assistant message
            message = await self.get_message_by_id(message_id)
            if not message:
                raise ValueError(f"Message {message_id} not found")
            
            if message.message_type != MessageType.ASSISTANT:
                raise ValueError("Feedback can only be added to assistant messages")
            
            # Check if user already provided feedback for this message
            if message.feedback_user_id == user_id and message.is_positive is not None:
                raise ValueError("User feedback already exists for this message")
            
            # Update the message with feedback
            stmt = (
                update(ChatMessage)
                .where(ChatMessage.id == message_id)
                .values(
                    is_positive=is_positive,
                    feedback_comment=feedback_comment,
                    feedback_user_id=user_id,
                    feedback_created_at=utc_now()
                )
            )
            
            result = await self.session.execute(stmt)
            await self.session.flush()
            
            if result.rowcount > 0:
                logger.info(f"Added feedback to message {message_id} - User: {user_id}, Positive: {is_positive}")
                return True
            else:
                logger.warning(f"No message updated for feedback - Message ID: {message_id}")
                return False
                
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Error adding feedback to message {message_id}: {e}")
            return False
    
    async def update_feedback(
        self,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        is_positive: bool,
        feedback_comment: Optional[str] = None
    ) -> bool:
        """
        Update existing user feedback on an assistant message
        
        Args:
            message_id: Message's unique identifier
            user_id: User updating feedback
            is_positive: True for thumbs up, False for thumbs down
            feedback_comment: Optional feedback comment
            
        Returns:
            True if feedback updated successfully, False otherwise
            
        Raises:
            ValueError: If no existing feedback found or message not found/not assistant type
        """
        try:
            # Verify the message exists, is an assistant message, and has existing feedback from this user
            message = await self.get_message_by_id(message_id)
            if not message:
                raise ValueError(f"Message {message_id} not found")
            
            if message.message_type != MessageType.ASSISTANT:
                raise ValueError("Feedback can only be updated on assistant messages")
            
            if message.feedback_user_id != user_id or message.is_positive is None:
                raise ValueError("No existing feedback found for this user on this message")
            
            # Update the existing feedback
            stmt = (
                update(ChatMessage)
                .where(ChatMessage.id == message_id)
                .values(
                    is_positive=is_positive,
                    feedback_comment=feedback_comment,
                    feedback_created_at=utc_now()  # Update timestamp when feedback changes
                )
            )
            
            result = await self.session.execute(stmt)
            await self.session.flush()
            
            if result.rowcount > 0:
                logger.info(f"Updated feedback on message {message_id} - User: {user_id}, Positive: {is_positive}")
                return True
            else:
                logger.warning(f"No message updated for feedback update - Message ID: {message_id}")
                return False
                
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Error updating feedback on message {message_id}: {e}")
            return False
    
    async def get_message_with_user_feedback(
        self,
        message_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[ChatMessage]:
        """
        Get message with user's feedback if it exists
        
        Args:
            message_id: Message's unique identifier
            user_id: User whose feedback to check
            
        Returns:
            ChatMessage with feedback data if found, None if no message or no feedback
        """
        try:
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.id == message_id)
                .where(ChatMessage.feedback_user_id == user_id)
                .where(ChatMessage.is_positive.isnot(None))
            )
            
            result = await self.session.execute(stmt)
            message = result.scalar_one_or_none()
            
            if message:
                logger.debug(f"Found message with feedback: {message_id}")
            else:
                logger.debug(f"No message with feedback found: {message_id}")
            
            return message
            
        except Exception as e:
            logger.error(f"Error getting message with feedback {message_id}: {e}")
            return None
    
    async def get_user_feedback_history(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        skip: int = 0
    ) -> List[ChatMessage]:
        """
        Get user's feedback history on assistant messages
        
        Args:
            user_id: User's unique identifier
            limit: Maximum number of messages to return
            skip: Number of messages to skip
            
        Returns:
            List of ChatMessage objects with feedback from this user
        """
        try:
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.feedback_user_id == user_id)
                .where(ChatMessage.is_positive.isnot(None))
                .where(ChatMessage.message_type == MessageType.ASSISTANT)
                .order_by(ChatMessage.feedback_created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            messages = result.scalars().all()
            
            logger.debug(f"Retrieved {len(messages)} feedback messages for user {user_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting user feedback history for {user_id}: {e}")
            return []


class ChatResponseRepository:
    """Repository pattern for ChatResponse database operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_response(
        self,
        response_id: uuid.UUID,
        message_id: uuid.UUID,
        success: bool,
        error_message: Optional[str] = None,
        generated_sql: Optional[str] = None,
        insight: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> ChatResponse:
        """
        Create a new chat response
        
        Args:
            response_id: Response's unique identifier
            message_id: Associated message's unique identifier
            success: Whether processing was successful
            error_message: Error message if processing failed
            generated_sql: Generated SQL query if successful
            insight: AI insight about the data
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            Created ChatResponse object
            
        Raises:
            ValueError: If response creation fails
        """
        try:
            response = ChatResponse(
                id=response_id,
                message_id=message_id,
                generated_sql=generated_sql,
                insight=insight,
                processing_time_ms=processing_time_ms,
                success=success,
                error_message=error_message,
                created_at=utc_now()
            )
            
            self.session.add(response)
            await self.session.flush()  # Get the ID without committing
            
            logger.info(f"Chat response saved to database: {response_id}")
            return response
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Chat response creation failed for {response_id}: {e}")
            raise ValueError(f"Chat response creation failed: {str(e)}")
    
    async def get_response_by_id(self, response_id: uuid.UUID) -> Optional[ChatResponse]:
        """
        Find response by ID
        
        Args:
            response_id: Response's unique identifier
            
        Returns:
            ChatResponse object if found, None otherwise
        """
        try:
            stmt = select(ChatResponse).where(ChatResponse.id == response_id)
            result = await self.session.execute(stmt)
            response = result.scalar_one_or_none()
            
            if response:
                logger.debug(f"Response found: {response_id}")
            else:
                logger.debug(f"Response not found: {response_id}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error finding response by ID {response_id}: {e}")
            return None
    
    async def get_message_responses(self, message_id: uuid.UUID) -> List[ChatResponse]:
        """
        Get all responses for a message
        
        Args:
            message_id: Message's unique identifier
            
        Returns:
            List of ChatResponse objects
        """
        try:
            stmt = (
                select(ChatResponse)
                .where(ChatResponse.message_id == message_id)
                .order_by(ChatResponse.created_at.desc())
            )
            
            result = await self.session.execute(stmt)
            responses = result.scalars().all()
            
            logger.debug(f"Retrieved {len(responses)} responses for message {message_id}")
            return list(responses)
            
        except Exception as e:
            logger.error(f"Error getting message responses for {message_id}: {e}")
            return []
    
    async def get_successful_responses(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatResponse]:
        """
        Get successful responses with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of successful ChatResponse objects
        """
        try:
            stmt = (
                select(ChatResponse)
                .where(ChatResponse.success == True)
                .order_by(ChatResponse.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            responses = result.scalars().all()
            
            logger.debug(f"Retrieved {len(responses)} successful responses")
            return list(responses)
            
        except Exception as e:
            logger.error(f"Error getting successful responses: {e}")
            return []
    
    async def get_failed_responses(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ChatResponse]:
        """
        Get failed responses with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of failed ChatResponse objects
        """
        try:
            stmt = (
                select(ChatResponse)
                .where(ChatResponse.success == False)
                .order_by(ChatResponse.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            responses = result.scalars().all()
            
            logger.debug(f"Retrieved {len(responses)} failed responses")
            return list(responses)
            
        except Exception as e:
            logger.error(f"Error getting failed responses: {e}")
            return []
    
    async def count_responses(self, success_only: bool = False) -> int:
        """
        Count total number of responses
        
        Args:
            success_only: Whether to count only successful responses
            
        Returns:
            Total number of responses
        """
        try:
            stmt = select(func.count(ChatResponse.id))
            
            if success_only:
                stmt = stmt.where(ChatResponse.success == True)
            
            result = await self.session.execute(stmt)
            count = result.scalar()
            
            logger.debug(f"Response count: {count} (success_only={success_only})")
            return count or 0
            
        except Exception as e:
            logger.error(f"Error counting responses: {e}")
            return 0
    
    async def add_feedback(
        self,
        response_id: uuid.UUID,
        user_id: uuid.UUID,
        is_positive: bool,
        feedback_comment: Optional[str] = None
    ) -> bool:
        """
        Add user feedback to an existing response
        
        Args:
            response_id: Response's unique identifier
            user_id: User's unique identifier
            is_positive: True for thumbs up, False for thumbs down
            feedback_comment: Optional feedback comment
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If feedback already exists or response not found
        """
        try:
            # Check if feedback already exists
            existing_feedback = await self.get_response_with_user_feedback(response_id, user_id)
            if existing_feedback and existing_feedback.is_positive is not None:
                raise ValueError("Feedback already exists for this response from this user")
            
            # Update the response with feedback
            stmt = (
                update(ChatResponse)
                .where(ChatResponse.id == response_id)
                .values(
                    is_positive=is_positive,
                    feedback_comment=feedback_comment,
                    feedback_user_id=user_id,
                    feedback_created_at=utc_now(),
                    feedback_updated_at=utc_now()
                )
            )
            
            result = await self.session.execute(stmt)
            
            if result.rowcount > 0:
                logger.info(f"Feedback added to response: {response_id}")
                return True
            else:
                logger.warning(f"Response not found for feedback: {response_id}")
                raise ValueError("Response not found")
                
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Failed to add feedback to response {response_id}: {e}")
            await self.session.rollback()
            return False
    
    async def update_feedback(
        self,
        response_id: uuid.UUID,
        user_id: uuid.UUID,
        is_positive: bool,
        feedback_comment: Optional[str] = None
    ) -> bool:
        """
        Update existing feedback on a response
        
        Args:
            response_id: Response's unique identifier
            user_id: User's unique identifier
            is_positive: True for thumbs up, False for thumbs down
            feedback_comment: Optional feedback comment
            
        Returns:
            True if successful, False otherwise
        """
        try:
            stmt = (
                update(ChatResponse)
                .where(
                    and_(
                        ChatResponse.id == response_id,
                        ChatResponse.feedback_user_id == user_id
                    )
                )
                .values(
                    is_positive=is_positive,
                    feedback_comment=feedback_comment,
                    feedback_updated_at=utc_now()
                )
            )
            
            result = await self.session.execute(stmt)
            
            if result.rowcount > 0:
                logger.info(f"Feedback updated for response: {response_id}")
                return True
            else:
                logger.warning(f"No feedback found to update for response: {response_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update feedback for response {response_id}: {e}")
            await self.session.rollback()
            return False
    
    async def get_response_with_user_feedback(
        self,
        response_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[ChatResponse]:
        """
        Get response with user's feedback if it exists
        
        Args:
            response_id: Response's unique identifier
            user_id: User's unique identifier
            
        Returns:
            ChatResponse object with feedback if found, None otherwise
        """
        try:
            stmt = select(ChatResponse).where(
                and_(
                    ChatResponse.id == response_id,
                    or_(
                        ChatResponse.feedback_user_id == user_id,
                        ChatResponse.feedback_user_id.is_(None)
                    )
                )
            )
            result = await self.session.execute(stmt)
            response = result.scalar_one_or_none()
            
            if response:
                logger.debug(f"Response with user feedback found: {response_id}")
            else:
                logger.debug(f"Response with user feedback not found: {response_id}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting response with user feedback {response_id}: {e}")
            return None
    
    async def get_feedback_summary(
        self,
        response_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Get feedback summary statistics
        
        Args:
            response_id: Optional response filter
            
        Returns:
            Dictionary with feedback summary
        """
        try:
            stmt = select(ChatResponse).where(ChatResponse.is_positive.isnot(None))
            
            if response_id:
                stmt = stmt.where(ChatResponse.id == response_id)
            
            result = await self.session.execute(stmt)
            responses_with_feedback = result.scalars().all()
            
            total_feedback = len(responses_with_feedback)
            positive_feedback = len([r for r in responses_with_feedback if r.is_positive])
            negative_feedback = total_feedback - positive_feedback
            
            positive_percentage = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
            negative_percentage = (negative_feedback / total_feedback * 100) if total_feedback > 0 else 0
            
            # Count feedback with comments
            feedback_with_comments = len([r for r in responses_with_feedback if r.feedback_comment])
            
            summary = {
                "total_feedback": total_feedback,
                "positive_feedback": positive_feedback,
                "negative_feedback": negative_feedback,
                "positive_percentage": round(positive_percentage, 2),
                "negative_percentage": round(negative_percentage, 2),
                "feedback_with_comments": feedback_with_comments
            }
            
            logger.debug(f"Generated feedback summary: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating feedback summary: {e}")
            return {
                "total_feedback": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
                "positive_percentage": 0,
                "negative_percentage": 0,
                "feedback_with_comments": 0,
                "error": str(e)
            }
