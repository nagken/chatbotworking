"""
SQLAlchemy models for CA Rebates Tool database
Defines the structure of all database tables
"""

from sqlalchemy import Column, String, Boolean, DateTime, UUID, Text, Integer, ForeignKey, Index, Enum
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

Base = declarative_base()


class MessageType(enum.Enum):
    """Enum for chat message types"""
    USER = "user"
    ASSISTANT = "assistant"



class User(Base):
    """
    Users table - replaces users.json file
    Stores user authentication and profile information
    """
    __tablename__ = 'users'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)  # bcrypt hashed password
    
    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # Note: No relationships to conversations or users since we use string user_id for auth fallback
    
    # Indexes
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_active', 'is_active'),
        Index('idx_users_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<User(email='{self.email}', username='{self.username}', active={self.is_active})>"


class UserSession(Base):
    """
    User sessions table - handles authentication tokens and session management
    """
    __tablename__ = 'user_sessions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to users - using string to match auth system
    user_id = Column(String(255), nullable=False, index=True)
    
    # Session data
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    remember_me = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(INET, nullable=True)
    
    # Note: No relationship to User since we use string user_id for auth fallback
    
    # Indexes
    __table_args__ = (
        Index('idx_sessions_user_id', 'user_id'),
        Index('idx_sessions_token', 'session_token'),
        Index('idx_sessions_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', expires_at='{self.expires_at}')>"


class ChatConversation(Base):
    """
    Chat conversations table - groups related messages together
    """
    __tablename__ = 'chat_conversations'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to users - using string to match auth system
    user_id = Column(String(255), nullable=False, index=True)
    
    # Conversation data
    conversation_id = Column(String(255), nullable=False, index=True)  # e.g., "cvs-rebate-conversation"
    title = Column(String(500), nullable=True)  # Generated title based on first message
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    # Note: No relationship to User since we use string user_id for auth fallback
    
    # Indexes
    __table_args__ = (
        Index('idx_conversations_user_id', 'user_id'),
        Index('idx_conversations_conversation_id', 'conversation_id'),
        Index('idx_conversations_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatConversation(id='{self.id}', conversation_id='{self.conversation_id}', title='{self.title}')>"


class ChatMessage(Base):
    """
    Chat messages table - stores user queries and assistant responses
    """
    __tablename__ = 'chat_messages'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('chat_conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # String to match auth system
    
    # Message data
    message_type = Column(Enum(MessageType), nullable=False, index=True)
    content = Column(Text, nullable=False)
    superclient = Column(String(255), nullable=True, index=True)  # For filtering queries
    enhanced_message = Column(Text, nullable=True)  # Message with SuperClient context
    
    # Enhanced storage fields for assistant messages
    sql_query = Column(Text, nullable=True, index=True)  # Generated SQL query for re-execution
    chart_config = Column(JSONB, nullable=True, index=True)  # Chart configuration without data values
    ai_insights = Column(Text, nullable=True, index=True)  # AI insights about the data analysis
    response_metadata = Column(JSONB, nullable=True)  # Additional metadata (timing, success, etc.)
    result_schema = Column(JSONB, nullable=True, index=True)  # Schema for result data (stored once per message)
    
    # User feedback fields (for assistant messages)
    is_positive = Column(Boolean, nullable=True, index=True)  # True = thumbs up, False = thumbs down, NULL = no feedback
    feedback_comment = Column(String(255), nullable=True)  # Optional feedback comment (max 255 chars)
    feedback_user_id = Column(String(255), nullable=True, index=True)  # String to match auth system - User who provided feedback
    feedback_created_at = Column(DateTime(timezone=True), nullable=True)  # When feedback was provided
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")
    responses = relationship("ChatResponse", back_populates="message", cascade="all, delete-orphan")
    message_chunks = relationship("MessageChunk", back_populates="message", cascade="all, delete-orphan")
    
    # Note: No relationships to User since we use string user_id for auth fallback
    
    # Indexes
    __table_args__ = (
        Index('idx_messages_conversation_id', 'conversation_id'),
        Index('idx_messages_user_id', 'user_id'),
        Index('idx_messages_type', 'message_type'),
        Index('idx_messages_superclient', 'superclient'),
        Index('idx_messages_created_at', 'created_at'),
        Index('idx_messages_sql_query', 'sql_query'), 
        Index('idx_messages_chart_config', 'chart_config', postgresql_using='gin'),
        Index('idx_messages_ai_insights', 'ai_insights'),
        Index('idx_messages_result_schema', 'result_schema', postgresql_using='gin'),
        # Feedback indexes
        Index('idx_messages_is_positive', 'is_positive'),
        Index('idx_messages_feedback_user_id', 'feedback_user_id'),
        Index('idx_messages_feedback_created_at', 'feedback_created_at'),
        # Composite indexes for efficient feedback queries
        Index('idx_messages_feedback_composite', 'message_type', 'is_positive'),
        Index('idx_messages_user_feedback', 'feedback_user_id', 'feedback_created_at'),
        # Unique constraint: one feedback per user per assistant message
        Index('uq_message_user_feedback', 'id', 'feedback_user_id', unique=True),
    )
    
    def __repr__(self):
        return f"<ChatMessage(id='{self.id}', type='{self.message_type}', superclient='{self.superclient}')>"


class ChatResponse(Base):
    """
    Chat responses table - stores LLM responses and user feedback
    """
    __tablename__ = 'chat_responses'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to messages
    message_id = Column(UUID(as_uuid=True), ForeignKey('chat_messages.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Response data
    generated_sql = Column(Text, nullable=True)  # Extracted SQL query
    insight = Column(Text, nullable=True)  # AI insight about the data
    
    # Performance metrics
    processing_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=False, index=True)
    error_message = Column(Text, nullable=True)
    
    # User feedback (merged from ResponseFeedback table)
    is_positive = Column(Boolean, nullable=True, index=True)  # True = thumbs up, False = thumbs down, NULL = no feedback
    feedback_comment = Column(String(255), nullable=True)  # Optional feedback comment (max 255 chars)
    feedback_user_id = Column(String(255), nullable=True, index=True)  # String to match auth system
    feedback_created_at = Column(DateTime(timezone=True), nullable=True)
    feedback_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="responses")
    
    # Note: No relationship to User since we use string user_id for auth fallback
    
    # Indexes
    __table_args__ = (
        Index('idx_responses_message_id', 'message_id'),
        Index('idx_responses_success', 'success'),
        Index('idx_responses_created_at', 'created_at'),
        Index('idx_responses_is_positive', 'is_positive'),
        Index('idx_responses_feedback_user_id', 'feedback_user_id'),
        Index('idx_responses_feedback_created_at', 'feedback_created_at'),
        # Unique constraint: one feedback per user per message (via response)
        Index('uq_response_user_feedback', 'message_id', 'feedback_user_id', unique=True),
    )
    
    def __repr__(self):
        return f"<ChatResponse(id='{self.id}', message_id='{self.message_id}', success={self.success})>"


class MessageChunkType(enum.Enum):
    """Enum for message chunk types from streaming"""
    sql = "sql"
    data = "data"  
    chart = "chart"
    insights = "insights"


class MessageChunk(Base):
    """
    Message chunks table - stores individual transformed chunks from streaming responses
    Each chunk represents a discrete piece of assistant message data (sql, data, chart, insights)
    """
    __tablename__ = 'message_chunks'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys for relationships
    message_id = Column(UUID(as_uuid=True), ForeignKey('chat_messages.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Chunk identification
    chunk_type = Column(Enum(MessageChunkType), nullable=False, index=True)
    chunk_sequence = Column(Integer, nullable=False, index=True)  # Order chunks were received during streaming
    
    # Data chunking for large datasets (mainly for 'data' and 'chart' types)
    data_chunk_index = Column(Integer, nullable=False, default=0, index=True)  # 0-based index for splitting large data
    total_data_chunks = Column(Integer, nullable=False, default=1, index=True)  # Total number of data chunks for this chunk_type
    
    # The transformed chunk data (stored as received from StreamingMessageTransformer)
    # NOTE: No index on chunk_data to avoid PostgreSQL btree v4 size limit (2704 bytes) - see postgresql-index-size-fix.md
    chunk_data = Column(JSONB, nullable=False)  # Complete transformed chunk ready for frontend
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="message_chunks")
    
    # Indexes
    __table_args__ = (
        Index('idx_message_chunks_message_id', 'message_id'),
        Index('idx_message_chunks_type', 'chunk_type'),
        Index('idx_message_chunks_sequence', 'chunk_sequence'),
        Index('idx_message_chunks_data_index', 'data_chunk_index'),
        Index('idx_message_chunks_created_at', 'created_at'),
        # Composite indexes for efficient retrieval
        Index('idx_message_chunks_message_type', 'message_id', 'chunk_type'),
        Index('idx_message_chunks_message_sequence', 'message_id', 'chunk_sequence'),
        Index('idx_message_chunks_message_data_chunk', 'message_id', 'chunk_type', 'data_chunk_index'),
        # Ensure unique data chunks per message and chunk type
        Index('uq_message_chunks_data_chunk', 'message_id', 'chunk_type', 'data_chunk_index', unique=True),
    )
    
    def __repr__(self):
        return f"<MessageChunk(id='{self.id}', message_id='{self.message_id}', type='{self.chunk_type}', seq={self.chunk_sequence}, data_chunk={self.data_chunk_index}/{self.total_data_chunks})>"


# Utility function to create all tables
async def create_all_tables(engine):
    """
    Create all database tables
    This should be used in migrations, not directly in application code
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Utility function to drop all tables (for testing/development)
async def drop_all_tables(engine):
    """
    Drop all database tables - USE WITH CAUTION!
    Only for development/testing environments
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
