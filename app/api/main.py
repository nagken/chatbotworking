"""
API Routes Initialization
Centralizes all route registration and dependencies
"""

from fastapi import APIRouter
from .routes import auth, chat, health, feedback, conversations, documents

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(health.router, tags=["health"])  # Remove prefix so /health works directly
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])


# Export the main API router
__all__ = ["api_router"]
