"""
Message service layer
Handles business logic for message operations
"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from ..models.schemas import MessageHistoryResponse, MessageDetail
from ..database.models import User, MessageType
from ..repositories.chat_repository import ChatConversationRepository, ChatMessageRepository
from ..services.message_reconstruction_service import MessageReconstructionService
from ..utils.chat_response_extractor import format_messages_for_history

logger = logging.getLogger(__name__)


class MessageService:
    """Service layer for message business logic"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversation_repo = ChatConversationRepository(session)
        self.message_repo = ChatMessageRepository(session)
        self.reconstruction_service = MessageReconstructionService(session)
    
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
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        user: User
    ) -> MessageHistoryResponse:
        """
        Get all messages in a conversation for the frontend
        
        Args:
            conversation_id: Conversation ID string
            user: Current user
            
        Returns:
            MessageHistoryResponse with complete conversation history
            
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
            
            # Get all messages in the conversation
            messages = await self.message_repo.get_conversation_messages(conversation.id)
            
            # Format messages for response, with chunk reconstruction for assistant messages
            formatted_messages = await self._format_messages_with_reconstruction(messages)
            
            return MessageHistoryResponse(
                conversation_id=conversation_id,
                title=conversation.title or "Untitled Conversation",
                messages=formatted_messages,
                total_messages=len(formatted_messages),
                created_at=conversation.created_at,
                updated_at=conversation.updated_at
            )
            
        except (ValueError, PermissionError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to get messages for conversation {conversation_id}: {e}")
            raise
    
    async def get_recent_conversation_messages(
        self,
        conversation_id: str,
        user: User,
        limit: int = 50
    ) -> MessageHistoryResponse:
        """
        Get recent messages in a conversation (for performance optimization)
        
        Args:
            conversation_id: Conversation ID string
            user: Current user
            limit: Maximum number of recent messages to return
            
        Returns:
            MessageHistoryResponse with recent conversation history
            
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
            
            # Get recent messages in the conversation
            messages = await self.message_repo.get_recent_conversation_messages(conversation.id, limit)
            
            # Format messages for response
            formatted_messages = format_messages_for_history(messages)
            
            return MessageHistoryResponse(
                conversation_id=conversation_id,
                title=conversation.title or "Untitled Conversation",
                messages=formatted_messages,
                total_messages=len(messages),
                created_at=conversation.created_at,
                updated_at=conversation.updated_at
            )
            
        except (ValueError, PermissionError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to get recent messages for conversation {conversation_id}: {e}")
            raise
    
    async def get_last_message_pair(
        self,
        conversation_id: str,
        user: User
    ) -> tuple[str, str, str]:
        """
        Get the last message pair for conversation summary
        
        Args:
            conversation_id: Conversation ID string
            user: Current user
            
        Returns:
            Tuple of (user_message, assistant_message, timestamp) or (None, None, None)
            
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
            
            # Get the last message pair
            last_user_message, last_assistant_message = await self.message_repo.get_last_message_pair(conversation.id)
            
            if last_user_message:
                return (
                    last_user_message.content,
                    last_assistant_message.content if last_assistant_message else None,
                    str(last_user_message.created_at)
                )
            else:
                return None, None, None
                
        except (ValueError, PermissionError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to get last message pair for conversation {conversation_id}: {e}")
            raise
    
    async def get_conversation_message_count(
        self,
        conversation_id: str,
        user: User
    ) -> int:
        """
        Get the total number of messages in a conversation
        
        Args:
            conversation_id: Conversation ID string
            user: Current user
            
        Returns:
            Total message count
            
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
            
            # Count messages in conversation
            return await self.message_repo.count_conversation_messages(conversation.id)
                
        except (ValueError, PermissionError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Failed to get message count for conversation {conversation_id}: {e}")
            raise
    
    async def _format_messages_with_reconstruction(self, messages: List) -> List[MessageDetail]:
        """
        Format messages for response, reconstructing assistant messages from chunks where available
        
        Args:
            messages: List of ChatMessage records from database
            
        Returns:
            List of MessageDetail objects for frontend
        """
        formatted_messages = []
        
        for message in messages:
            if message.message_type == MessageType.USER:
                # User messages are simple, no reconstruction needed
                formatted_message = MessageDetail(
                    id=str(message.id),
                    message_type="user",
                    content=message.content,
                    created_at=message.created_at,
                    superclient=message.superclient
                )
                formatted_messages.append(formatted_message)
                
            elif message.message_type == MessageType.ASSISTANT:
                # Try to reconstruct assistant message from chunks
                reconstruction_result = await self.reconstruction_service.reconstruct_message(str(message.id))
                
                if reconstruction_result["success"]:
                    # Successfully reconstructed from chunks
                    reconstructed_message = reconstruction_result["message"]
                    
                    # Convert to MessageDetail format for frontend
                    formatted_message = MessageDetail(
                        id=reconstructed_message["id"],
                        message_type=reconstructed_message["message_type"],
                        content=reconstructed_message["content"],
                        created_at=message.created_at,  # Use original timestamp from database
                        superclient=reconstructed_message["superclient"],
                        # Add reconstructed chunk data
                        chunks=reconstructed_message["chunks"],
                        chunk_summary=reconstructed_message["chunk_summary"],
                        # Legacy fields for backward compatibility (if needed)
                        sql_query=self._extract_chunk_data(reconstructed_message["chunks"], "sql", "sql_query"),
                        chart_config=self._extract_chunk_data(reconstructed_message["chunks"], "chart", "chart_config"),
                        ai_insights=self._extract_chunk_data(reconstructed_message["chunks"], "insights", "ai_insights"),
                        result_data=self._extract_chunk_data(reconstructed_message["chunks"], "data", "result_data"),
                        result_schema=self._extract_chunk_data(reconstructed_message["chunks"], "data", "result_schema"),
                        data_status="complete" if reconstructed_message["chunks"] else "no_chunks"
                    )
                    
                    logger.info(f"✅ Reconstructed assistant message {message.id} with {len(reconstructed_message['chunks'])} chunks")
                else:
                    # Reconstruction failed, use basic message data
                    logger.warning(f"⚠️ Failed to reconstruct assistant message {message.id}: {reconstruction_result.get('error', 'Unknown error')}")
                    
                    formatted_message = MessageDetail(
                        id=str(message.id),
                        message_type="assistant", 
                        content=message.content,
                        created_at=message.created_at,
                        superclient=message.superclient,
                        data_status="reconstruction_failed",
                        data_message=f"Unable to load message data: {reconstruction_result.get('error', 'Unknown error')}"
                    )
                
                formatted_messages.append(formatted_message)
        
        return formatted_messages
    
    def _extract_chunk_data(self, chunks: List[Dict], chunk_type: str, field_name: str) -> Any:
        """
        Extract specific data from chunks for backward compatibility
        
        Args:
            chunks: List of reconstructed chunks
            chunk_type: Type of chunk to look for (sql, data, chart, insights)
            field_name: Field name to extract from chunk data
            
        Returns:
            Extracted data or None if not found
        """
        try:
            for chunk in chunks:
                if chunk.get("message_type") == chunk_type:
                    chunk_data = chunk.get("data", {})
                    if field_name in chunk_data:
                        return chunk_data[field_name]
            return None
            
        except Exception as e:
            logger.error(f"Error extracting {field_name} from {chunk_type} chunk: {e}")
            return None
