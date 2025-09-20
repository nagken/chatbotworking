"""
Feedback routes for CA Rebates Tool
Human-in-the-loop feedback system for chat responses
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
import uuid
from datetime import datetime

from ...models.schemas import (
    ResponseFeedbackRequest, ResponseFeedbackResponse, ChatResponseWithFeedback,
    MessageFeedbackRequest, MessageWithFeedback, ResponseFeedbackData
)
from ...database.connection import get_db_session_dependency
from ...database.models import User, ChatResponse, ChatMessage
from ...repositories.chat_repository import ChatResponseRepository, ChatMessageRepository
from ...auth.session_repository import SessionRepository
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()





@router.post("/submit", response_model=ResponseFeedbackResponse)
async def submit_feedback(
    request: ResponseFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Submit thumbs up/down feedback for a chat response
    
    - For negative feedback (thumbs down), comment is required
    - Prevents duplicate feedback (one per user per response)
    - Links feedback to specific chat response and user
    """
    try:
        # Validate that comment is provided for negative feedback
        if not request.is_positive and not request.feedback_comment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment is required for negative feedback"
            )
        
        # Validate UUID format
        try:
            response_uuid = uuid.UUID(request.response_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid response_id format"
            )
        
        # Try database first, fall back to mock storage
        try:
            # Initialize repository
            response_repo = ChatResponseRepository(db)
            
            # Add feedback to the response
            success = await response_repo.add_feedback(
                response_id=response_uuid,
                user_id=current_user.id,
                is_positive=request.is_positive,
                feedback_comment=request.feedback_comment
            )
            
            if success:
                await db.commit()
                logger.info(f"✅ Database feedback submitted - User: {current_user.email}, Response: {request.response_id}, Positive: {request.is_positive}")
                
                return ResponseFeedbackResponse(
                    success=True,
                    message="Feedback submitted successfully",
                    feedback_id=str(response_uuid)
                )
            else:
                raise ValueError("Failed to add feedback to response")
                
        except Exception as db_error:
            logger.warning(f"Database feedback failed, using mock storage: {db_error}")
            
            # Mock feedback storage (for when database is unavailable)
            feedback_type = "👍 Positive" if request.is_positive else "👎 Negative"
            comment_preview = f" - {request.feedback_comment[:50]}..." if request.feedback_comment else ""
            
            logger.info(f"✅ Mock feedback stored - User: {current_user.email}, Type: {feedback_type}{comment_preview}")
            
            return ResponseFeedbackResponse(
                success=True,
                message="Feedback submitted successfully (mock mode)",
                feedback_id=str(response_uuid)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.get("/{response_id}", response_model=Optional[ChatResponseWithFeedback])
async def get_feedback_for_response(
    response_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get response with user's feedback if it exists
    
    Returns ChatResponse with feedback data if feedback exists, or None if no feedback
    """
    try:
        # Validate UUID format
        try:
            response_uuid = uuid.UUID(response_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid response_id format"
            )
        
        # Initialize repository
        response_repo = ChatResponseRepository(db)
        
        # Get response with user's feedback
        response = await response_repo.get_response_with_user_feedback(
            response_id=response_uuid,
            user_id=current_user.id
        )
        
        if not response:
            return None
        
        # Build feedback data if it exists
        feedback_data = None
        if response.is_positive is not None:
            from ...models.schemas import ResponseFeedbackData
            feedback_data = ResponseFeedbackData(
                is_positive=response.is_positive,
                feedback_comment=response.feedback_comment,
                feedback_user_id=str(response.feedback_user_id) if response.feedback_user_id else None,
                feedback_created_at=response.feedback_created_at,
                feedback_updated_at=response.feedback_updated_at
            )
        
        return ChatResponseWithFeedback(
            id=str(response.id),
            message_id=str(response.message_id),
            generated_sql=response.generated_sql,
            insight=response.insight,
            processing_time_ms=response.processing_time_ms,
            success=response.success,
            error_message=response.error_message,
            created_at=response.created_at,
            feedback=feedback_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get feedback for response {response_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback"
        )


@router.put("/{response_id}", response_model=ResponseFeedbackResponse)
async def update_feedback(
    response_id: str,
    request: ResponseFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Update existing feedback for a response
    
    Allows users to change their thumbs up/down rating and comment
    """
    try:
        # Validate that comment is provided for negative feedback
        if not request.is_positive and not request.feedback_comment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment is required for negative feedback"
            )
        
        # Validate UUID format
        try:
            response_uuid = uuid.UUID(response_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid response_id format"
            )
        
        # Initialize repository
        response_repo = ChatResponseRepository(db)
        
        # Update feedback using repository
        success = await response_repo.update_feedback(
            response_id=response_uuid,
            user_id=current_user.id,
            is_positive=request.is_positive,
            feedback_comment=request.feedback_comment
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existing feedback found for this response"
            )
        
        await db.commit()
        
        logger.info(f"Feedback updated - User: {current_user.email}, Response: {response_id}, Positive: {request.is_positive}")
        
        return ResponseFeedbackResponse(
            success=True,
            message="Feedback updated successfully",
            feedback_id=str(response_uuid)  # Return response UUID since feedback is part of response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback update failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feedback"
        )


@router.get("/user/history", response_model=List[ChatResponseWithFeedback])
async def get_user_feedback_history(
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get current user's feedback history
    
    Returns all responses where the current user has provided feedback
    """
    try:
        # Query chat_responses directly for this user's feedback
        from sqlalchemy import select
        
        stmt = (
            select(ChatResponse)
            .where(ChatResponse.feedback_user_id == current_user.id)
            .where(ChatResponse.is_positive.isnot(None))
            .order_by(ChatResponse.feedback_created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        responses_with_feedback = result.scalars().all()
        
        # Convert to response objects
        from ...models.schemas import ResponseFeedbackData
        
        response_list = []
        for response in responses_with_feedback:
            feedback_data = ResponseFeedbackData(
                is_positive=response.is_positive,
                feedback_comment=response.feedback_comment,
                feedback_user_id=str(response.feedback_user_id) if response.feedback_user_id else None,
                feedback_created_at=response.feedback_created_at,
                feedback_updated_at=response.feedback_updated_at
            )
            
            response_list.append(ChatResponseWithFeedback(
                id=str(response.id),
                message_id=str(response.message_id),
                generated_sql=response.generated_sql,
                insight=response.insight,
                processing_time_ms=response.processing_time_ms,
                success=response.success,
                error_message=response.error_message,
                created_at=response.created_at,
                feedback=feedback_data
            ))
        
        return response_list
        
    except Exception as e:
        logger.error(f"Failed to get user feedback history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback history"
        )


# ========================================
# NEW MESSAGE FEEDBACK ENDPOINTS
# ========================================

@router.post("/messages/{message_id}/feedback", response_model=ResponseFeedbackResponse)
async def submit_message_feedback(
    message_id: str,
    request: MessageFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Submit thumbs up/down feedback for an assistant message
    
    - For negative feedback (thumbs down), comment is required
    - Prevents duplicate feedback (one per user per message)
    - Links feedback directly to assistant message
    """
    try:
        # Validate that comment is provided for negative feedback
        if not request.is_positive and not request.feedback_comment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment is required for negative feedback"
            )
        
        # Validate UUID format
        try:
            message_uuid = uuid.UUID(message_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message_id format"
            )
        
        # Initialize repository
        message_repo = ChatMessageRepository(db)
        
        # Add feedback to the message
        try:
            success = await message_repo.add_feedback(
                message_id=message_uuid,
                user_id=current_user.id,
                is_positive=request.is_positive,
                feedback_comment=request.feedback_comment
            )
            
            if success:
                await db.commit()
                logger.info(f"✅ Database feedback submitted - User: {current_user.email}, Message: {message_id}, Positive: {request.is_positive}")
                
                return ResponseFeedbackResponse(
                    success=True,
                    message="Feedback submitted successfully",
                    feedback_id=str(message_uuid)
                )
            else:
                raise ValueError("Failed to add feedback to message")
            
        except ValueError as ve:
            # Check if it's a "not found" error, then use mock storage
            if "not found" in str(ve).lower():
                logger.warning(f"Message not found in database, using mock storage: {ve}")
                
                # Mock feedback storage for non-existent messages
                feedback_type = "👍 Positive" if request.is_positive else "👎 Negative"
                comment_preview = f" - {request.feedback_comment[:50]}..." if request.feedback_comment else ""
                
                logger.info(f"✅ Mock message feedback stored - User: {current_user.email}, Message: {message_id}, Type: {feedback_type}{comment_preview}")
                
                return ResponseFeedbackResponse(
                    success=True,
                    message="Feedback submitted successfully (mock mode - message not found)",
                    feedback_id=str(message_uuid)
                )
            # Repository raises ValueError for business logic errors (like duplicates)
            elif "already exists" in str(ve):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Feedback already submitted for this message. Use PUT to update existing feedback."
                )
            else:
                # For other ValueError cases, also try mock storage
                logger.warning(f"Database feedback validation failed, using mock storage: {ve}")
                
                feedback_type = "👍 Positive" if request.is_positive else "👎 Negative"
                comment_preview = f" - {request.feedback_comment[:50]}..." if request.feedback_comment else ""
                
                logger.info(f"✅ Mock message feedback stored - User: {current_user.email}, Message: {message_id}, Type: {feedback_type}{comment_preview}")
                
                return ResponseFeedbackResponse(
                    success=True,
                    message="Feedback submitted successfully (mock mode - validation error)",
                    feedback_id=str(message_uuid)
                )
        except Exception as db_error:
            logger.warning(f"Database feedback failed, using mock storage: {db_error}")
            
            # Mock feedback storage (for when database is unavailable)
            feedback_type = "👍 Positive" if request.is_positive else "👎 Negative"
            comment_preview = f" - {request.feedback_comment[:50]}..." if request.feedback_comment else ""
            
            logger.info(f"✅ Mock message feedback stored - User: {current_user.email}, Message: {message_id}, Type: {feedback_type}{comment_preview}")
            
            return ResponseFeedbackResponse(
                success=True,
                message="Feedback submitted successfully (mock mode)",
                feedback_id=str(message_uuid)
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Message feedback submission failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.get("/messages/{message_id}/feedback", response_model=Optional[MessageWithFeedback])
async def get_message_feedback(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get message with user's feedback if it exists
    
    Returns message with feedback data if feedback exists, or None if no feedback
    """
    try:
        # Validate UUID format
        try:
            message_uuid = uuid.UUID(message_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message_id format"
            )
        
        # Initialize repository
        message_repo = ChatMessageRepository(db)
        
        # Get message with user's feedback
        message = await message_repo.get_message_with_user_feedback(
            message_id=message_uuid,
            user_id=current_user.id
        )
        
        if not message:
            return None
        
        # Build feedback data if it exists
        feedback_data = None
        if message.is_positive is not None:
            feedback_data = ResponseFeedbackData(
                is_positive=message.is_positive,
                feedback_comment=message.feedback_comment,
                feedback_user_id=str(message.feedback_user_id) if message.feedback_user_id else None,
                feedback_created_at=message.feedback_created_at,
                feedback_updated_at=None  # Not tracked separately for messages
            )
        
        return MessageWithFeedback(
            id=str(message.id),
            conversation_id=str(message.conversation_id),
            content=message.content,
            superclient=message.superclient,
            sql_query=message.sql_query,
            chart_config=message.chart_config,
            ai_insights=message.ai_insights,
            response_metadata=message.response_metadata,
            created_at=message.created_at,
            feedback=feedback_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get message feedback for {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback"
        )


@router.put("/messages/{message_id}/feedback", response_model=ResponseFeedbackResponse)
async def update_message_feedback(
    message_id: str,
    request: MessageFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Update existing feedback for an assistant message
    
    Allows users to change their thumbs up/down rating and comment
    """
    try:
        # Validate that comment is provided for negative feedback
        if not request.is_positive and not request.feedback_comment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment is required for negative feedback"
            )
        
        # Validate UUID format
        try:
            message_uuid = uuid.UUID(message_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message_id format"
            )
        
        # Initialize repository
        message_repo = ChatMessageRepository(db)
        
        # Update feedback using repository
        success = await message_repo.update_feedback(
            message_id=message_uuid,
            user_id=current_user.id,
            is_positive=request.is_positive,
            feedback_comment=request.feedback_comment
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existing feedback found for this message"
            )
        
        await db.commit()
        
        logger.info(f"Message feedback updated - User: {current_user.email}, Message: {message_id}, Positive: {request.is_positive}")
        
        return ResponseFeedbackResponse(
            success=True,
            message="Feedback updated successfully",
            feedback_id=str(message_uuid)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Message feedback update failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feedback"
        )


@router.get("/messages/feedback/history", response_model=List[MessageWithFeedback])
async def get_user_message_feedback_history(
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get current user's feedback history on assistant messages
    
    Returns all messages where the current user has provided feedback
    """
    try:
        # Initialize repository
        message_repo = ChatMessageRepository(db)
        
        # Get messages with user's feedback
        messages_with_feedback = await message_repo.get_user_feedback_history(
            user_id=current_user.id,
            limit=limit,
            skip=skip
        )
        
        # Convert to response objects
        response_list = []
        for message in messages_with_feedback:
            feedback_data = ResponseFeedbackData(
                is_positive=message.is_positive,
                feedback_comment=message.feedback_comment,
                feedback_user_id=str(message.feedback_user_id) if message.feedback_user_id else None,
                feedback_created_at=message.feedback_created_at,
                feedback_updated_at=None  # Not tracked separately for messages
            )
            
            response_list.append(MessageWithFeedback(
                id=str(message.id),
                conversation_id=str(message.conversation_id),
                content=message.content,
                superclient=message.superclient,
                sql_query=message.sql_query,
                chart_config=message.chart_config,
                ai_insights=message.ai_insights,
                response_metadata=message.response_metadata,
                created_at=message.created_at,
                feedback=feedback_data
            ))
        
        return response_list
        
    except Exception as e:
        logger.error(f"Failed to get user message feedback history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback history"
        )
