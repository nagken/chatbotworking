"""
Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel, Field, EmailStr, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatQuery(BaseModel):
    """Natural language query from user"""
    message: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    superclient: Optional[str] = Field(None, description="Selected SuperClient for the query")
    conversation_id: Optional[str] = Field(None, description="Target conversation ID (creates new if not provided)")

# Login schemas
class LoginRequest(BaseModel):
    """Login request payload"""
    email: EmailStr = Field(..., description="Email address for authentication")
    password: str = Field(..., min_length=1, max_length=255, description="Password for authentication")
    remember_me: Optional[bool] = Field(False, description="Whether to create a persistent session")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "remember_me": False
            }
        }

class LoginResponse(BaseModel):
    """Login response payload"""
    success: bool = Field(..., description="Whether login was successful")
    message: str = Field(..., description="Login result message")
    user: Optional[Dict[str, Any]] = Field(None, description="User information if login successful")
    session_duration: Optional[int] = Field(None, description="Session duration in seconds")
    session_token: Optional[str] = Field(None, description="Session token for API authentication")

# User management schemas for database-backed authentication
class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr = Field(..., description="User's email address (used for login)")
    username: str = Field(..., min_length=2, max_length=100, description="Display name for the user")
    password: str = Field(..., min_length=8, max_length=255, description="User's password (will be hashed)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "John Doe",
                "password": "securepassword123"
            }
        }

class UserResponse(BaseModel):
    """Schema for returning user information (no sensitive data)"""
    id: str = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    username: str = Field(..., description="User's display name")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="When the user account was created")
    last_login_at: Optional[datetime] = Field(None, description="When the user last logged in")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com", 
                "username": "John Doe",
                "is_active": True,
                "created_at": "2024-12-29T12:00:00Z",
                "last_login_at": "2024-12-29T14:30:00Z"
            }
        }

class UserUpdate(BaseModel):
    """Schema for updating user profile information"""
    username: Optional[str] = Field(None, min_length=2, max_length=100, description="New display name")
    is_active: Optional[bool] = Field(None, description="Update user's active status (admin only)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "Jane Smith",
                "is_active": True
            }
        }

class PasswordChangeRequest(BaseModel):
    """Schema for changing user password"""
    current_password: str = Field(..., description="User's current password")
    new_password: str = Field(..., min_length=8, max_length=255, description="New password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newsecurepassword456"
            }
        }

class UserListResponse(BaseModel):
    """Schema for listing users (admin only)"""
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of users per page")

# New models for chat response extraction
class SqlResponse(BaseModel):
    """Generated SQL from chat response"""
    generated_sql: str = Field(..., description="The generated SQL query text")

class DataResult(BaseModel):
    """SQL execution result data"""
    data: List[Dict[str, Any]] = Field(..., description="The actual data rows returned")
    schema: Dict[str, Any] = Field(..., description="Field definitions and metadata")
    name: str = Field(..., description="Name/identifier for the result set")

class ChartResponse(BaseModel):
    """Chart configuration from chat response"""
    vega_spec: Dict[str, Any] = Field(..., description="Vega-Lite specification for chart rendering")
    chart_metadata: Optional[Dict[str, Any]] = Field(None, description="Chart title, description, and type information")
    rendering_options: Optional[Dict[str, Any]] = Field(None, description="Chart rendering options like width, height, theme")

class ChatResponseExtract(BaseModel):
    """Extracted data from chat response array - used internally for processing"""
    response_id: str = Field(..., description="Unique identifier for this response (UUID)")
    generated_sql: Optional[str] = Field(None, description="Latest generated SQL query found")
    ai_insights: Optional[str] = Field(None, description="AI insight about the data")
    execution_result: Optional[DataResult] = Field(None, description="SQL execution results with data and schema")
    chart_config: Optional[ChartResponse] = Field(None, description="Chart configuration from LLM response")
    chart_config_for_storage: Optional[Dict[str, Any]] = Field(None, description="Chart configuration without data for storage")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Extraction metadata and processing info")
    
    # Storage data for MessageChunk table
    result_schema: Optional[Dict[str, Any]] = Field(None, description="Schema for result data (stored once per message)")
    result_data: Optional[List[Dict[str, Any]]] = Field(None, description="Raw result data for storage")

class ResponseFeedbackData(BaseModel):
    """User feedback data on a response"""
    is_positive: Optional[bool] = Field(None, description="True for thumbs up, False for thumbs down, None if no feedback")
    feedback_comment: Optional[str] = Field(None, max_length=255, description="Optional feedback comment (max 255 chars)")
    feedback_user_id: Optional[str] = Field(None, description="UUID of user who provided feedback")
    feedback_created_at: Optional[datetime] = Field(None, description="When feedback was created")
    feedback_updated_at: Optional[datetime] = Field(None, description="When feedback was last updated")

class ChatResponseWithFeedback(BaseModel):
    """Chat response with integrated feedback data"""
    id: str = Field(..., description="Response UUID")
    message_id: str = Field(..., description="Associated message UUID")
    generated_sql: Optional[str] = Field(None, description="Generated SQL query")
    insight: Optional[str] = Field(None, description="AI insight about the data")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    success: bool = Field(..., description="Whether processing was successful")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    created_at: datetime = Field(..., description="When response was created")
    feedback: Optional[ResponseFeedbackData] = Field(None, description="User feedback if provided")

class ChatResponse(BaseModel):
    """Response to chat query"""
    success: bool
    message: str
    conversation_id: Optional[str] = Field(None, description="ID of the conversation (useful for newly created conversations)")
    
    # Extracted data from chat response (current working format)
    data: Optional[ChatResponseExtract] = Field(None, description="Extracted data from chat response")
    
    # FUTURE: Standardized assistant message data for frontend consistency
    # assistant_message: Optional["MessageDetail"] = Field(None, description="Standardized assistant message data for frontend rendering")

# Response Feedback schemas (legacy - for ChatResponse table)
class ResponseFeedbackRequest(BaseModel):
    """Request to submit feedback on an AI response"""
    response_id: str = Field(..., description="UUID of the chat response being rated")
    is_positive: bool = Field(..., description="True for thumbs up, False for thumbs down")
    feedback_comment: Optional[str] = Field(None, max_length=255, description="Optional feedback comment (required for negative feedback, max 255 chars)")
    
    class Config:
        # Example for API documentation
        json_schema_extra = {
            "example": {
                "response_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_positive": False,
                "feedback_comment": "The SQL query didn't return the expected results for my question about rebates."
            }
        }

class ResponseFeedbackResponse(BaseModel):
    """Response after submitting feedback"""
    success: bool = Field(..., description="Whether feedback was successfully recorded")
    message: str = Field(..., description="Result message")
    feedback_id: Optional[str] = Field(None, description="UUID of the created feedback record")

# Message Feedback schemas (new - for ChatMessage table)
class MessageFeedbackRequest(BaseModel):
    """Request to submit feedback on an assistant message"""
    is_positive: bool = Field(..., description="True for thumbs up, False for thumbs down")
    feedback_comment: Optional[str] = Field(None, max_length=255, description="Optional feedback comment (required for negative feedback, max 255 chars)")
    
    class Config:
        # Example for API documentation
        json_schema_extra = {
            "example": {
                "is_positive": False,
                "feedback_comment": "The response didn't fully answer my question about rebate eligibility."
            }
        }

class MessageWithFeedback(BaseModel):
    """Assistant message with integrated feedback data"""
    id: str = Field(..., description="Message UUID")
    conversation_id: str = Field(..., description="Associated conversation UUID")
    content: str = Field(..., description="Message content")
    superclient: Optional[str] = Field(None, description="SuperClient context")
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    chart_config: Optional[Dict[str, Any]] = Field(None, description="Chart configuration")
    ai_insights: Optional[str] = Field(None, description="AI insights about the data")
    response_metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")
    created_at: datetime = Field(..., description="When message was created")
    feedback: Optional[ResponseFeedbackData] = Field(None, description="User feedback if provided")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "conversation_id": "conv-123",
                "content": "Here's the analysis you requested...",
                "superclient": "CVS_Health",
                "sql_query": "SELECT * FROM rebates WHERE...",
                "chart_config": {"mark": "bar", "data": {...}},
                "ai_insights": "The data shows increasing trends...",
                "created_at": "2024-12-31T12:00:00Z",
                "feedback": {
                    "is_positive": True,
                    "feedback_comment": "Very helpful analysis!",
                    "feedback_created_at": "2024-12-31T12:05:00Z"
                }
            }
        }


# ========== CONVERSATION MANAGEMENT SCHEMAS ==========

class ConversationCreate(BaseModel):
    """Request to create a new conversation"""
    title: Optional[str] = Field(None, max_length=500, description="Optional conversation title (auto-generated if not provided)")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Rebate Analysis for Q4"
            }
        }

class ConversationUpdate(BaseModel):
    """Request to update an existing conversation"""
    title: str = Field(..., min_length=1, max_length=500, description="New conversation title")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Rebate Analysis"
            }
        }

class MessageSummary(BaseModel):
    """Summary of the last message pair in a conversation"""
    user_message: Optional[str] = Field(None, description="Last user message content")
    assistant_message: Optional[str] = Field(None, description="Last assistant response")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of the last message")

class MessageDetail(BaseModel):
    """Detailed message information for conversation history - unified schema for all messages"""
    id: str = Field(..., description="Message UUID")
    message_type: str = Field(..., description="Type of message (user or assistant)")
    content: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="When the message was created")
    superclient: Optional[str] = Field(None, description="SuperClient context if applicable")
    
    # New chunk-based fields for assistant messages (reconstructed from message_chunks table)
    chunks: Optional[List[Dict[str, Any]]] = Field(None, description="Reconstructed message chunks for rendering")
    chunk_summary: Optional[Dict[str, Any]] = Field(None, description="Summary of available chunks")
    
    # Legacy fields for assistant messages (for backward compatibility - extracted from chunks)
    sql_query: Optional[str] = Field(None, description="Generated SQL query")
    chart_config: Optional[Dict[str, Any]] = Field(None, description="Chart configuration with data for rendering")
    ai_insights: Optional[str] = Field(None, description="AI insights about the data")
    response_metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")
    
    # Result data fields for assistant messages (extracted from chunks)
    result_data: Optional[List[Dict[str, Any]]] = Field(None, description="Reconstructed result data")
    result_schema: Optional[Dict[str, Any]] = Field(None, description="Result data schema")
    data_status: Optional[str] = Field(None, description="Status of result data (complete, error, stale, etc.)")
    data_message: Optional[str] = Field(None, description="Message about data status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "message_type": "user",
                "content": "Show me rebate trends for last quarter",
                "created_at": "2024-01-15T14:45:00Z",
                "superclient": "CVS_Health",
                "sql_query": None,
                "chart_config": None,
                "ai_insights": None,
                "response_metadata": None
            }
        }

class MessageHistoryResponse(BaseModel):
    """Response containing full conversation message history"""
    conversation_id: str = Field(..., description="Conversation UUID")
    title: str = Field(..., description="Conversation title")
    messages: List[MessageDetail] = Field(..., description="List of all messages in chronological order")
    total_messages: int = Field(..., description="Total number of messages in conversation")
    created_at: datetime = Field(..., description="When conversation was created")
    updated_at: datetime = Field(..., description="When conversation was last updated")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Rebate Analysis Discussion",
                "messages": [
                    {
                        "id": "msg-1",
                        "message_type": "user",
                        "content": "Show me rebate trends",
                        "created_at": "2024-01-15T10:30:00Z",
                        "superclient": "CVS_Health",
                        "sql_query": None,
                        "chart_config": None,
                        "ai_insights": None,
                        "response_metadata": None
                    },
                                         {
                         "id": "msg-2", 
                         "message_type": "assistant",
                         "content": "Here's your rebate analysis...",
                         "created_at": "2024-01-31T10:31:00Z",
                         "superclient": None,
                         "sql_query": "SELECT client_name, rebate_amount FROM rebates WHERE year = 2025 ORDER BY rebate_amount DESC",
                         "chart_config": {
                             "mark": "bar",
                             "encoding": {
                                 "x": {"field": "client_name", "type": "nominal"},
                                 "y": {"field": "rebate_amount", "type": "quantitative"}
                             },
                             "data": {"values": [{"client_name": "Client A", "rebate_amount": 50000}]}
                         },
                         "ai_insights": "The data shows significant variation in rebate amounts across clients, with the top performers showing 3x higher rebates than average.",
                         "response_metadata": {
                             "processing_time_ms": 1250,
                             "success": True,
                             "data_points": 45
                         },
                         "result_data": [{"client_name": "Client A", "rebate_amount": 50000}],
                         "result_schema": {
                             "fields": [
                                 {"name": "client_name", "type": "string"},
                                 {"name": "rebate_amount", "type": "number"}
                             ]
                         },
                         "data_status": "complete",
                         "data_message": None
                     }
                ],
                "total_messages": 2,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:31:00Z"
            }
        }

class ConversationSummary(BaseModel):
    """Conversation information for listing"""
    id: str = Field(..., description="Conversation UUID")
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="When conversation was created")
    updated_at: datetime = Field(..., description="When conversation was last updated")
    last_message: Optional[MessageSummary] = Field(None, description="Summary of the last message pair")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Rebate Analysis Discussion",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T14:45:00Z",
                "last_message": {
                    "user_message": "Show me rebate trends for last quarter",
                    "assistant_message": "Here's your rebate analysis...",
                    "timestamp": "2024-01-15T14:45:00Z"
                }
            }
        }

class ConversationListResponse(BaseModel):
    """Response containing list of user's conversations"""
    conversations: List[ConversationSummary] = Field(..., description="List of conversation summaries")
    total: int = Field(..., description="Total number of conversations")

class ConversationDetailResponse(BaseModel):
    """Detailed conversation information"""
    id: str = Field(..., description="Conversation UUID")
    title: str = Field(..., description="Conversation title")
    created_at: datetime = Field(..., description="When conversation was created")
    updated_at: datetime = Field(..., description="When conversation was last updated")
    message_count: int = Field(..., description="Total number of messages in conversation")

class ConversationResponse(BaseModel):
    """Response after conversation operations"""
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Result message")
    conversation: Optional[ConversationDetailResponse] = Field(None, description="Conversation details if successful")

# Note: ChatQuery class updated above to include conversation_id parameter


# Note: StandardizedAssistantMessage removed - using MessageDetail consistently



