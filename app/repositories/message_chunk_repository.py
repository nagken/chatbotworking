"""
Repository for MessageChunk database operations
Handles CRUD operations for storing and retrieving streaming message chunks
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from ..database.models import MessageChunk, MessageChunkType, ChatMessage
from ..utils.datetime_utils import utc_now
import json

logger = logging.getLogger(__name__)


class MessageChunkRepository:
    """
    Repository for managing MessageChunk records from streaming responses
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_message_chunk(
        self,
        message_id: str,
        chunk_type: MessageChunkType,
        chunk_sequence: int,
        chunk_data: Dict[str, Any],
        data_chunk_index: int = 0,
        total_data_chunks: int = 1
    ) -> MessageChunk:
        """
        Create a new MessageChunk record
        
        Args:
            message_id: UUID of the associated message
            chunk_type: Type of chunk (sql, data, chart, insights)
            chunk_sequence: Order this chunk was received during streaming
            chunk_data: Complete transformed chunk data ready for frontend
            data_chunk_index: Index for splitting large data (mainly for data/chart types)
            total_data_chunks: Total number of data chunks for this chunk_type
            
        Returns:
            Created MessageChunk instance
        """
        try:
            # Log chunk size for debugging
            chunk_json = json.dumps(chunk_data)
            chunk_size = len(chunk_json.encode('utf-8'))
            logger.debug(f"Creating MessageChunk {chunk_type.value} seq={chunk_sequence} data_chunk={data_chunk_index}/{total_data_chunks} with {chunk_size} bytes")
            
            # Warn for chunks approaching PostgreSQL btree v4 index size limit (2704 bytes)
            if chunk_size > 2500:  # Safety warning threshold as documented in postgresql-index-size-fix.md
                logger.warning(f"Large chunk detected: {chunk_size} bytes for {chunk_type.value} chunk {chunk_sequence} (PostgreSQL btree v4 limit is 2704 bytes)")
            
            message_chunk = MessageChunk(
                message_id=message_id,
                chunk_type=chunk_type,
                chunk_sequence=chunk_sequence,
                chunk_data=chunk_data,
                data_chunk_index=data_chunk_index,
                total_data_chunks=total_data_chunks
            )
            
            self.session.add(message_chunk)
            await self.session.flush()
            
            logger.info(f"Created MessageChunk {chunk_type.value} seq={chunk_sequence} data_chunk={data_chunk_index}/{total_data_chunks} for message {message_id}")
            return message_chunk
            
        except Exception as e:
            logger.error(f"Failed to create MessageChunk: {e}")
            # Log additional details for debugging
            if "ProgramLimitExceededError" in str(e) or "index row requires" in str(e):
                logger.error(f"Index size limit error detected. Chunk size: {chunk_size if 'chunk_size' in locals() else 'unknown'} bytes")
            raise
    
    async def get_message_chunks(
        self, 
        message_id: str,
        chunk_type: Optional[MessageChunkType] = None
    ) -> List[MessageChunk]:
        """
        Get all chunks for a specific message, optionally filtered by chunk type
        
        Args:
            message_id: UUID of the message
            chunk_type: Optional filter by chunk type
            
        Returns:
            List of MessageChunk records ordered by chunk_sequence, then data_chunk_index
        """
        try:
            stmt = (
                select(MessageChunk)
                .where(MessageChunk.message_id == message_id)
            )
            
            if chunk_type:
                stmt = stmt.where(MessageChunk.chunk_type == chunk_type)
                
            stmt = stmt.order_by(MessageChunk.chunk_sequence, MessageChunk.data_chunk_index)
            
            result = await self.session.execute(stmt)
            chunks = result.scalars().all()
            
            logger.info(f"Retrieved {len(chunks)} chunks for message {message_id}" + (f" (type: {chunk_type.value})" if chunk_type else ""))
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to get MessageChunks for message {message_id}: {e}")
            raise
    
    async def get_chunk_by_id(self, chunk_id: str) -> Optional[MessageChunk]:
        """
        Get a specific MessageChunk by ID
        
        Args:
            chunk_id: UUID of the chunk
            
        Returns:
            MessageChunk instance or None if not found
        """
        try:
            stmt = select(MessageChunk).where(MessageChunk.id == chunk_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get MessageChunk {chunk_id}: {e}")
            raise
    
    async def delete_message_chunks(self, message_id: str) -> int:
        """
        Delete all MessageChunk records for a specific message
        
        Args:
            message_id: UUID of the message
            
        Returns:
            Number of records deleted
        """
        try:
            stmt = delete(MessageChunk).where(MessageChunk.message_id == message_id)
            result = await self.session.execute(stmt)
            deleted_count = result.rowcount
            
            logger.info(f"Deleted {deleted_count} MessageChunk records for message {message_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete MessageChunk records for message {message_id}: {e}")
            raise
    
    async def get_messages_with_chunks(self, conversation_id: str) -> List[ChatMessage]:
        """
        Get all ChatMessages in a conversation that have associated chunks
        Useful for reconstructing conversation history
        
        Args:
            conversation_id: UUID of the conversation
            
        Returns:
            List of ChatMessage records with their chunks loaded
        """
        try:
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .options(selectinload(ChatMessage.message_chunks))
                .order_by(ChatMessage.created_at)
            )
            
            result = await self.session.execute(stmt)
            messages = result.scalars().all()
            
            # Filter to only messages that have chunks
            messages_with_chunks = [msg for msg in messages if msg.message_chunks]
            
            logger.info(f"Retrieved {len(messages_with_chunks)} messages with chunks for conversation {conversation_id}")
            return messages_with_chunks
            
        except Exception as e:
            logger.error(f"Failed to get messages with chunks for conversation {conversation_id}: {e}")
            raise
    
    async def count_chunks_by_type(self, message_id: str) -> Dict[str, int]:
        """
        Count chunks by type for a specific message
        
        Args:
            message_id: UUID of the message
            
        Returns:
            Dictionary with chunk type counts
        """
        try:
            stmt = select(MessageChunk).where(MessageChunk.message_id == message_id)
            result = await self.session.execute(stmt)
            chunks = result.scalars().all()
            
            counts = {}
            for chunk in chunks:
                chunk_type = chunk.chunk_type.value
                counts[chunk_type] = counts.get(chunk_type, 0) + 1
            
            logger.info(f"Chunk counts for message {message_id}: {counts}")
            return counts
            
        except Exception as e:
            logger.error(f"Failed to count chunks for message {message_id}: {e}")
            raise
    
    async def get_chunk_data_size_estimate(self, message_id: str) -> int:
        """
        Estimate total size of chunk data for a message (for debugging)
        
        Args:
            message_id: UUID of the message
            
        Returns:
            Estimated size in bytes
        """
        try:
            chunks = await self.get_message_chunks(message_id)
            total_size = 0
            
            for chunk in chunks:
                chunk_json = json.dumps(chunk.chunk_data)
                chunk_size = len(chunk_json.encode('utf-8'))
                total_size += chunk_size
            
            logger.debug(f"Estimated total chunk data size for message {message_id}: {total_size} bytes")
            return total_size
            
        except Exception as e:
            logger.error(f"Failed to estimate chunk data size for message {message_id}: {e}")
            raise
