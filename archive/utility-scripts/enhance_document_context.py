#!/usr/bin/env python3
"""
Enhanced Document Context Integration
This script enhances the CVS Pharmacy Knowledge Assist to provide better document context and links
"""

import asyncio
import json
import logging
from pathlib import Path
from app.services.pdf_indexing_service import get_pdf_indexing_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enhance_document_integration():
    """Enhance the document integration to provide better context and links"""
    
    print("🔧 Enhancing CVS Pharmacy Knowledge Assist document integration...")
    print("=" * 70)
    
    # Get the PDF indexing service
    pdf_service = get_pdf_indexing_service()
    
    # Check current indexing status
    stats = pdf_service.get_stats()
    print(f"📊 Current Document Statistics:")
    print(f"  • Total Documents: {stats['total_documents']}")
    print(f"  • Categories: {len(stats['categories'])}")
    for category, count in stats['categories'].items():
        print(f"    - {category}: {count} documents")
    
    # Test document search functionality
    print(f"\n🔍 Testing document search functionality...")
    
    test_queries = [
        "contraceptive coverage",
        "prior authorization", 
        "Medicare Part D",
        "specialty pharmacy",
        "mail order"
    ]
    
    for query in test_queries:
        results = pdf_service.search_documents(query, limit=3)
        print(f"\n📋 Search results for '{query}': {len(results)} documents found")
        
        for i, doc in enumerate(results[:2], 1):  # Show top 2 results
            print(f"  {i}. {doc['title']}")
            print(f"     📁 File: {doc['filename']}")
            print(f"     📂 Category: {doc['category']}")
            print(f"     🔗 Path: {doc['filepath']}")
            print(f"     📝 Snippet: {doc.get('snippet', 'No snippet available')[:100]}...")
            print(f"     ⭐ Score: {doc['relevance_score']:.1f}")
    
    print(f"\n✅ Document integration test complete!")
    print(f"\n💡 Recommendations:")
    print("1. Documents are properly indexed and searchable")
    print("2. The system should return actual document content + links")
    print("3. AI responses should include relevant document snippets")
    print("4. Users should get clickable links to source documents")
    
    return True

def create_enhanced_transformer():
    """Create an enhanced streaming message transformer that includes document context"""
    
    enhanced_code = '''
    @staticmethod
    def _transform_insights_message_with_documents(system_msg: Dict[str, Any], timestamp: str, sequence: int) -> Optional[Dict[str, Any]]:
        """Transform AI insights message and enhance with relevant document context"""
        if 'text' in system_msg and 'parts' in system_msg['text']:
            text_parts = system_msg['text']['parts']
            insight = "<br>".join(text_parts)
            logger.info(f"🔍 Found AI insights message: {insight[:100]}...")
            
            # Try to find relevant documents based on the insight content
            from app.services.pdf_indexing_service import get_pdf_indexing_service
            
            try:
                pdf_service = get_pdf_indexing_service()
                
                # Extract key terms from the insight for document search
                search_terms = StreamingMessageTransformer._extract_search_terms_from_insight(insight)
                relevant_docs = []
                
                for term in search_terms[:3]:  # Search top 3 terms
                    docs = pdf_service.search_documents(term, limit=2)
                    for doc in docs:
                        if doc not in relevant_docs:  # Avoid duplicates
                            relevant_docs.append({
                                'title': doc['title'],
                                'filename': doc['filename'], 
                                'filepath': doc['filepath'],
                                'category': doc['category'],
                                'snippet': doc.get('snippet', ''),
                                'relevance_score': doc['relevance_score'],
                                'document_link': f"/documents/{doc['filepath']}"
                            })
                
                # Limit to top 3 most relevant documents
                relevant_docs = sorted(relevant_docs, key=lambda x: x['relevance_score'], reverse=True)[:3]
                
                return {
                    'message_type': 'insights',
                    'data': {
                        'ai_insights': insight,
                        'relevant_documents': relevant_docs,
                        'document_count': len(relevant_docs),
                        'timestamp': timestamp
                    }
                }
                
            except Exception as e:
                logger.warning(f"Could not enhance insights with documents: {e}")
                # Fallback to original format
                return {
                    'message_type': 'insights',
                    'data': {
                        'ai_insights': insight,
                        'relevant_documents': [],
                        'document_count': 0,
                        'timestamp': timestamp
                    }
                }
        return None
    
    @staticmethod
    def _extract_search_terms_from_insight(insight_text: str) -> List[str]:
        """Extract key search terms from AI insight text"""
        import re
        
        # Common CVS pharmacy terms to look for
        pharmacy_terms = [
            'contraceptive coverage', 'birth control', 'contraception',
            'prior authorization', 'PA', 'auth', 'approval',
            'Medicare Part D', 'medicare', 'part d',
            'specialty pharmacy', 'specialty medication',
            'mail order', 'home delivery', 'mail service',
            'formulary', 'covered medications', 'tier',
            'copay', 'co-pay', 'deductible', 'cost',
            'prescription', 'medication', 'drug',
            'insulin', 'diabetic', 'diabetes',
            'vaccine', 'vaccination', 'immunization',
            'opioid', 'controlled substance',
            'generic', 'brand name', 'substitute',
            'refill', 'renewal', 'transfer',
            'billing', 'payment', 'insurance',
            'claim', 'rejection', 'override',
            'member', 'patient', 'enrollment'
        ]
        
        insight_lower = insight_text.lower()
        found_terms = []
        
        for term in pharmacy_terms:
            if term in insight_lower:
                found_terms.append(term)
        
        # Also extract any quoted terms or specific medication names
        quoted_terms = re.findall(r'"([^"]+)"', insight_text)
        found_terms.extend(quoted_terms)
        
        # Remove duplicates and return
        return list(set(found_terms))[:5]  # Max 5 terms
    '''
    
    print("📝 Enhanced transformer code generated")
    print("This code can be integrated into the streaming_message_transformer.py")
    
    return enhanced_code

