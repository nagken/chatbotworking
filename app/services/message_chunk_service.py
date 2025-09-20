"""
Service for managing message chunks from streaming responses
Handles storage of transformed chunks during streaming with data chunking for large datasets
"""

import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.message_chunk_repository import MessageChunkRepository
from ..database.models import MessageChunkType
import asyncio

logger = logging.getLogger(__name__)


class MessageChunkService:
    """
    Service for storing and managing streaming message chunks
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chunk_repo = MessageChunkRepository(session)
        self.max_chunk_size = 2000  # Maximum bytes per chunk to prevent PostgreSQL btree v4 index size limit (2704 bytes)
    
    async def store_transformed_chunk(
        self,
        message_id: str,
        chunk_sequence: int,
        transformed_chunk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store a transformed chunk from StreamingMessageTransformer
        Handles data chunking if the chunk is too large
        
        Args:
            message_id: UUID of the message
            chunk_sequence: Order this chunk was received during streaming  
            transformed_chunk: Complete transformed chunk from StreamingMessageTransformer
            
        Returns:
            Dictionary containing operation status and details
        """
        try:
            # Extract chunk type and data from transformed chunk
            chunk_type_str = transformed_chunk.get("message_type")
            chunk_data = transformed_chunk.get("data", {})
            
            if not chunk_type_str:
                return {
                    "success": False,
                    "error": "No message_type found in transformed chunk"
                }
            
            # Map string to enum
            try:
                chunk_type = MessageChunkType(chunk_type_str)
            except ValueError:
                logger.warning(f"Unknown chunk type: {chunk_type_str}, storing as insights")
                chunk_type = MessageChunkType.insights
            
            # Handle data chunking based on chunk type
            if chunk_type in [MessageChunkType.data, MessageChunkType.chart]:
                # These chunk types might have large data that needs splitting
                storage_result = await self._store_large_data_chunk(
                    message_id, chunk_type, chunk_sequence, transformed_chunk, chunk_data
                )
            else:
                # SQL and Insights chunks are typically small, store directly
                storage_result = await self._store_single_chunk(
                    message_id, chunk_type, chunk_sequence, transformed_chunk
                )
            
            if storage_result["success"]:
                logger.info(f"Successfully stored {chunk_type.value} chunk seq={chunk_sequence} for message {message_id}")
            
            return storage_result
            
        except Exception as e:
            logger.error(f"Failed to store transformed chunk for message {message_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunk_type": chunk_type_str if 'chunk_type_str' in locals() else 'unknown',
                "chunk_sequence": chunk_sequence
            }
    
    async def _store_single_chunk(
        self,
        message_id: str,
        chunk_type: MessageChunkType,
        chunk_sequence: int,
        chunk_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store a single chunk without data splitting
        
        Args:
            message_id: UUID of the message
            chunk_type: Type of chunk
            chunk_sequence: Order this chunk was received
            chunk_data: Complete chunk data
            
        Returns:
            Dictionary containing operation result
        """
        try:
            # Check chunk size
            chunk_json = json.dumps(chunk_data)
            chunk_size = len(chunk_json.encode('utf-8'))
            
            # Warn for chunks approaching PostgreSQL index size limit
            if chunk_size > 2500:  # Safety warning threshold as documented in postgresql-index-size-fix.md
                logger.warning(f"Large chunk detected: {chunk_size} bytes for {chunk_type.value} chunk (PostgreSQL btree v4 limit is 2704 bytes)")
            elif chunk_size > self.max_chunk_size:
                logger.warning(f"Single chunk {chunk_type.value} is large ({chunk_size} bytes) but storing as-is")
            
            # Store the chunk
            await self.chunk_repo.create_message_chunk(
                message_id=message_id,
                chunk_type=chunk_type,
                chunk_sequence=chunk_sequence,
                chunk_data=chunk_data,
                data_chunk_index=0,
                total_data_chunks=1
            )
            
            return {
                "success": True,
                "chunks_stored": 1,
                "total_size": chunk_size
            }
            
        except Exception as e:
            logger.error(f"Failed to store single chunk: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _store_large_data_chunk(
        self,
        message_id: str,
        chunk_type: MessageChunkType,
        chunk_sequence: int,
        transformed_chunk: Dict[str, Any],
        chunk_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store a data or chart chunk with potential data splitting for large datasets
        
        Args:
            message_id: UUID of the message
            chunk_type: DATA or CHART chunk type
            chunk_sequence: Order this chunk was received
            transformed_chunk: Complete transformed chunk
            chunk_data: Data portion of the chunk
            
        Returns:
            Dictionary containing operation result
        """
        try:
            # Check if this chunk contains large data that needs splitting
            large_data_field = None
            large_data = None
            
            if chunk_type == MessageChunkType.data and "result_data" in chunk_data:
                large_data_field = "result_data"
                large_data = chunk_data["result_data"]
            elif chunk_type == MessageChunkType.chart and "chart_config" in chunk_data:
                # For charts, check if the vega_spec contains large data
                chart_config = chunk_data["chart_config"]
                if isinstance(chart_config, dict) and "vega_spec" in chart_config:
                    vega_spec = chart_config["vega_spec"]
                    if isinstance(vega_spec, dict) and "data" in vega_spec and "values" in vega_spec["data"]:
                        large_data_field = "chart_data_values"
                        large_data = vega_spec["data"]["values"]
            
            # If no large data found, store as single chunk
            if not large_data or not isinstance(large_data, list):
                return await self._store_single_chunk(message_id, chunk_type, chunk_sequence, transformed_chunk)
            
            # Check if data needs chunking
            large_data_json = json.dumps(large_data)
            data_size = len(large_data_json.encode('utf-8'))
            
            if data_size <= self.max_chunk_size:
                # Data is small enough, store as single chunk
                return await self._store_single_chunk(message_id, chunk_type, chunk_sequence, transformed_chunk)
            
            # Data is too large, need to split it
            logger.info(f"Large {chunk_type.value} data detected ({data_size} bytes), splitting into chunks")
            
            # Split the data into smaller chunks
            data_chunks = self._split_large_data(large_data, self.max_chunk_size)
            total_data_chunks = len(data_chunks)
            
            # Store each data chunk
            chunks_stored = 0
            for data_chunk_index, data_chunk in enumerate(data_chunks):
                # Create a copy of the original chunk with just this data chunk
                chunk_copy = transformed_chunk.copy()
                chunk_data_copy = chunk_data.copy()
                
                if chunk_type == MessageChunkType.data:
                    chunk_data_copy["result_data"] = data_chunk
                elif chunk_type == MessageChunkType.chart:
                    # Update the chart config with just this data chunk
                    chart_config_copy = chart_config.copy()
                    vega_spec_copy = vega_spec.copy()
                    vega_data_copy = vega_spec["data"].copy()
                    vega_data_copy["values"] = data_chunk
                    vega_spec_copy["data"] = vega_data_copy
                    chart_config_copy["vega_spec"] = vega_spec_copy
                    chunk_data_copy["chart_config"] = chart_config_copy
                
                chunk_copy["data"] = chunk_data_copy
                
                # Store this data chunk
                await self.chunk_repo.create_message_chunk(
                    message_id=message_id,
                    chunk_type=chunk_type,
                    chunk_sequence=chunk_sequence,
                    chunk_data=chunk_copy,
                    data_chunk_index=data_chunk_index,
                    total_data_chunks=total_data_chunks
                )
                
                chunks_stored += 1
            
            logger.info(f"Split large {chunk_type.value} data into {chunks_stored} chunks for message {message_id}")
            
            return {
                "success": True,
                "chunks_stored": chunks_stored,
                "total_size": data_size,
                "data_was_split": True
            }
            
        except Exception as e:
            logger.error(f"Failed to store large data chunk: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _split_large_data(self, data: List[Any], max_chunk_size: int, max_rows: int = 150) -> List[List[Any]]:
        """
        Split large data array into smaller chunks based on size and row count
        Uses the same limits as documented in postgresql-index-size-fix.md
        
        Args:
            data: Large data array to split
            max_chunk_size: Maximum bytes per chunk
            max_rows: Maximum rows per chunk (default 150 from documentation)
            
        Returns:
            List of data chunks
        """
        if not data:
            return []
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for item in data:
            # Estimate size of this item
            item_json = json.dumps(item)
            item_size = len(item_json.encode('utf-8'))
            
            # Check if adding this item would exceed either size or row limits
            would_exceed_size = (current_size + item_size) > max_chunk_size
            would_exceed_rows = len(current_chunk) >= max_rows
            
            if (would_exceed_size or would_exceed_rows) and current_chunk:
                # Save current chunk and start a new one
                chunks.append(current_chunk)
                current_chunk = []
                current_size = 0
            
            # Add item to current chunk
            current_chunk.append(item)
            current_size += item_size
            
            # If a single item is larger than max size, still include it
            # (PostgreSQL will handle it as best as possible, but may fail if indexed)
            if item_size > max_chunk_size:
                logger.warning(f"Single data item exceeds max chunk size: {item_size} bytes (PostgreSQL btree v4 limit is 2704 bytes)")
        
        # Add final chunk if it has data
        if current_chunk:
            chunks.append(current_chunk)
        
        logger.info(f"Split {len(data)} data items into {len(chunks)} chunks (max {max_chunk_size} bytes, {max_rows} rows per chunk)")
        return chunks
    
    async def store_chunks_with_error_handling(
        self,
        message_id: str,
        chunks_to_store: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Store multiple chunks with error handling - continue storing even if some fail
        This supports the requirement to continue streaming even if storage fails
        
        Args:
            message_id: UUID of the message
            chunks_to_store: List of (chunk_sequence, transformed_chunk) pairs
            
        Returns:
            Dictionary with overall results
        """
        results = {
            "success": True,
            "total_chunks": len(chunks_to_store),
            "chunks_stored": 0,
            "chunks_failed": 0,
            "errors": []
        }
        
        for chunk_info in chunks_to_store:
            chunk_sequence = chunk_info["chunk_sequence"]
            transformed_chunk = chunk_info["transformed_chunk"]
            
            try:
                store_result = await self.store_transformed_chunk(
                    message_id=message_id,
                    chunk_sequence=chunk_sequence,
                    transformed_chunk=transformed_chunk
                )
                
                if store_result["success"]:
                    results["chunks_stored"] += store_result.get("chunks_stored", 1)
                else:
                    results["chunks_failed"] += 1
                    results["errors"].append({
                        "chunk_sequence": chunk_sequence,
                        "error": store_result.get("error", "Unknown error")
                    })
                    
            except Exception as e:
                logger.error(f"Failed to store chunk {chunk_sequence}: {e}")
                results["chunks_failed"] += 1
                results["errors"].append({
                    "chunk_sequence": chunk_sequence,
                    "error": str(e)
                })
        
        # Mark as failed if more than half the chunks failed to store
        if results["chunks_failed"] > results["total_chunks"] // 2:
            results["success"] = False
        
        logger.info(f"Stored {results['chunks_stored']} chunks, {results['chunks_failed']} failed for message {message_id}")
        return results
