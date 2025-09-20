"""
Service for reconstructing historical assistant messages from stored chunks
Assembles streaming message chunks back into complete messages for conversation history
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.message_chunk_repository import MessageChunkRepository
from ..repositories.chat_repository import ChatMessageRepository
from ..database.models import MessageChunk, MessageChunkType, ChatMessage, MessageType
from collections import defaultdict

logger = logging.getLogger(__name__)


class MessageReconstructionService:
    """
    Service for reconstructing complete assistant messages from stored chunks
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chunk_repo = MessageChunkRepository(session)
        self.message_repo = ChatMessageRepository(session)
    
    async def reconstruct_message(self, message_id: str) -> Dict[str, Any]:
        """
        Reconstruct a complete assistant message from its stored chunks
        
        Args:
            message_id: UUID of the message to reconstruct
            
        Returns:
            Dictionary containing the reconstructed message data
        """
        try:
            # Get the message record
            message = await self.message_repo.get_message_by_id(message_id)
            if not message:
                return {
                    "success": False,
                    "error": "Message not found",
                    "message_id": message_id
                }
            
            # Only reconstruct assistant messages
            if message.message_type != MessageType.ASSISTANT:
                return {
                    "success": False,
                    "error": "Only assistant messages can be reconstructed from chunks",
                    "message_id": message_id
                }
            
            # Get all chunks for this message
            chunks = await self.chunk_repo.get_message_chunks(message_id)
            if not chunks:
                return {
                    "success": False,
                    "error": "No chunks found for message",
                    "message_id": message_id
                }
            
            # Reconstruct the complete message
            reconstructed_chunks = await self._assemble_chunks(chunks)
            
            # Build the complete message structure
            reconstructed_message = {
                "id": str(message.id),
                "message_type": "assistant", 
                "content": message.content,
                "created_at": message.created_at.isoformat() if message.created_at else None,
                "superclient": message.superclient,
                "chunks": reconstructed_chunks,
                "chunk_summary": {
                    "total_chunks": len(reconstructed_chunks),
                    "chunk_types": [chunk["message_type"] for chunk in reconstructed_chunks],
                    "has_sql": any(chunk["message_type"] == "sql" for chunk in reconstructed_chunks),
                    "has_data": any(chunk["message_type"] == "data" for chunk in reconstructed_chunks),
                    "has_chart": any(chunk["message_type"] == "chart" for chunk in reconstructed_chunks),
                    "has_insights": any(chunk["message_type"] == "insights" for chunk in reconstructed_chunks)
                }
            }
            
            logger.info(f"✅ Successfully reconstructed message {message_id} with {len(reconstructed_chunks)} chunks")
            
            return {
                "success": True,
                "message": reconstructed_message,
                "message_id": message_id
            }
            
        except Exception as e:
            logger.error(f"Failed to reconstruct message {message_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message_id": message_id
            }
    
    async def reconstruct_conversation_messages(self, conversation_id: str) -> Dict[str, Any]:
        """
        Reconstruct all assistant messages in a conversation that have stored chunks
        
        Args:
            conversation_id: UUID of the conversation
            
        Returns:
            Dictionary containing all reconstructed messages
        """
        try:
            # Get all messages in conversation that have chunks
            messages_with_chunks = await self.chunk_repo.get_messages_with_chunks(conversation_id)
            
            reconstructed_messages = []
            reconstruction_errors = []
            
            for message in messages_with_chunks:
                if message.message_type == MessageType.ASSISTANT:
                    # Reconstruct this assistant message
                    result = await self.reconstruct_message(str(message.id))
                    
                    if result["success"]:
                        reconstructed_messages.append(result["message"])
                    else:
                        reconstruction_errors.append({
                            "message_id": str(message.id),
                            "error": result["error"]
                        })
                        logger.warning(f"⚠️ Failed to reconstruct message {message.id}: {result['error']}")
            
            logger.info(f"✅ Reconstructed {len(reconstructed_messages)} assistant messages for conversation {conversation_id}")
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "messages": reconstructed_messages,
                "total_messages": len(reconstructed_messages),
                "errors": reconstruction_errors
            }
            
        except Exception as e:
            logger.error(f"Failed to reconstruct conversation messages {conversation_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "conversation_id": conversation_id
            }
    
    async def _assemble_chunks(self, chunks: List[MessageChunk]) -> List[Dict[str, Any]]:
        """
        Assemble chunks into complete message chunks, merging split data chunks
        
        Args:
            chunks: List of MessageChunk records for a message
            
        Returns:
            List of complete chunk data ready for frontend
        """
        # Group chunks by type and sequence
        chunks_by_type_sequence = defaultdict(list)
        
        for chunk in chunks:
            key = (chunk.chunk_type, chunk.chunk_sequence)
            chunks_by_type_sequence[key].append(chunk)
        
        assembled_chunks = []
        
        # Process each chunk type/sequence group
        for (chunk_type, chunk_sequence), chunk_group in chunks_by_type_sequence.items():
            if len(chunk_group) == 1 and chunk_group[0].total_data_chunks == 1:
                # Single chunk, no data splitting
                assembled_chunks.append(chunk_group[0].chunk_data)
            else:
                # Multiple data chunks need to be merged
                merged_chunk = await self._merge_data_chunks(chunk_group, chunk_type)
                if merged_chunk:
                    assembled_chunks.append(merged_chunk)
        
        # Sort by original chunk sequence
        assembled_chunks.sort(key=lambda x: x.get("sequence", 0))
        
        return assembled_chunks
    
    async def _merge_data_chunks(
        self, 
        chunk_group: List[MessageChunk], 
        chunk_type: MessageChunkType
    ) -> Optional[Dict[str, Any]]:
        """
        Merge multiple data chunks back into a single complete chunk
        
        Args:
            chunk_group: List of MessageChunk records that were split
            chunk_type: Type of chunk being merged
            
        Returns:
            Complete merged chunk data or None if merging fails
        """
        try:
            # Sort chunks by data_chunk_index
            sorted_chunks = sorted(chunk_group, key=lambda x: x.data_chunk_index)
            
            # Validate chunk integrity
            expected_total = sorted_chunks[0].total_data_chunks
            if len(sorted_chunks) != expected_total:
                logger.error(f"Chunk count mismatch: expected {expected_total}, got {len(sorted_chunks)}")
                return None
            
            for i, chunk in enumerate(sorted_chunks):
                if chunk.data_chunk_index != i:
                    logger.error(f"Chunk index mismatch: expected {i}, got {chunk.data_chunk_index}")
                    return None
            
            # Start with the first chunk as the base
            base_chunk_data = sorted_chunks[0].chunk_data.copy()
            
            if chunk_type == MessageChunkType.data:
                # Merge result_data arrays
                merged_data = []
                for chunk in sorted_chunks:
                    chunk_data = chunk.chunk_data.get("data", {}).get("result_data", [])
                    merged_data.extend(chunk_data)
                
                # Update the base chunk with merged data
                if "data" in base_chunk_data:
                    base_chunk_data["data"]["result_data"] = merged_data
                
                logger.info(f"Merged {len(sorted_chunks)} data chunks into {len(merged_data)} total records")
                
            elif chunk_type == MessageChunkType.chart:
                # Merge chart data values
                merged_chart_data = []
                for chunk in sorted_chunks:
                    chunk_config = chunk.chunk_data.get("data", {}).get("chart_config", {})
                    if "vega_spec" in chunk_config and "data" in chunk_config["vega_spec"]:
                        chart_values = chunk_config["vega_spec"]["data"].get("values", [])
                        merged_chart_data.extend(chart_values)
                
                # Update the base chunk with merged chart data
                if ("data" in base_chunk_data and 
                    "chart_config" in base_chunk_data["data"] and
                    "vega_spec" in base_chunk_data["data"]["chart_config"]):
                    
                    base_chart_config = base_chunk_data["data"]["chart_config"]
                    if "data" not in base_chart_config["vega_spec"]:
                        base_chart_config["vega_spec"]["data"] = {}
                    base_chart_config["vega_spec"]["data"]["values"] = merged_chart_data
                
                logger.info(f"Merged {len(sorted_chunks)} chart chunks into {len(merged_chart_data)} total data points")
            
            return base_chunk_data
            
        except Exception as e:
            logger.error(f"Failed to merge data chunks: {e}")
            return None
    
    async def get_chunk_summary(self, message_id: str) -> Dict[str, Any]:
        """
        Get a summary of chunks stored for a message (for debugging/monitoring)
        
        Args:
            message_id: UUID of the message
            
        Returns:
            Dictionary containing chunk summary information
        """
        try:
            chunks = await self.chunk_repo.get_message_chunks(message_id)
            
            if not chunks:
                return {
                    "message_id": message_id,
                    "total_chunks": 0,
                    "chunk_types": [],
                    "has_split_data": False
                }
            
            # Analyze chunks
            chunk_counts = await self.chunk_repo.count_chunks_by_type(message_id)
            has_split_data = any(chunk.total_data_chunks > 1 for chunk in chunks)
            total_data_chunks = sum(chunk.total_data_chunks for chunk in chunks)
            
            return {
                "message_id": message_id,
                "total_chunks": len(chunks),
                "total_data_chunks": total_data_chunks,
                "chunk_types": list(chunk_counts.keys()),
                "chunk_counts": chunk_counts,
                "has_split_data": has_split_data,
                "chunks": [
                    {
                        "type": chunk.chunk_type.value,
                        "sequence": chunk.chunk_sequence,
                        "data_chunk_index": chunk.data_chunk_index,
                        "total_data_chunks": chunk.total_data_chunks,
                        "created_at": chunk.created_at.isoformat() if chunk.created_at else None
                    }
                    for chunk in chunks
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get chunk summary for message {message_id}: {e}")
            return {
                "message_id": message_id,
                "error": str(e)
            }
