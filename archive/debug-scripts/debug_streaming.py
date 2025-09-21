"""
Debug script to test streaming response format for document queries
"""
import asyncio
import json
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.pdf_indexing_service import PDFIndexingService

async def test_document_search_response():
    """Test what the backend streaming response looks like for document queries"""
    
    # Initialize PDF service
    pdf_service = PDFIndexingService("GyaniNuxeo")
    await pdf_service.initialize()
    
    # Test query
    query = "contraceptive coverage"
    print(f"🔍 Testing query: '{query}'")
    
    # Search for documents
    search_results = await pdf_service.search_documents(query, max_results=3)
    print(f"📚 Found {len(search_results)} documents")
    
    # Simulate the chat response creation
    if search_results:
        # Create the response content like the backend does
        response_content = f"Based on your query about '{query}', I found relevant information in our CVS Pharmacy knowledge base:\n\n"
        response_content += "📚 **Related Documents Found:**\n\n"
        
        for i, doc in enumerate(search_results, 1):
            response_content += f"**{i}. {doc['filename']}** (Relevance: {doc['score']})\n"
            response_content += f"*Preview:* \"{doc['snippet']}\"\n"
            response_content += f"📁 *Path:* {doc['path']}\n\n"
        
        response_content += "These documents contain detailed information about contraceptive coverage policies, member benefits, and coverage guidelines. You may want to review the specific documents for complete details."
        
        print("\n" + "="*50)
        print("📝 RESPONSE CONTENT:")
        print("="*50)
        print(response_content)
        print("="*50)
        
        # Check what the markdown conversion would look like
        # from static.js.message_renderer_test import test_markdown_conversion
        # html_content = test_markdown_conversion(response_content)
        # print("\n" + "="*50)
        # print("🎨 HTML CONTENT:")
        # print("="*50)
        # print(html_content)
        # print("="*50)
        
        # Check for the specific patterns the frontend looks for
        has_related_docs = "Related Documents" in response_content
        print(f"\n🔍 Contains 'Related Documents': {has_related_docs}")
        
        if has_related_docs:
            start_idx = response_content.find("Related Documents")
            sample = response_content[start_idx:start_idx + 200]
            print(f"📚 Document section sample: {sample}")
    
    else:
        print("❌ No documents found for query")

if __name__ == "__main__":
    asyncio.run(test_document_search_response())
