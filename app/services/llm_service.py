"""
LLM Service for Google Gemini Conversational Analytics API
Provides a simple interface for data agents, conversations, and chat functionality
"""

import json
import logging
import requests
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
from ..config import config
import google.auth
import google.auth.transport.requests
import requests
from datetime import datetime, timedelta
from ..utils.streaming_message_transformer import streaming_transformer
from .pdf_indexing_service import PDFIndexingService

logger = logging.getLogger(__name__)


class LLMService:
    """Service for Google Gemini Conversational Analytics API operations"""
    
    def __init__(self):
        """Initialize LLM service with authentication and configuration"""
        logger.info("Initializing LLM service...")
        self.base_url = config.BASE_URL
        self.location = config.LOCATION
        self.billing_project = config.BILLING_PROJECT
        self.data_agent_id: Optional[str] = None
        self.credentials = self._get_credentials()
        
        # Initialize PDF indexing service for local document search
        self.pdf_service = PDFIndexingService()
        self.pdf_service.load_index()
        logger.info("PDF indexing service loaded for document search")
        
        # Initialize headers even if credentials fail to prevent AttributeError
        self.headers = {
            "Content-Type": "application/json",
        }
        
        if self.credentials and self.credentials.token:
            self.headers["Authorization"] = f"Bearer {self.credentials.token}"
            logger.info(f"LLM Service initialized successfully for project: {self.billing_project}")
        else:
            logger.warning("LLM service initialized without credentials - will attempt to get them later")
        
        

    

    def _get_credentials(self):
        try:
            # First try default credentials
            logger.info("Getting programmatic access token...")
            try:
                credentials, _ = google.auth.default()
                
                if credentials:
                    try:
                        logger.info("Refreshing credentials...")
                        credentials.refresh(google.auth.transport.requests.Request())
                        logger.info(f"Credentials refreshed successfully: {credentials.token}")
                        return credentials
                    except Exception as e:
                        logger.error(f"Error refreshing credentials: {e}")
                        
            except Exception as e:
                logger.warning(f"Default credentials failed: {e}")
                
            # Fallback: Try to use gcloud user credentials by subprocess
            logger.info("Attempting to use gcloud user credentials...")
            import subprocess
            import os
            
            # Get access token from gcloud
            gcloud_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Google", "Cloud SDK", "google-cloud-sdk", "bin", "gcloud.cmd")
            
            if os.path.exists(gcloud_path):
                result = subprocess.run([gcloud_path, "auth", "print-access-token"], 
                                     capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    access_token = result.stdout.strip()
                    
                    # Create a mock credentials object
                    class MockCredentials:
                        def __init__(self, token):
                            self.token = token
                            self.expired = False
                            self.expiry = None
                    
                    logger.info("Successfully obtained access token from gcloud")
                    return MockCredentials(access_token)
                else:
                    logger.error(f"Failed to get access token from gcloud: {result.stderr}")
            else:
                logger.error(f"gcloud not found at: {gcloud_path}")
                        
            return None
            
        except Exception as e:
            logger.error(f"Error obtaining credentials: {e}")
            return None

    def check_credentials(self):
        logger.info("Checking if credentials expired...")
        
        # Check if credentials exist first
        if not self.credentials:
            logger.warning("No credentials available, attempting to get new ones...")
            self.credentials = self._get_credentials()
            if self.credentials and self.credentials.token:
                self.headers["Authorization"] = f"Bearer {self.credentials.token}"
                logger.info("Successfully obtained new credentials")
            else:
                logger.error("Failed to get credentials")
            return
        
        # Check if credentials have expiry and if they're expired or expiring soon
        if hasattr(self.credentials, 'expiry') and self.credentials.expiry:
            credentials_expire_soon = datetime.now() > (self.credentials.expiry - timedelta(minutes=10)) # expires in less than 10 minutes
            if self.credentials.expired or credentials_expire_soon:
                logger.info("Credentials are expired or expire soon, refreshing...")
                self.credentials = self._get_credentials()
                if self.credentials and self.credentials.token:
                    self.headers["Authorization"] = f"Bearer {self.credentials.token}"
                    logger.info("Successfully refreshed credentials")
                else:
                    logger.error("Failed to refresh credentials")
            else:
                logger.info("Credentials are still valid")
        else:
            # For mock credentials (from gcloud), always refresh to get latest token
            logger.info("Refreshing gcloud user credentials...")
            self.credentials = self._get_credentials()
            if self.credentials and self.credentials.token:
                self.headers["Authorization"] = f"Bearer {self.credentials.token}"
                logger.info("Successfully refreshed gcloud credentials")
            else:
                logger.error("Failed to refresh gcloud credentials")

    def search_relevant_documents(self, user_message: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents based on user message
        
        Args:
            user_message: The user's question or request
            limit: Maximum number of documents to return
            
        Returns:
            List of relevant documents with context
        """
        try:
            logger.info(f"🔍 Searching for documents relevant to: '{user_message[:100]}...'")
            
            # Search for relevant documents
            results = self.pdf_service.search_documents(user_message, limit=limit)
            
            if results:
                logger.info(f"📚 Found {len(results)} relevant documents")
                for i, doc in enumerate(results, 1):
                    logger.info(f"  {i}. {doc['title']} (score: {doc['relevance_score']:.1f})")
            else:
                logger.info("📚 No relevant documents found")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error searching documents: {e}")
            return []

    def enhance_user_message_with_context(self, user_message: str) -> str:
        """
        Enhance user message with relevant document context
        
        Args:
            user_message: Original user message
            
        Returns:
            Enhanced message with document context
        """
        try:
            # Search for relevant documents
            relevant_docs = self.search_relevant_documents(user_message, limit=3)
            
            if not relevant_docs:
                logger.info("📝 No document context added - no relevant docs found")
                return user_message
            
            # Build context from documents
            context_parts = []
            context_parts.append("RELEVANT DOCUMENT CONTEXT:")
            context_parts.append("=" * 50)
            
            for i, doc in enumerate(relevant_docs, 1):
                context_parts.append(f"\nDocument {i}: {doc['title']}")
                context_parts.append(f"File: {doc['filename']}")
                context_parts.append(f"Category: {doc['category']}")
                
                # Get more comprehensive content from the document
                full_doc_info = self.pdf_service.get_document_info(doc['filepath'])
                if full_doc_info and 'full_text' in full_doc_info:
                    full_text = full_doc_info['full_text']
                    if full_text and len(full_text.strip()) > 0:
                        # Extract a larger, more meaningful snippet
                        snippet = self.pdf_service.extract_relevant_snippet(
                            user_message.lower(), full_text, snippet_length=800
                        )
                        if snippet:
                            context_parts.append(f"Content: {snippet}")
                        else:
                            # If no specific snippet found, use first part of document
                            preview = full_text[:600].strip()
                            if preview:
                                context_parts.append(f"Content Preview: {preview}...")
                            else:
                                context_parts.append("Content: [Document content could not be extracted]")
                    else:
                        context_parts.append("Content: [No text content available]")
                else:
                    # Fallback to basic snippet if full document not available
                    if 'snippet' in doc and doc['snippet']:
                        context_parts.append(f"Content: {doc['snippet']}")
                    else:
                        context_parts.append("Content: [Document metadata only]")
                
                context_parts.append(f"Relevance Score: {doc['relevance_score']:.1f}")
                context_parts.append("-" * 30)
            
            # Combine context with user message
            enhanced_message = f"""
{chr(10).join(context_parts)}

USER QUESTION: {user_message}

INSTRUCTIONS: 
- Answer the user's question using the relevant document context provided above
- Use the actual content from the documents to provide specific, detailed information
- Include direct quotes or specific information from the document content when available
- Reference the specific documents by title and filename
- If the document content doesn't contain the exact information needed, say so clearly
- Provide as much relevant detail as possible from the document content
- Always mention which specific documents you're referencing
"""
            
            logger.info(f"📝 Enhanced user message with context from {len(relevant_docs)} documents")
            return enhanced_message
            
        except Exception as e:
            logger.error(f"❌ Error enhancing message with context: {e}")
            return user_message

    def create_data_agent(self, data_agent_id: str, system_instruction: str, 
                         dataset_id: str = None, table_id: str = None) -> Dict[str, Any]:
        """
        Create a data agent for the billing project
        
        Args:
            data_agent_id: Unique identifier for the data agent
            system_instruction: YAML content to guide agent behavior
            dataset_id: BigQuery dataset ID (defaults to config value)
            table_id: BigQuery table ID (defaults to config value)
            
        Returns:
            Dict containing the created data agent response
        """
        self.check_credentials()
        if not data_agent_id or not system_instruction:
            raise ValueError("Data agent ID and system instruction are required")

        # Use provided values or fall back to config defaults
        dataset_id = dataset_id or getattr(config, 'BQ_DATASET', None)
        table_id = table_id or getattr(config, 'BQ_TABLE', None)
        
        if not dataset_id or not table_id:
            raise ValueError("BigQuery dataset and table IDs are required")

        bigquery_data_sources = {
            "bq": {
                "tableReferences": [
                    {
                        "projectId": self.billing_project,
                        "datasetId": dataset_id,
                        "tableId": table_id
                    }
                ]
            }
        }

        data_agent_url = f"{self.base_url}/v1alpha/projects/{self.billing_project}/locations/{self.location}/dataAgents"
        
        data_agent_payload = {
            "name": f"projects/{self.billing_project}/locations/{self.location}/dataAgents/{data_agent_id}",
            "description": f"Data agent for {dataset_id}.{table_id} analysis",
            "data_analytics_agent": {
                "published_context": {
                    "datasource_references": bigquery_data_sources,
                    "system_instruction": system_instruction.strip(),
                    "options": {
                        "analysis": {
                            "python": {
                                "enabled": True
                            }
                        }
                    }
                }
            }
        }

        params = {"data_agent_id": data_agent_id}

        try:
            response = requests.post(
                data_agent_url, 
                params=params, 
                json=data_agent_payload, 
                headers=self.headers
            )
            
            if response.status_code == 200:
                self.data_agent_id = data_agent_id
                logger.info(f"Data Agent '{data_agent_id}' created successfully")
                return response.json()
            else:
                logger.error(f"Failed to create Data Agent: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def get_data_agent(self, data_agent_id: str) -> Dict[str, Any]:
        """
        Get a data agent for the billing project
        
        Args:
            data_agent_id: ID of the data agent to retrieve
            
        Returns:
            Dict containing the data agent details
        """
        self.check_credentials()

        data_agent_url = f"{self.base_url}/v1alpha/projects/{self.billing_project}/locations/{self.location}/dataAgents/{data_agent_id}"

        try:
            response = requests.get(data_agent_url, headers=self.headers)
            
            if response.status_code == 200:
                self.data_agent_id = data_agent_id
                logger.info(f"Data Agent '{data_agent_id}' retrieved successfully")
                return response.json()
            else:
                logger.error(f"Failed to retrieve Data Agent: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def update_data_agent(self, data_agent_id: str, system_instruction: str, 
                         dataset_id: str = None, table_id: str = None) -> Dict[str, Any]:
        """
        Update a data agent's system instruction and other properties
        
        Args:
            data_agent_id: ID of the data agent to update
            system_instruction: New YAML content to guide agent behavior
            dataset_id: BigQuery dataset ID (defaults to config value)
            table_id: BigQuery table ID (defaults to config value)
            
        Returns:
            Dict containing the updated data agent response
        """
        self.check_credentials()

        if not data_agent_id or not system_instruction:
            raise ValueError("Data agent ID and system instruction are required")

        # Use provided values or fall back to config defaults
        dataset_id = dataset_id or getattr(config, 'BQ_DATASET', None)
        table_id = table_id or getattr(config, 'BQ_TABLE', None)
        
        if not dataset_id or not table_id:
            raise ValueError("BigQuery dataset and table IDs are required")

        bigquery_data_sources = {
            "bq": {
                "tableReferences": [
                    {
                        "projectId": self.billing_project,
                        "datasetId": dataset_id,
                        "tableId": table_id
                    }
                ]
            }
        }

        data_agent_url = f"{self.base_url}/v1alpha/projects/{self.billing_project}/locations/{self.location}/dataAgents/{data_agent_id}"
        
        update_payload = {
            "data_analytics_agent": {
                "published_context": {
                    "datasource_references": bigquery_data_sources,
                    "system_instruction": system_instruction.strip(),
                    "options": {
                        "analysis": {
                            "python": {
                                "enabled": True
                            }
                        }
                    }
                }
            }
        }

        fields = ["data_analytics_agent"]
        params = {
            "updateMask": ",".join(fields)
        }

        try:
            response = requests.patch(
                data_agent_url, 
                json=update_payload, 
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                self.data_agent_id = data_agent_id  # Set the data_agent_id when update succeeds
                logger.info(f"Data Agent '{data_agent_id}' updated successfully")
                return response.json()
            else:
                logger.error(f"Failed to update Data Agent: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def create_conversation(self, conversation_id: str, data_agent_id: str = None) -> Dict[str, Any]:
        """
        Create a conversation for the billing project
        
        Args:
            conversation_id: Unique identifier for the conversation
            data_agent_id: ID of the data agent to use (defaults to current agent)
            
        Returns:
            Dict containing the created conversation response
        """
        agent_id = data_agent_id or self.data_agent_id
        if not agent_id:
            raise ValueError("Data agent ID is required. Create or get a data agent first.")

        conversation_url = f"{self.base_url}/v1alpha/projects/{self.billing_project}/locations/{self.location}/conversations"
        
        conversation_payload = {
            "agents": [
                f"projects/{self.billing_project}/locations/{self.location}/dataAgents/{agent_id}"
            ],
            "name": f"projects/{self.billing_project}/locations/{self.location}/conversations/{conversation_id}"
        }
        
        params = {"conversation_id": conversation_id}

        try:
            response = requests.post(
                conversation_url, 
                headers=self.headers, 
                params=params, 
                json=conversation_payload
            )
            
            if response.status_code == 200:
                logger.info(f"Conversation '{conversation_id}' created successfully")
                return response.json()
            else:
                logger.error(f"Failed to create conversation: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get a conversation for the billing project
        
        Args:
            conversation_id: ID of the conversation to retrieve
            
        Returns:
            Dict containing the conversation details
        """
        conversation_url = f"{self.base_url}/v1alpha/projects/{self.billing_project}/locations/{self.location}/conversations/{conversation_id}"
        
        try:
            response = requests.get(conversation_url, headers=self.headers)
            
            if response.status_code == 200:
                logger.info(f"Conversation '{conversation_id}' retrieved successfully")
                return response.json()
            else:
                logger.error(f"Failed to retrieve conversation: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def chat(self, user_message: str, conversation_id: str = None, 
             data_agent_id: str = None, use_conversation: bool = False) -> Dict[str, Any]:
        """
        Chat with the data agent
        
        Args:
            user_message: The user's question or request
            conversation_id: ID of the conversation (required if use_conversation=True)
            data_agent_id: ID of the data agent to use (defaults to current agent)
            use_conversation: Whether to use conversation context (defaults to True)
            
        Returns:
            Dict containing the chat response
        """
        self.check_credentials()

        agent_id = data_agent_id or self.data_agent_id
        if not agent_id:
            raise ValueError("Data agent ID is required. Create or get a data agent first.")

        if use_conversation and not conversation_id:
            raise ValueError("Conversation ID is required when using conversation context")

        # Enhance user message with document context
        enhanced_message = self.enhance_user_message_with_context(user_message)

        chat_url = f"{self.base_url}/v1alpha/projects/{self.billing_project}/locations/{self.location}:chat"
        
        chat_payload = {
            "parent": f"projects/{self.billing_project}/locations/{self.location}",
            "messages": [
                {
                    "userMessage": {
                        "text": enhanced_message
                    }
                }
            ]
        }

        if use_conversation and conversation_id:
            # Use conversation context (stateful)
            chat_payload["conversation_reference"] = {
                "conversation": f"projects/{self.billing_project}/locations/{self.location}/conversations/{conversation_id}",
                "data_agent_context": {
                    "data_agent": f"projects/{self.billing_project}/locations/{self.location}/dataAgents/{agent_id}"
                }
            }
        else:
            # Use data agent context directly (stateless)
            chat_payload["data_agent_context"] = {
                "data_agent": f"projects/{self.billing_project}/locations/{self.location}/dataAgents/{agent_id}"
            }

        try:
            logger.info(f"\n**********\n\nChat payload: {chat_payload}\n\n\n**********\n\n")
            response = requests.post(chat_url, headers=self.headers, json=chat_payload)
            
            if response.status_code == 200:
                logger.info("Chat completed successfully")
                return response.json()
            else:
                logger.error(f"Chat failed: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise



    async def stream_chat(self, user_message: str, conversation_id: str = None,
                         data_agent_id: str = None, use_conversation: bool = False,
                         system_instruction: str = None):
        """
        Stream chat responses (like chat() method but with streaming)
        
        Args:
            user_message: The user's question or request
            conversation_id: ID of the conversation (required if use_conversation=True)
            data_agent_id: ID of the data agent to use (defaults to current agent)
            use_conversation: Whether to use conversation context (defaults to False)
            system_instruction: System instruction for inline context (if not using data agent)
            
        Yields:
            Dict containing individual system message objects as they arrive
        """
        self.check_credentials()

        agent_id = data_agent_id or self.data_agent_id
        
        # If no agent_id, raise error (we removed inline context methods)
        if not agent_id:
            logger.error("❌ No data agent ID available for streaming chat")
            yield {
                "error": True,
                "message": "Data agent ID is required for streaming. Please configure a data agent first.",
                "timestamp": datetime.now().isoformat()
            }
            return

        if agent_id:
            # Use data agent approach (like regular chat method)
            if use_conversation and not conversation_id:
                raise ValueError("Conversation ID is required when using conversation context")

            # Enhance user message with document context
            enhanced_message = self.enhance_user_message_with_context(user_message)

            chat_url = f"{self.base_url}/v1alpha/projects/{self.billing_project}/locations/{self.location}:chat"
            
            chat_payload = {
                "parent": f"projects/{self.billing_project}/locations/{self.location}",
                "messages": [
                    {
                        "userMessage": {
                            "text": enhanced_message
                        }
                    }
                ]
            }

            if use_conversation and conversation_id:
                # Use conversation context (stateful)
                chat_payload["conversation_reference"] = {
                    "conversation": f"projects/{self.billing_project}/locations/{self.location}/conversations/{conversation_id}",
                    "data_agent_context": {
                        "data_agent": f"projects/{self.billing_project}/locations/{self.location}/dataAgents/{agent_id}"
                    }
                }
            else:
                # Use data agent context directly (stateless)
                chat_payload["data_agent_context"] = {
                    "data_agent": f"projects/{self.billing_project}/locations/{self.location}/dataAgents/{agent_id}"
                }

        try:
            logger.info("🌊 Starting streaming chat request to CA API...")
            logger.info(f"\n**********\n\nStreaming Chat payload: {chat_payload}\n\n\n**********\n\n")
            
            # Make streaming request to CA API (same endpoint as regular chat)
            response = requests.post(
                chat_url, 
                headers=self.headers, 
                json=chat_payload,
                stream=True
            )
            
            if response.status_code != 200:
                logger.error(f"Streaming chat failed: {response.status_code} - {response.text}")
                yield {
                    "error": True,
                    "status_code": response.status_code,
                    "message": f"CA API error: {response.text}"
                }
                return

            logger.info("✅ Streaming response received from CA API, processing chunks...")
            
            # Process streaming response using CA API format (JSON array streaming)
            # Based on the official CA API documentation helper function
            accumulator = ""
            message_count = 0
            raw_chunk_count = 0
            
            def is_json_valid(json_str):
                try:
                    json.loads(json_str)
                    return True
                except json.JSONDecodeError:
                    return False
            
            for chunk in response.iter_lines(decode_unicode=True):
                if not chunk:
                    continue
                    
                raw_chunk_count += 1
                
                # Handle CA API streaming format based on documentation
                if chunk == '[{':
                    # Start of JSON array, begin accumulating with just the object
                    accumulator = '{'
                elif chunk == '}]':
                    # End of JSON array, complete the object
                    accumulator += '}'
                elif chunk == ',':
                    # Skip commas between objects
                    continue
                else:
                    # Regular content, add to accumulator
                    accumulator += chunk
                
                # Check if we have a complete JSON object
                if is_json_valid(accumulator):
                    try:
                        # Parse the complete JSON object
                        data_json = json.loads(accumulator)
                        message_count += 1
                        
                        logger.info(f"📦 Parsed object preview: {str(data_json)[:500]}{'...' if len(str(data_json)) > 500 else ''}")
                        
                        # Transform system messages using dedicated streaming transformer
                        transformed_message = streaming_transformer.transform_system_message(data_json, message_count)
                        
                        # Only yield if transformation was successful
                        if transformed_message:
                            yield transformed_message
                            logger.info(f"✅ Yielded {transformed_message.get('message_type', 'unknown')} message to frontend")
                        else:
                            logger.info("⏭️ Skipped non-essential message")
                        
                        # Reset accumulator for next object
                        accumulator = ""
                        
                        # Add small delay to prevent overwhelming the frontend
                        await asyncio.sleep(0.1)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"🔶 Unexpected JSON decode error: {e}")
                        logger.error(f"🔶 Accumulator content: {accumulator[:200]}...")
                else:
                    logger.info(f"🔹 Accumulator not yet valid JSON (length: {len(accumulator)}): {accumulator[:100]}{'...' if len(accumulator) > 100 else ''}")
            
            # Handle any remaining data in accumulator
            if accumulator.strip():
                logger.info(f"🔸 Processing remaining accumulator (length: {len(accumulator)}): {accumulator[:200]}{'...' if len(accumulator) > 200 else ''}")
                if is_json_valid(accumulator):
                    try:
                        data_json = json.loads(accumulator)
                        message_count += 1
                                                
                        # Transform final message using dedicated streaming transformer
                        transformed_message = streaming_transformer.transform_system_message(data_json, message_count)
                        
                        if transformed_message:
                            yield transformed_message
                            logger.info(f"✅ Yielded final {transformed_message.get('message_type', 'unknown')} message to frontend")
                        else:
                            logger.info("⏭️ Skipped final non-essential message")
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Could not parse remaining accumulator: {accumulator[:100]}... Error: {e}")
                else:
                    logger.warning(f"🔶 Remaining accumulator is not valid JSON: {accumulator[:100]}...")
            else:
                logger.info("🔸 No remaining data in accumulator")

            logger.info(f"🏁 Streaming complete. Total raw chunks: {raw_chunk_count}, Total parsed messages: {message_count}")
            
            # Send completion signal
            yield {
                "type": "complete",
                "message": f"Streaming completed successfully. Processed {message_count} system messages from {raw_chunk_count} raw chunks.",
                "total_messages": message_count,
                "total_raw_chunks": raw_chunk_count,
                "timestamp": datetime.now().isoformat()
            }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Streaming request failed: {e}")
            yield {
                "error": True,
                "message": f"Request failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"General streaming error: {e}")
            yield {
                "error": True,
                "message": f"Streaming failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }


                
