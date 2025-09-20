"""
Service Locator for CVS Rebate Analytics
Provides centralized access to services without circular imports
"""

from typing import Optional
from .llm_service import LLMService

# Global service instances
_llm_service: Optional[LLMService] = None

def set_llm_service(service: LLMService) -> None:
    """Set the LLM service for routes to use"""
    global _llm_service
    _llm_service = service

def get_llm_service() -> Optional[LLMService]:
    """Get the LLM service for routes to use"""
    return _llm_service

def get_streaming_llm_service() -> Optional[LLMService]:
    """Get the streaming LLM service (same as regular LLM service now)"""
    return _llm_service