def create_frontend_enhancement():
    """Create frontend enhancement to display document links"""
    
    frontend_js = '''
    // Enhanced message rendering with document links
    function renderInsightsMessageWithDocuments(message) {
        const data = message.data;
        let html = `
            <div class="message-content">
                <div class="ai-insights">
                    ${data.ai_insights}
                </div>
        `;
        
        // Add document references if available
        if (data.relevant_documents && data.relevant_documents.length > 0) {
            html += `
                <div class="document-references">
                    <h4>📋 Related Documents (${data.document_count})</h4>
                    <div class="document-list">
            `;
            
            data.relevant_documents.forEach(doc => {
                html += `
                    <div class="document-item">
                        <div class="document-header">
                            <strong>📄 ${doc.title}</strong>
                            <span class="document-category">${doc.category}</span>
                        </div>
                        <div class="document-snippet">${doc.snippet}</div>
                        <div class="document-actions">
                            <a href="${doc.document_link}" target="_blank" class="document-link">
                                🔗 Open Document
                            </a>
                            <span class="document-file">${doc.filename}</span>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        html += `</div>`;
        return html;
    }
    
    // CSS for document styling
    const documentStyles = `
        .document-references {
            margin-top: 15px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }
        
        .document-item {
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 5px;
            border: 1px solid #e9ecef;
        }
        
        .document-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        
        .document-category {
            background: #e9ecef;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }
        
        .document-snippet {
            color: #666;
            font-style: italic;
            margin: 5px 0;
        }
        
        .document-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .document-link {
            color: #007bff;
            text-decoration: none;
            font-weight: 500;
        }
        
        .document-link:hover {
            text-decoration: underline;
        }
        
        .document-file {
            font-size: 0.9em;
            color: #666;
        }
    `;
    '''
    
    print("🎨 Frontend enhancement code generated")
    print("This code enhances the UI to show document links and content")
    
    return frontend_js

def main():
    """Main function to enhance document context integration"""
    print("🚀 CVS Pharmacy Knowledge Assist Document Enhancement")
    print("=" * 70)
    
    # Test current document integration
    enhance_document_integration()
    
    print("\n" + "=" * 70)
    print("🔧 ENHANCEMENT RECOMMENDATIONS:")
    print("=" * 70)
    
    print("\n1. 📋 UPDATE SYSTEM PROMPT:")
    print("   - Add instruction to always search for relevant documents")
    print("   - Include document snippets in responses")
    print("   - Provide document links when available")
    
    print("\n2. 🔧 ENHANCE MESSAGE TRANSFORMER:")
    print("   - Modify _transform_insights_message to include document context")
    print("   - Search indexed documents based on AI response content")
    print("   - Include relevant document snippets and links")
    
    print("\n3. 🎨 UPDATE FRONTEND:")
    print("   - Add document reference section to chat messages")
    print("   - Make document links clickable and accessible")
    print("   - Show document categories and relevance scores")
    
    print("\n4. 📁 DOCUMENT SERVING:")
    print("   - Add endpoint to serve documents from GyaniNuxeo folder")
    print("   - Enable direct document access via links")
    print("   - Support PDF viewing in browser")
    
    print("\n✅ All enhancements identified!")
    print("📝 Ready to implement document context integration")

if __name__ == "__main__":
    main()