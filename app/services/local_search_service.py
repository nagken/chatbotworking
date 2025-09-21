"""
Local Search Service - Alternative to Vertex AI
Provides document search and template-based responses without external AI APIs
"""

import logging
import json
import re
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from ..services.pdf_indexing_service import PDFIndexingService

logger = logging.getLogger(__name__)


class LocalSearchService:
    """Service for local document search and template-based responses"""
    
    def __init__(self):
        """Initialize local search service"""
        logger.info("Initializing Local Search service...")
        
        # Initialize PDF indexing service
        self.pdf_service = PDFIndexingService()
        self.pdf_service.load_index()
        logger.info("PDF indexing service loaded for local search")
        
        # Load response templates
        self.response_templates = self._load_response_templates()
        self.common_patterns = self._load_common_patterns()
        
        logger.info("Local Search Service initialized successfully")
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load predefined response templates for common queries"""
        return {
            "greeting": "Hello! I'm your CVS Pharmacy Knowledge Assist. I can help you find information about policies, procedures, benefits, and other company resources. What would you like to know?",
            
            "policy_question": "I found information about {topic} in our policy documents. Here are the relevant details:\n\n{content}\n\nWould you like me to search for more specific information?",
            
            "procedure_question": "Based on our procedure documentation for {topic}:\n\n{content}\n\nIs there a specific step or aspect you'd like me to clarify?",
            
            "benefits_question": "Here's information about {topic} from our benefits documentation:\n\n{content}\n\nDo you need details about enrollment, eligibility, or coverage?",
            
            "general_search": "I found {count} document(s) related to '{query}':\n\n{content}\n\nWould you like me to search for something more specific?",
            
            "no_results": "I couldn't find specific information about '{query}' in our current document library. You might try:\n\n• Using different keywords\n• Checking if the topic might be covered under a different name\n• Contacting your supervisor or HR for specialized questions\n\nWould you like to try a different search?",
            
            "document_list": "Here are the documents I found related to '{query}':\n\n{documents}\n\nClick on any document name to download and view the full content.",
            
            "contraceptive_coverage": "Based on our contraceptive coverage documentation:\n\n{content}\n\nFor specific coverage questions or enrollment, please contact Member Services.",
            
            "prescription_benefits": "Here's information about prescription benefits:\n\n{content}\n\nFor specific medication coverage or prior authorization questions, please contact the pharmacy benefits department.",
        }
    
    def _load_common_patterns(self) -> Dict[str, List[str]]:
        """Load common search patterns and keywords"""
        return {
            "greeting_patterns": [
                r"\b(hello|hi|hey|good morning|good afternoon)\b",
                r"\bhelp\b",
                r"\bwhat can you do\b",
            ],
            
            "policy_patterns": [
                r"\bpolicy\b",
                r"\bpolicies\b", 
                r"\brules?\b",
                r"\bguidelines?\b",
                r"\bregulations?\b",
            ],
            
            "procedure_patterns": [
                r"\bprocedure\b",
                r"\bsteps?\b",
                r"\bhow to\b",
                r"\bprocess\b",
                r"\binstructions?\b",
            ],
            
            "benefits_patterns": [
                r"\bbenefits?\b",
                r"\binsurance\b",
                r"\bcoverage\b",
                r"\benrollment?\b",
                r"\beligibility\b",
                r"\bhealth plan\b",
            ],
            
            "contraceptive_patterns": [
                r"\bcontraceptiv\w*\b",
                r"\bbirth control\b",
                r"\bfamily planning\b",
                r"\breproductive health\b",
            ],
            
            "prescription_patterns": [
                r"\bprescription\b",
                r"\bmedication\b",
                r"\bdrug\b",
                r"\bpharmacy\b",
                r"\brx\b",
            ],
        }
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query to determine response template"""
        query_lower = query.lower()
        
        # Check for greeting patterns
        for pattern in self.common_patterns["greeting_patterns"]:
            if re.search(pattern, query_lower):
                return "greeting"
        
        # Check for specific topic patterns
        for pattern in self.common_patterns["contraceptive_patterns"]:
            if re.search(pattern, query_lower):
                return "contraceptive_coverage"
        
        for pattern in self.common_patterns["prescription_patterns"]:
            if re.search(pattern, query_lower):
                return "prescription_benefits"
        
        for pattern in self.common_patterns["benefits_patterns"]:
            if re.search(pattern, query_lower):
                return "benefits_question"
        
        for pattern in self.common_patterns["policy_patterns"]:
            if re.search(pattern, query_lower):
                return "policy_question"
        
        for pattern in self.common_patterns["procedure_patterns"]:
            if re.search(pattern, query_lower):
                return "procedure_question"
        
        return "general_search"
    
    def _extract_topic_from_query(self, query: str) -> str:
        """Extract the main topic from the user's query"""
        # Remove common question words
        topic = re.sub(r'\b(what|how|when|where|why|is|are|can|could|would|should|do|does|about|the|a|an)\b', '', query.lower())
        topic = re.sub(r'\s+', ' ', topic).strip()
        return topic or query.lower()
    
    def _format_document_content(self, documents: List[Dict], max_content_length: int = 1000) -> str:
        """Format document content for display"""
        if not documents:
            return "No relevant documents found."
        
        formatted_content = []
        
        for doc in documents[:3]:  # Limit to top 3 results
            title = doc.get('title', 'Untitled Document')
            content = doc.get('content', '')
            filename = doc.get('filename', '')
            
            # Truncate content if too long
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            # Create clickable document link
            doc_link = f"📄 **{title}**"
            if filename:
                doc_link += f" `{filename}`"
            
            formatted_content.append(f"{doc_link}\n{content}")
        
        return "\n\n---\n\n".join(formatted_content)
    
    def _format_document_list(self, documents: List[Dict]) -> str:
        """Format a list of document titles with download links"""
        if not documents:
            return "No documents found."
        
        doc_list = []
        for i, doc in enumerate(documents[:10], 1):  # Limit to top 10
            title = doc.get('title', 'Untitled Document')
            filename = doc.get('filename', '')
            
            if filename:
                doc_list.append(f"{i}. 📄 **{title}** - `{filename}`")
            else:
                doc_list.append(f"{i}. 📄 **{title}**")
        
        return "\n".join(doc_list)
    
    def search_documents(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search documents using the PDF indexing service"""
        try:
            # Use existing PDF search functionality
            search_results = self.pdf_service.search_documents(query, max_results=max_results)
            return search_results
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def generate_response(self, user_message: str) -> Dict[str, Any]:
        """
        Generate a response based on local document search and templates
        
        Args:
            user_message: The user's question or request
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            # Classify the query type
            query_type = self._classify_query(user_message)
            topic = self._extract_topic_from_query(user_message)
            
            logger.info(f"Query classified as: {query_type}, Topic: {topic}")
            
            # Handle greeting
            if query_type == "greeting":
                return {
                    "response": self.response_templates["greeting"],
                    "documents": [],
                    "query_type": query_type,
                    "confidence": "high"
                }
            
            # Search for relevant documents
            documents = self.search_documents(user_message)
            
            # Generate response based on query type and search results
            if documents:
                if query_type == "general_search":
                    content = self._format_document_content(documents)
                    response = self.response_templates[query_type].format(
                        count=len(documents),
                        query=user_message,
                        content=content
                    )
                else:
                    content = self._format_document_content(documents)
                    response = self.response_templates[query_type].format(
                        topic=topic,
                        content=content
                    )
                
                confidence = "high" if len(documents) >= 3 else "medium"
            else:
                response = self.response_templates["no_results"].format(query=user_message)
                confidence = "low"
            
            return {
                "response": response,
                "documents": documents,
                "query_type": query_type,
                "confidence": confidence,
                "topic": topic
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "I apologize, but I encountered an error while searching for information. Please try rephrasing your question or contact support for assistance.",
                "documents": [],
                "query_type": "error",
                "confidence": "low"
            }
    
    async def stream_response(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        Generate streaming response for real-time display
        
        Args:
            user_message: The user's question or request
            
        Yields:
            Chunks of the response text
        """
        try:
            # Generate the full response
            result = self.generate_response(user_message)
            response = result["response"]
            
            # Stream the response in chunks
            chunk_size = 50  # Characters per chunk
            for i in range(0, len(response), chunk_size):
                chunk = response[i:i + chunk_size]
                yield chunk
                # Small delay to simulate streaming
                await asyncio.sleep(0.05)
                
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield "I apologize, but I encountered an error while processing your request."

    def get_document_suggestions(self, query: str) -> List[str]:
        """Get document filename suggestions for download links"""
        documents = self.search_documents(query)
        return [doc.get('filename', '') for doc in documents if doc.get('filename')]