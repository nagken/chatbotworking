"""
Local Chat API Routes - Alternative to Vertex AI
Provides chat functionality using local document search without external AI APIs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
import json
import asyncio
import uuid
import re
from datetime import datetime

from ...models.schemas import ChatQuery, ChatResponse
from ...database.connection import get_db_session_dependency
from ...database.models import User
from ...services.local_search_service import LocalSearchService
from ...services.conversation_service import ConversationService
from ...services.message_service import MessageService
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize local search service
local_search_service = LocalSearchService()


@router.post("/local/stream", response_class=StreamingResponse)
async def chat_stream_local(
    request: ChatQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Stream chat responses using local search (no Vertex AI)
    """
    try:
        logger.info(f"🔍 Local chat stream request from user: {current_user.email}")
        logger.info(f"📝 Message: {request.message}")
        
        # Get or create conversation
        conversation_service = ConversationService(db)
        message_service = MessageService(db)
        
        conversation = None
        
        if request.conversation_id:
            try:
                conversation = await conversation_service.get_conversation(
                    conversation_id=request.conversation_id,
                    user=current_user
                )
                logger.info(f"📋 Using existing conversation: {request.conversation_id}")
            except Exception as e:
                logger.warning(f"Could not find conversation {request.conversation_id}: {e}")
        
        if not conversation:
            # Create new conversation with a smart title
            title = _generate_conversation_title(request.message)
            from ...models.schemas import ConversationCreate
            
            conversation_create = ConversationCreate(title=title)
            conversation = await conversation_service.create_conversation(
                user=current_user,
                request=conversation_create
            )
            logger.info(f"✨ Created new conversation: {conversation.id} - '{title}'")
        
        # Save user message
        try:
            user_message = await message_service.create_message(
                conversation_id=conversation.id,
                content=request.message,
                message_type="user",
                user=current_user
            )
            logger.info(f"💾 Saved user message: {user_message.id}")
        except Exception as e:
            logger.warning(f"Could not save user message: {e}")
        
        # Generate streaming response
        async def generate_stream():
            try:
                # Send conversation metadata first
                metadata = {
                    "type": "metadata",
                    "conversation_id": conversation.id,
                    "title": conversation.title,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(metadata)}\\n\\n"
                
                # Initialize response content
                full_response = ""
                
                # Stream the local search response
                async for chunk in local_search_service.stream_response(request.message):
                    full_response += chunk
                    
                    chunk_data = {
                        "type": "content",
                        "content": chunk,
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(chunk_data)}\\n\\n"
                
                # Get document suggestions for download links
                document_suggestions = local_search_service.get_document_suggestions(request.message)
                
                if document_suggestions:
                    # Add document links to response
                    document_links = "\\n\\n📚 **Related Documents:**\\n"
                    for filename in document_suggestions[:5]:  # Limit to 5 documents
                        document_links += f"• [{filename}](/documents/{filename})\\n"
                    
                    full_response += document_links
                    
                    links_data = {
                        "type": "content", 
                        "content": document_links,
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {links_data}\\n\\n"
                
                # Save assistant response
                try:
                    assistant_message = await message_service.create_message(
                        conversation_id=conversation.id,
                        content=full_response,
                        message_type="assistant",
                        user=current_user
                    )
                    logger.info(f"💾 Saved assistant message: {assistant_message.id}")
                except Exception as e:
                    logger.warning(f"Could not save assistant message: {e}")
                
                # Send completion signal
                completion_data = {
                    "type": "complete",
                    "conversation_id": conversation.id,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(completion_data)}\\n\\n"
                
            except Exception as e:
                logger.error(f"❌ Error in local chat stream: {e}")
                error_data = {
                    "type": "error",
                    "error": "Failed to process your request. Please try again.",
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(error_data)}\\n\\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Local chat stream error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )


@router.post("/local", response_model=ChatResponse)
async def chat_local(
    request: ChatQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Non-streaming chat response using local search (no Vertex AI)
    """
    try:
        logger.info(f"🔍 Local chat request from user: {current_user.email}")
        
        # Generate response using local search
        search_result = local_search_service.generate_response(request.message)
        
        # Get or create conversation
        conversation_service = ConversationService(db)
        conversation = None
        
        if request.conversation_id:
            try:
                conversation = await conversation_service.get_conversation(
                    conversation_id=request.conversation_id,
                    user=current_user
                )
            except Exception:
                pass
        
        if not conversation:
            title = _generate_conversation_title(request.message)
            from ...models.schemas import ConversationCreate
            
            conversation_create = ConversationCreate(title=title)
            conversation = await conversation_service.create_conversation(
                user=current_user,
                request=conversation_create
            )
        
        # Add document links if available
        response_content = search_result["response"]
        document_suggestions = local_search_service.get_document_suggestions(request.message)
        
        if document_suggestions:
            response_content += "\\n\\n📚 **Related Documents:**\\n"
            for filename in document_suggestions[:5]:
                response_content += f"• [{filename}](/documents/{filename})\\n"
        
        return ChatResponse(
            message=response_content,
            conversation_id=conversation.id,
            timestamp=datetime.now(),
            metadata={
                "search_method": "local",
                "query_type": search_result.get("query_type"),
                "confidence": search_result.get("confidence"),
                "document_count": len(search_result.get("documents", []))
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Local chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )


@router.get("/local/search")
async def search_documents_local(
    query: str,
    max_results: int = 10,
    current_user: User = Depends(get_current_user)
):
    """
    Search documents directly without chat context
    """
    try:
        documents = local_search_service.search_documents(query, max_results)
        
        return {
            "query": query,
            "results": documents,
            "count": len(documents),
            "search_method": "local"
        }
        
    except Exception as e:
        logger.error(f"❌ Local search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search documents"
        )


def _generate_conversation_title(message: str) -> str:
    """Generate a smart title for the conversation based on the first message"""
    # Clean and truncate message for title
    title = message.strip()
    
    # Remove question words and clean up
    title = re.sub(r'^(what|how|when|where|why|can|could|is|are|do|does)\\s+', '', title, flags=re.IGNORECASE)
    
    # Truncate and capitalize
    if len(title) > 50:
        title = title[:47] + "..."
    
    return title.capitalize() if title else "New Conversation"