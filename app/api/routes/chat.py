"""
Chat routes for CVS Pharmacy Knowledge Assist
Handles both regular chat and streaming chat endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ...models.schemas import ChatQuery, ChatResponse, ChatResponseExtract
from ...database.connection import get_db_session_dependency
from ...database.models import MessageType, User, ChatMessage
from ...repositories.chat_repository import (
    ChatConversationRepository, 
    ChatMessageRepository, 
    ChatResponseRepository
)
from ...services.message_chunk_service import MessageChunkService
from ...utils import extract_chat_response_data
import logging
import uuid
import time
import asyncio
from typing import List, Dict, Any, Optional
from ...services.service_locator import get_llm_service
from .auth import get_current_user
from ...utils.datetime_utils import utc_now
import json

logger = logging.getLogger(__name__)

router = APIRouter() 


async def create_mock_chat_response(query: ChatQuery, current_user: User) -> ChatResponse:
    """Create mock chat responses for development/testing when database is unavailable"""
    import uuid
    from datetime import datetime
    from ...services.pdf_indexing_service import get_pdf_indexing_service
    
    # Search for relevant documents FIRST
    pdf_service = get_pdf_indexing_service()
    search_results = pdf_service.search_documents(query.message, limit=5)
    
    logger.info(f"🔍 PDF Search Debug (Non-streaming) - Query: '{query.message}', Results: {len(search_results)}")
    if search_results:
        logger.info(f"🔍 Top result: {search_results[0].get('filename', 'Unknown')} - Score: {search_results[0].get('relevance_score', 0)}")
    
    # Select response based on message content, prioritizing document search results
    message_lower = query.message.lower()
    
    # Prioritize document-based responses if we have good search results
    if search_results and len(search_results) > 0 and search_results[0].get('relevance_score', 0) > 0.3:
        logger.info(f"🔍 Should use document-based response - Score: {search_results[0].get('relevance_score', 0)}")
        # Use document search to generate contextual response
        top_doc = search_results[0]
        doc_name = top_doc.get('filename', 'document')
        snippet = top_doc.get('snippet', '')
        
        logger.info(f"🔍 Message check - contains 'contraceptive': {'contraceptive' in message_lower}, contains 'coverage': {'coverage' in message_lower}")
        logger.info(f"🔍 Message check - contains 'mail order': {'mail order' in message_lower}, contains 'history': {'history' in message_lower}")
        
        if 'contraceptive' in message_lower and 'coverage' in message_lower:
            logger.info("🔍 Using contraceptive coverage response")
            response_text = f"Based on your CVS Pharmacy documents, I found specific information about contraceptive coverage. The key document '{doc_name}' provides detailed guidance on coverage policies and procedures for contraceptive medications and services."
        elif 'automatic' in message_lower and 'refill' in message_lower:
            logger.info("🔍 Using automatic refill response")
            response_text = f"I found information about the Automatic Refill Program (ARP) in your pharmacy documents. The document '{doc_name}' contains detailed procedures for managing automatic refills and member enrollment."
        elif 'prescription' in message_lower and 'label' in message_lower:
            logger.info("🔍 Using prescription label response")
            response_text = f"Your pharmacy documentation includes specific guidance on prescription labels. The document '{doc_name}' provides the current labeling requirements and procedures."
        elif 'silverscript' in message_lower:
            logger.info("🔍 Using SilverScript response")
            response_text = f"I found SilverScript-specific information in your documents. The document '{doc_name}' contains procedures for SilverScript and Blue MedicareRx enrollment and member services."
        elif 'mail order' in message_lower and ('history' in message_lower or 'payment' in message_lower):
            logger.info("🔍 Using mail order history response")
            response_text = f"I found specific information about mail order history in your pharmacy documents. The document '{doc_name}' contains detailed procedures for accessing member mail order payment history and tracking information through the Compass system."
        elif 'mail order' in message_lower:
            logger.info("🔍 Using mail order general response")
            response_text = f"I found relevant mail order information in your pharmacy documents. The document '{doc_name}' contains procedures and guidance for mail order pharmacy services and member support."
        else:
            logger.info("🔍 Using generic document-based response")
            response_text = f"I found relevant information in your CVS Pharmacy documents. The document '{doc_name}' appears to contain information related to your query about {query.message}."
    elif any(word in message_lower for word in ['credit card', 'payment', 'billing']):
        response_text = "To add a credit card to a member's profile, you'll need to access their account in Compass and navigate to the Payment Methods section. You can add, edit, or remove payment methods from there."
    elif any(word in message_lower for word in ['mail order', 'history', 'order history']):
        response_text = "To access a member's mail order history, log into Compass and search for the member. Then navigate to the Order History tab where you can view all past mail order prescriptions and their status."
    elif any(word in message_lower for word in ['transfer', 'prescription', 'mail to retail']):
        response_text = "To transfer a prescription from mail to retail, you'll need to use the prescription transfer function in Compass. Locate the prescription in the member's profile and select the transfer option to move it to their preferred retail pharmacy."
    elif any(word in message_lower for word in ['test claim', 'commercial']):
        response_text = "To submit a test claim for a commercial plan, access the Test Claim feature in Compass, enter the member information, drug details, and plan specifics. This will show you the expected coverage and copay amounts."
    else:
        # Default responses
        mock_responses = [
            "As a CVS Pharmacy Knowledge Assist, I can help you with pharmacy policies, medication coverage, member services, and prescription management. What specific topic would you like to learn about?",
            "I understand you're looking for information about pharmacy procedures. Let me provide you with the relevant details about medication coverage, prior authorizations, and member services.",
            "Thank you for your question about pharmacy operations. I can assist with prescription management, insurance coverage, formulary information, and member account services. How can I help you today?",
            "I'm here to help with CVS Pharmacy inquiries. Whether you need information about medication coverage, billing, prior authorizations, or member services, I'm ready to assist. What would you like to know?",
            "Based on your query, I can provide information about CVS pharmacy services and procedures. Let me know if you need details about specific coverage areas or member account management."
        ]
        
        if any(word in message_lower for word in ['policy', 'policies', 'procedure']):
            response_text = mock_responses[2]
        elif any(word in message_lower for word in ['coverage', 'formulary', 'benefit']):
            response_text = mock_responses[1]
        elif any(word in message_lower for word in ['help', 'assist', 'support']):
            response_text = mock_responses[3]
        else:
            response_text = mock_responses[0]
    
    # Add document references if found
    if search_results:
        response_text += "\n\n📚 **Related Documents Found:**\n"
        for i, doc in enumerate(search_results[:3], 1):
            doc_title = doc.get('filename', doc.get('title', 'Unknown Document'))
            doc_path = doc.get('file_path', doc.get('filepath', ''))
            snippet = doc.get('snippet', '')
            score = doc.get('relevance_score', 0)
            
            response_text += f"\n**{i}. {doc_title}** (Relevance: {score:.2f})\n"
            if snippet:
                response_text += f"*Preview:* \"{snippet[:150]}...\"\n"
            if doc_path:
                response_text += f"📁 *Path:* {doc_path}\n"
            response_text += "\n"
    
    # Create mock conversation ID if not provided
    conversation_id = query.conversation_id or str(uuid.uuid4())
    
    # Add this conversation to mock storage for the conversations list
    from .conversations import add_mock_conversation
    
    # Generate title from user message for mock storage
    title = query.message.strip()
    title = " ".join(title.split())  # Clean whitespace
    if len(title) > 50:
        title = title[:47].strip() + "..."
    
    add_mock_conversation(current_user.email, conversation_id, title)
    
    # Create mock response with proper ChatResponse schema
    mock_response = ChatResponse(
        success=True,
        message=response_text,  # The actual assistant response text goes in message field
        conversation_id=conversation_id
    )
    
    logger.info(f"✅ Mock response generated for user: {current_user.email}")
    return mock_response


async def create_mock_streaming_response(query: ChatQuery, current_user: User):
    """Create mock streaming responses for development/testing when database is unavailable"""
    import asyncio
    import json
    from ...services.pdf_indexing_service import get_pdf_indexing_service
    
    async def generate_mock_stream():
        """Generate mock SSE stream for CVS Pharmacy Knowledge Assist"""
        
        # Search for relevant documents FIRST
        pdf_service = get_pdf_indexing_service()
        search_results = pdf_service.search_documents(query.message, limit=3)
        
        logger.info(f"🔍 PDF Search Debug - Query: '{query.message}', Results: {len(search_results)}")
        if search_results:
            logger.info(f"🔍 Top result: {search_results[0].get('filename', 'Unknown')} - Score: {search_results[0].get('relevance_score', 0)}")
        
        # Mock CVS Pharmacy-focused responses based on user input
        message_lower = query.message.lower()
        
        # Prioritize document-based responses if we have good search results
        if search_results and len(search_results) > 0 and search_results[0].get('relevance_score', 0) > 0.3:
            logger.info(f"🔍 Should use document-based response - Score: {search_results[0].get('relevance_score', 0)}")
            # Use document search to generate contextual response
            top_doc = search_results[0]
            doc_name = top_doc.get('filename', 'document')
            snippet = top_doc.get('snippet', '')
            
            logger.info(f"🔍 Message check - contains 'contraceptive': {'contraceptive' in message_lower}, contains 'coverage': {'coverage' in message_lower}")
            logger.info(f"🔍 Message check - contains 'mail order': {'mail order' in message_lower}, contains 'history': {'history' in message_lower}")
            
            if 'contraceptive' in message_lower and 'coverage' in message_lower:
                logger.info("🔍 Using contraceptive coverage response")
                response_text = f"Based on your CVS Pharmacy documents, I found specific information about contraceptive coverage. The key document '{doc_name}' provides detailed guidance on coverage policies and procedures for contraceptive medications and services."
            elif 'automatic' in message_lower and 'refill' in message_lower:
                logger.info("🔍 Using automatic refill response")
                response_text = f"I found information about the Automatic Refill Program (ARP) in your pharmacy documents. The document '{doc_name}' contains detailed procedures for managing automatic refills and member enrollment."
            elif 'prescription' in message_lower and 'label' in message_lower:
                logger.info("🔍 Using prescription label response")
                response_text = f"Your pharmacy documentation includes specific guidance on prescription labels. The document '{doc_name}' provides the current labeling requirements and procedures."
            elif 'silverscript' in message_lower:
                logger.info("🔍 Using SilverScript response")
                response_text = f"I found SilverScript-specific information in your documents. The document '{doc_name}' contains procedures for SilverScript and Blue MedicareRx enrollment and member services."
            elif 'mail order' in message_lower and ('history' in message_lower or 'payment' in message_lower):
                logger.info("🔍 Using mail order history response")
                response_text = f"I found specific information about mail order history in your pharmacy documents. The document '{doc_name}' contains detailed procedures for accessing member mail order payment history and tracking information through the Compass system."
            elif 'mail order' in message_lower:
                logger.info("🔍 Using mail order general response")
                response_text = f"I found relevant mail order information in your pharmacy documents. The document '{doc_name}' contains procedures and guidance for mail order pharmacy services and member support."
            else:
                logger.info("🔍 Using generic document-based response")
                response_text = f"I found relevant information in your CVS Pharmacy documents. The document '{doc_name}' appears to contain information related to your query about {query.message}."
                response_text = f"I found relevant information in your CVS Pharmacy documents. The document '{doc_name}' appears to contain information related to your query about {query.message}."
        elif 'credit card' in message_lower or 'payment' in message_lower:
            response_text = "To add a credit card to a member's profile, you'll need to access their account in Compass and navigate to the Payment Methods section. You can add, edit, or remove payment methods from there. Make sure to verify the member's identity before making any changes to payment information."
        elif 'mail order' in message_lower and 'history' in message_lower:
            response_text = "To access a member's mail order history, log into Compass and search for the member using their ID or personal information. Then navigate to the Order History tab where you can view all past mail order prescriptions, their status, and tracking information."
        elif 'transfer' in message_lower and 'prescription' in message_lower:
            response_text = "To transfer a prescription from mail to retail, use the prescription transfer function in Compass. Locate the prescription in the member's profile, select the transfer option, and choose their preferred retail pharmacy. Ensure all refills are properly transferred."
        elif 'test claim' in message_lower:
            response_text = "To submit a test claim for a commercial plan, access the Test Claim feature in Compass. Enter the member information, drug details, and plan specifics. This will show you the expected coverage, copay amounts, and any potential rejections before processing the actual claim."
        elif any(word in message_lower for word in ['formulary', 'coverage', 'prior authorization']):
            response_text = "I can help you with formulary information, coverage determinations, and prior authorization processes. Our pharmacy systems provide comprehensive coverage details and can guide you through the approval process for medications requiring prior authorization."
        elif any(word in message_lower for word in ['medicare', 'part d', 'med d']):
            response_text = "For Medicare Part D questions, I can assist with enrollment, formulary coverage, low-income subsidies, coverage gaps, and billing issues. Our systems have comprehensive tools for managing Medicare Part D benefits and member inquiries."
        elif any(word in message_lower for word in ['specialty', 'specialty pharmacy']):
            response_text = "CVS Specialty Pharmacy handles complex medications requiring special handling, monitoring, or patient education. I can help you with specialty pharmacy transfers, prior authorizations, and patient support programs."
        else:
            response_text = "As your CVS Pharmacy Knowledge Assist, I'm here to help with pharmacy operations, medication coverage, member services, and prescription management. I can provide support with billing, prior authorizations, formulary information, and system navigation. What would you like to know?"
        
        # Add document references if found
        if search_results:
            logger.info(f"🔍 Adding {len(search_results)} documents to response")
            response_text += "\n\n📚 **Related Documents Found:**\n"
            for i, doc in enumerate(search_results, 1):
                doc_title = doc.get('filename', doc.get('title', 'Unknown Document'))
                doc_path = doc.get('file_path', doc.get('filepath', ''))
                snippet = doc.get('snippet', '')
                score = doc.get('relevance_score', 0)
                
                response_text += f"\n**{i}. {doc_title}** (Relevance: {score:.2f})\n"
                if snippet:
                    response_text += f"*Preview:* \"{snippet[:150]}...\"\n"
                if doc_path:
                    response_text += f"📁 *Path:* {doc_path}\n"
                response_text += "\n"
        
        conversation_id = query.conversation_id or str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        
        # Add this conversation to mock storage for the conversations list
        from .conversations import add_mock_conversation
        
        # Generate title from user message for mock storage
        title = query.message.strip()
        title = " ".join(title.split())  # Clean whitespace
        if len(title) > 50:
            title = title[:47].strip() + "..."
        
        add_mock_conversation(current_user.email, conversation_id, title)
        
        # Split response into main text and document section
        if "📚 **Related Documents Found:**" in response_text:
            main_text, documents_section = response_text.split("📚 **Related Documents Found:**", 1)
            documents_section = "📚 **Related Documents Found:**" + documents_section
        else:
            main_text = response_text
            documents_section = ""
        
        # First, stream the main text word by word
        words = main_text.split()
        current_text = ""
        
        for i, word in enumerate(words):
            current_text += word + " "
            
            # Create SSE message in the format the frontend expects
            sse_data = {
                "type": "system_message",
                "message_type": "text_response", 
                "sequence": i + 1,
                "data": {
                    "content": current_text.strip(),
                    "is_final": False
                },
                "conversation_id": conversation_id,
                "message_id": message_id,
                "timestamp": int(time.time() * 1000)
            }
            
            yield f"data: {json.dumps(sse_data)}\n\n"
            
            # Small delay to simulate streaming
            await asyncio.sleep(0.05)
        
        # Then send the complete document section as one chunk (if it exists)
        if documents_section:
            complete_text = main_text.strip() + "\n\n" + documents_section
            
            final_sse_data = {
                "type": "system_message",
                "message_type": "text_response", 
                "sequence": len(words) + 1,
                "data": {
                    "content": complete_text,
                    "is_final": True
                },
                "conversation_id": conversation_id,
                "message_id": message_id,
                "timestamp": int(time.time() * 1000)
            }
            
            yield f"data: {json.dumps(final_sse_data)}\n\n"
        else:
            # No documents, just mark the main text as final
            final_sse_data = {
                "type": "system_message",
                "message_type": "text_response", 
                "sequence": len(words),
                "data": {
                    "content": current_text.strip(),
                    "is_final": True
                },
                "conversation_id": conversation_id,
                "message_id": message_id,
                "timestamp": int(time.time() * 1000)
            }
            
            yield f"data: {json.dumps(final_sse_data)}\n\n"
        
        # Send completion message
        completion_data = {
            "type": "complete",
            "conversation_id": conversation_id,
            "message_id": message_id,
            "success": True,
            "enable_feedback": True  # This will tell the frontend to add feedback buttons
        }
        
        yield f"data: {json.dumps(completion_data)}\n\n"
        
        logger.info(f"✅ Mock streaming response completed for user: {current_user.email}")
    
    return StreamingResponse(
        generate_mock_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.post("", response_model=ChatResponse)
async def chat(
    query: ChatQuery, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Core endpoint: Natural Language → LLM → SQL → BigQuery → Visualization → Response
    Proper flow: User Message → LLM Call → AI Response → Parse & Store
    """
    
    # Check if we should use mock responses (when database/LLM unavailable)
    try:
        # Try a simple database check first
        conversation_repo = ChatConversationRepository(db)
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))  # Simple test query with proper text() wrapper
        use_database = True
    except Exception as e:
        logger.warning(f"Database unavailable, using mock chat responses: {e}")
        use_database = False
    
    if not use_database:
        # Return mock chat responses for development/testing
        return await create_mock_chat_response(query, current_user)
    
    # Initialize repositories
    conversation_repo = ChatConversationRepository(db)
    message_repo = ChatMessageRepository(db)
    response_repo = ChatResponseRepository(db)
    
    try:
        processing_start_time = utc_now()
        
        # Debug: Log incoming request details
        logger.info(f"📥 Chat request received - Message: '{query.message[:50]}...' | ConversationID: {query.conversation_id or 'None'} | User: {current_user.email}")

        # Step 1: Handle conversation selection or creation
        conversation = None
        if query.conversation_id:
            # Use existing conversation
            logger.info(f"🔍 Looking up existing conversation: {query.conversation_id}")
            try:
                conversation_uuid = uuid.UUID(query.conversation_id)
                conversation = await conversation_repo.get_conversation_by_id(conversation_uuid)
                logger.info(f"🔍 Conversation lookup result: {conversation.id if conversation else 'None'}")
                
                if not conversation:
                    logger.warning(f"❌ Conversation {query.conversation_id} not found - this should not happen for existing conversations!")
                    return ChatResponse(
                        success=False,
                        message="Conversation not found"
                    )
                
                # Check if user owns this conversation
                if conversation.user_id != current_user.id:
                    return ChatResponse(
                        success=False,
                        message="Access denied to this conversation"
                    )
                    
            except ValueError:
                return ChatResponse(
                    success=False,
                    message="Invalid conversation ID format"
                )
        else:
            # Create a new conversation with auto-generated title from first message
            logger.info(f"🆕 Creating new conversation - no conversation_id provided")
            new_conversation_id = str(uuid.uuid4())
            
            # Generate title from first message (truncated)
            title = query.message.strip()
            title = " ".join(title.split())  # Clean whitespace
            if len(title) > 50:
                title = title[:47].strip() + "..."
            
            conversation = await conversation_repo.create_conversation(
                user_id=current_user.id,
                conversation_id=new_conversation_id,
                title=title
            )
            
            logger.info(f"✅ Created new conversation {conversation.id} with title: {title}")
        
        # Ensure we have a valid conversation at this point
        if not conversation:
            return ChatResponse(
                success=False,
                message="Failed to create or retrieve conversation"
            )
        
        # Step 2: Save user's message to database
        superclient = getattr(query, 'superclient', 'EMPLOYERS HEALTH PURCHASING CORPORATION OF OHIO (EHPCO)')
        enhanced_message = f"SuperClient: {superclient}. User Query: {query.message}"
        
        user_message = await message_repo.create_message(
            conversation_id=conversation.id,
            user_id=current_user.id,
            message_type=MessageType.USER,
            content=query.message,
            superclient=superclient,
            enhanced_message=enhanced_message
        )
        
        # Commit user message to database first
        await db.commit()
        logger.info(f"User message saved: {user_message.id}")
        
        # Step 3: Check LLM service availability (no DB writes on failure)
        llm_service = get_llm_service()
        if not llm_service:
            logger.error("Analytics service not available")
            return ChatResponse(
                success=False,
                message="Analytics service not available. Please try again later."
            )

        # Step 4: Call LLM service (no DB writes on failure)
        try:
            # Use user-specific conversation ID for LLM context
            llm_response = llm_service.chat(enhanced_message, f"user-{conversation.conversation_id}", "cvs-pharmacy-knowledge-assist")
            logger.info(f"LLM response received for message: {user_message.id}")
        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            return ChatResponse(
                success=False,
                message="Oops! Error encountered processing your query. Please try again."
            )
        
        # Step 5: We have an actual LLM response - now create ChatResponse record
        response_id = uuid.uuid4()
        
        # Step 6: Extract structured data from the LLM response
        try:
            extracted_data = extract_chat_response_data(llm_response, str(response_id))
            processing_end_time = utc_now()
            processing_time_ms = int((processing_end_time - processing_start_time).total_seconds() * 1000)
            logger.info(f"Extracted data successfully for response_id {response_id} (took {processing_time_ms}ms)")

            # Step 7a: Create ChatMessage(ASSISTANT) for conversation history with enhanced data
            success_message = f"Successfully analyzed: '{query.message}'"
            
            # Prepare response metadata
            response_metadata = {
                "processing_time_ms": processing_time_ms,
                "success": True,
                "response_id": str(response_id),
                "extraction_success": True
            }
            
            
            assistant_message = await message_repo.create_message(
                conversation_id=conversation.id,
                user_id=current_user.id,
                message_type=MessageType.ASSISTANT,
                content=success_message,
                superclient=superclient,
                enhanced_message=None,  # Assistant messages don't need enhancement
                sql_query=extracted_data.generated_sql,
                chart_config=None, # TODO store chart config without data
                ai_insights=extracted_data.ai_insights,
                response_metadata=response_metadata,
                result_schema=None  # TODO store schema from executed results.
            )

            

            
            await db.commit()
            logger.info(f"Assistant message and chat response saved successfully: {response_id}")

            # Create standardized assistant message data for frontend consistency
            from ...models.schemas import MessageDetail
            
            
            # FUTURE: Create standardized assistant message data for frontend consistency
            # This will be used when we implement the new MessageDetail-based rendering
            # chart_config_for_message = None
            # if extracted_data.chart_config:
            #     chart_config_for_message = extracted_data.chart_config.model_dump()
            # 
            # standardized_message = MessageDetail(
            #     id=str(assistant_message.id),
            #     message_type="assistant",
            #     content=success_message,
            #     created_at=assistant_message.created_at,
            #     superclient=superclient,
            #     sql_query=extracted_data.generated_sql,
            #     chart_config=chart_config_for_message,
            #     ai_insights=extracted_data.ai_insights,
            #     response_metadata=response_metadata,
            #     result_data=extracted_data.result_data,
            #     result_schema=extracted_data.result_schema,
            #     data_status="complete" if extracted_data.result_data else "no_data",
            #     data_message=None
            # )
            
            logger.info(f"🎉 Returning successful response with conversation_id: {conversation.id}")
            
            # FUTURE: Write standardized message to output file
            # try:
            #     output_file = f"output/chat_message_{response_id}.json"
            #     with open(output_file, "w", encoding="utf-8") as f:
            #         message_dict = standardized_message.model_dump()
            #         json.dump(message_dict, f, indent=2, ensure_ascii=False, default=str)
            #     logger.info(f"✅ Saved standardized message to {output_file}")
            # except Exception as file_error:
            #     logger.warning(f"⚠️ Failed to save output file: {file_error}")

            # Return data in the old working format (matches old frontend expectations)
            return ChatResponse(
                success=True,
                message=success_message,
                conversation_id=str(conversation.id),
                data=extracted_data
            )

        except Exception as extraction_error:
            logger.error(f"Data extraction failed: {extraction_error}")
            
            # Calculate processing time even for extraction failures  
            processing_end_time = utc_now()
            processing_time_ms = int((processing_end_time - processing_start_time).total_seconds() * 1000)
            
            # Create ChatMessage(ASSISTANT) and ChatResponse even for extraction failures
            try:
                # Create ChatMessage(ASSISTANT) for conversation history
                error_message = f"Analysis completed but data extraction failed: {str(extraction_error)}"
                
                # Prepare error response metadata
                error_response_metadata = {
                    "processing_time_ms": processing_time_ms,
                    "success": False,
                    "response_id": str(response_id),
                    "extraction_success": False,
                    "error_type": "data_extraction_failure",
                    "error_details": str(extraction_error)
                }
                
                assistant_message = await message_repo.create_message(
                    conversation_id=conversation.id,
                    user_id=current_user.id,
                    message_type=MessageType.ASSISTANT,
                    content=error_message,
                    superclient=superclient,
                    enhanced_message=None,
                    sql_query=None,  # No SQL since extraction failed
                    chart_config=None,  # No chart since extraction failed
                    ai_insights=None,  # No insight since extraction failed
                    response_metadata=error_response_metadata
                )

                # Create ChatResponse with extraction failure (we still have LLM response)
                chat_response = await response_repo.create_response(
                    response_id=response_id,
                    message_id=assistant_message.id,  # Link to assistant message
                    success=False,
                    error_message=f"Data extraction failed: {str(extraction_error)}",
                    generated_sql=None,  # No SQL since extraction failed
                    insight=None,  # No insight since extraction failed
                    processing_time_ms=processing_time_ms
                )
                
                await db.commit()
                logger.info(f"Assistant message and chat response saved with extraction error: {response_id}")
                
                logger.info(f"⚠️ Returning error response with conversation_id: {conversation.id}")
                return ChatResponse(
                    success=False,
                    message=error_message,
                    conversation_id=str(conversation.id)
                )
                
            except Exception as repo_error:
                logger.error(f"Failed to save ChatResponse with extraction error: {repo_error}")
                await db.rollback()
                
                return ChatResponse(
                    success=False,
                    message=f"Analysis completed but data extraction failed: {str(extraction_error)}"
                )

    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        await db.rollback()
        
        return ChatResponse(
            success=False,
            message=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/stream")
async def stream_chat(
    query: ChatQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Stream chat responses from CA API to frontend via Server-Sent Events
    
    This endpoint:
    1. Receives chat query from frontend
    2. Streams responses from CA API as they arrive
    3. Sends individual system message objects to frontend via SSE
    4. Stores complete response in database when streaming finishes
    """
    logger.info(f"🌊 Streaming chat request received - Message: '{query.message[:50]}...' | User: {current_user.email}")
    
    # Check if we should use mock streaming responses (when database/LLM unavailable)
    try:
        # Try a simple database check first
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))  # Simple test query with proper text() wrapper
        use_database = True
    except Exception as e:
        logger.warning(f"Database unavailable, using mock streaming responses: {e}")
        use_database = False
    
    if not use_database:
        # Return mock streaming responses for development/testing
        return await create_mock_streaming_response(query, current_user)
    
    # Initialize repositories
    conversation_repo = ChatConversationRepository(db)
    message_repo = ChatMessageRepository(db)
    response_repo = ChatResponseRepository(db)
    
    try:
        processing_start_time = utc_now()
        
        # Step 1: Handle conversation selection or creation
        conversation = None
        if query.conversation_id:
            # Use existing conversation with proper validation
            logger.info(f"🔍 Looking up existing conversation: {query.conversation_id}")
            try:
                conversation_uuid = uuid.UUID(query.conversation_id)
                conversation = await conversation_repo.get_conversation_by_id(conversation_uuid)
                logger.info(f"🔍 Conversation lookup result: {conversation.id if conversation else 'None'}")
                
                if not conversation:
                    logger.warning(f"❌ Conversation {query.conversation_id} not found for streaming!")
                    logger.info("🔄 Creating new conversation since existing one not found")
                    # Instead of falling back to mock, create a new conversation
                    conversation = None
                
                # Check if user owns this conversation
                if conversation and conversation.user_id != current_user.id:
                    logger.warning(f"❌ Access denied to conversation {query.conversation_id} for user {current_user.email}")
                    logger.info("🔄 Creating new conversation due to access denied")
                    conversation = None
                    
            except ValueError:
                logger.warning(f"❌ Invalid conversation ID format: {query.conversation_id}")
                logger.info("🔄 Creating new conversation due to invalid ID format")
                # Instead of falling back to mock, create a new conversation
                conversation = None
        if not conversation:
            # Create new conversation
            conversation_id = str(uuid.uuid4())
            try:
                conversation = await conversation_repo.create_conversation(
                    conversation_id=conversation_id,
                    user_id=current_user.id,
                    title=query.message[:100]  # Use first 100 chars as title
                )
            except Exception as conv_error:
                logger.error(f"❌ Failed to create conversation: {conv_error}")
                # Continue without conversation record - still use LLM service
                logger.info("🔄 Continuing with LLM service without conversation record")
                conversation = None

        # Step 2: Create user message record (if we have a conversation)
        user_message = None
        if conversation:
            try:
                user_message = await message_repo.create_message(
                    conversation_id=conversation.id,  # Use primary key UUID, not the string field
                    user_id=current_user.id,
                    message_type=MessageType.USER,
                    content=query.message,
                    superclient=query.superclient or "Default"
                )
            except Exception as user_msg_error:
                logger.error(f"❌ Failed to create user message: {user_msg_error}")
                logger.info("🔄 Continuing with LLM service without message record")
                user_message = None

        # Step 3: Get LLM service (now supports streaming)
        llm_service = get_llm_service()
        if not llm_service:
            logger.warning("LLM service not available, falling back to mock streaming")
            return await create_mock_streaming_response(query, current_user)

        # Step 4: Create assistant message record early for chunk storage (if we have a conversation)
        assistant_message = None
        if conversation:
            try:
                assistant_message = await message_repo.create_message(
                    conversation_id=conversation.id,
                    user_id=current_user.id,
                    message_type=MessageType.ASSISTANT,
                    content="Processing streaming response...",  # Will be updated after streaming
                    superclient=query.superclient or "Default"
                )
            except Exception as assist_msg_error:
                logger.error(f"❌ Failed to create assistant message: {assist_msg_error}")
                logger.info("🔄 Continuing with LLM service without assistant message record")
                assistant_message = None
        
        # Initialize chunk service for storing chunks during streaming
        chunk_service = MessageChunkService(db)
        
        # Step 5: Define streaming response generator
        async def generate_stream():
            """Generator function for Server-Sent Events"""
            response_id = uuid.uuid4()
            chunk_sequence = 0
            collected_chunks_info = []
            
            try:
                # Send initial status
                yield f"data: {json.dumps({'type': 'status', 'message': 'Starting CA API request...', 'timestamp': utc_now().isoformat()})}\n\n"
                
                # Stream from CA API using data agent (like regular chat)
                async for message_chunk in llm_service.stream_chat(
                    user_message=query.message,
                    conversation_id=None,  # Could be extended to support conversation context later  
                    data_agent_id="cvs-pharmacy-knowledge-assist",   # Explicitly use the data agent
                    use_conversation=False
                ):
                    # Only process system_message chunks (ignore status/error messages)
                    if message_chunk.get("type") == "system_message":
                        chunk_sequence += 1
                        
                        # Store transformed chunk BEFORE sending to frontend (if we have assistant message)
                        # This ensures we capture the data even if streaming fails later
                        if assistant_message:
                            try:
                                store_result = await chunk_service.store_transformed_chunk(
                                    message_id=str(assistant_message.id),
                                    chunk_sequence=chunk_sequence,
                                    transformed_chunk=message_chunk
                                )
                                
                                if store_result["success"]:
                                    logger.info(f"✅ Stored chunk {chunk_sequence} ({message_chunk.get('message_type', 'unknown')}) for message {assistant_message.id}")
                                    collected_chunks_info.append({
                                        "sequence": chunk_sequence,
                                        "type": message_chunk.get("message_type"),
                                        "chunks_stored": store_result.get("chunks_stored", 1)
                                    })
                                else:
                                    logger.warning(f"⚠️ Failed to store chunk {chunk_sequence}: {store_result.get('error', 'Unknown error')}")
                                    
                            except Exception as chunk_store_error:
                                # Continue streaming even if chunk storage fails (per requirement)
                                logger.error(f"❌ Exception storing chunk {chunk_sequence}: {chunk_store_error}")
                        else:
                            logger.debug(f"📡 Skipping chunk storage (no assistant message) for chunk {chunk_sequence}")
                    
                    # Send each chunk to frontend (regardless of storage success)
                    chunk_data = {
                        "type": "chunk",
                        "response_id": str(response_id),
                        "conversation_id": str(conversation.id) if conversation else None,
                        "data": message_chunk,
                        "timestamp": utc_now().isoformat()
                    }
                    
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                    # Add small delay to prevent overwhelming the connection
                    await asyncio.sleep(0.05)

                # Calculate final statistics
                total_chunks_stored = sum(chunk_info.get("chunks_stored", 0) for chunk_info in collected_chunks_info)
                processing_time = (utc_now() - processing_start_time).total_seconds() * 1000
                
                # Send completion signal
                completion_data = {
                    "type": "complete",
                    "response_id": str(response_id),
                    "conversation_id": str(conversation.id) if conversation else None,
                    "message_id": str(assistant_message.id) if assistant_message else None,
                    "message": "Streaming completed successfully",
                    "total_chunks": len(collected_chunks_info),
                    "total_chunks_stored": total_chunks_stored,
                    "chunk_types": [chunk_info["type"] for chunk_info in collected_chunks_info],
                    "timestamp": utc_now().isoformat()
                }
                
                yield f"data: {json.dumps(completion_data)}\n\n"
                
                # Step 6: Update assistant message with final content and create response record
                try:
                    if assistant_message and collected_chunks_info:
                        # Update the assistant message with final content
                        final_content = f"Streaming response completed with {len(collected_chunks_info)} chunks: {', '.join(set(chunk_info['type'] for chunk_info in collected_chunks_info if chunk_info['type']))}"
                        
                        # Update assistant message content  
                        from sqlalchemy import update
                        stmt = (
                            update(ChatMessage)
                            .where(ChatMessage.id == assistant_message.id)
                            .values(content=final_content)
                        )
                        await db.execute(stmt)
                        
                        # Create response record for tracking
                        await response_repo.create_response(
                            response_id=response_id,
                            message_id=assistant_message.id,
                            success=True,
                            processing_time_ms=int(processing_time),
                            # Note: raw_response is no longer used since chunks are stored individually
                            generated_sql=None,  # Individual chunks contain this data
                            insight=None         # Individual chunks contain this data
                        )
                        
                        # Commit all changes
                        await db.commit()
                        
                        logger.info(f"✅ Updated assistant message and created response record. Total chunks stored: {total_chunks_stored}")
                    else:
                        # No chunks were processed, mark as failed
                        await response_repo.create_response(
                            response_id=response_id,
                            message_id=assistant_message.id,
                            success=False,
                            error_message="No chunks were processed during streaming",
                            processing_time_ms=int(processing_time)
                        )
                        await db.commit()
                        logger.warning(f"⚠️ No chunks processed for message {assistant_message.id}")
                
                except Exception as db_error:
                    logger.error(f"Failed to update assistant message and response record: {db_error}")
                    await db.rollback()
                    
                    # Send error notification to frontend
                    error_data = {
                        "type": "storage_error", 
                        "message": "Streaming completed but final database update failed",
                        "error": str(db_error),
                        "timestamp": utc_now().isoformat()
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                
            except Exception as stream_error:
                logger.error(f"Streaming error: {stream_error}")
                error_data = {
                    "type": "error",
                    "message": f"Streaming failed: {str(stream_error)}",
                    "timestamp": utc_now().isoformat()
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        # Return StreamingResponse with Server-Sent Events
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streaming chat setup failed: {e}")
        logger.info("🔄 Falling back to mock streaming response due to setup failure")
        return await create_mock_streaming_response(query, current_user)
        return await create_mock_streaming_response(query, current_user)
