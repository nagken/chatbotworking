/**
 * Consolidated Streaming System for PSS Knowledge Assist
 * Combines streaming protocol handling with UI integration
 */

class StreamingHandler {
    constructor() {
        // Core streaming state (from streaming-handler.js)
        this.eventSource = null;
        this.isStreaming = false;
        this.onMessageCallback = null;
        this.onCompleteCallback = null;
        this.onErrorCallback = null;
        this.currentStreamData = {
            chunks: [],
            totalChunks: 0,
            startTime: null,
            responseId: null,
            conversationId: null
        };

        // UI integration state (from streaming-integration.js)
        this.progressiveThinkingState = {
            currentIndicator: null,
            rotationTimer: null,
            messageIndex: 0,
            messages: ["Analyzing", "Thinking", "Generating"],
            rotationInterval: 3500
        };

        // Message renderer instance for consistent UI
        this.messageRenderer = window.messageRenderer || new MessageRenderer();
    }

    /**
     * Consolidated utility function to escape HTML (delegate to messageRenderer)
     */
    escapeHtml(text) {
        return this.messageRenderer.escapeHtml(text);
    }

    /**
     * Enhanced base URL getter (delegate to messageRenderer)
     */
    getBaseUrl() {
        return this.messageRenderer.getBaseUrl();
    }

    // =============================================================================
    // CORE STREAMING METHODS
    // =============================================================================

    /**
     * Start streaming chat response
     */
    async startStreamingChat(message, superclient, conversationId = null) {
        console.log('🌊 Starting streaming chat request...');
        
        if (this.isStreaming) {
            console.warn('⚠️ Streaming already in progress, stopping current stream');
            this.stopStreaming();
        }

        // Reset stream data
        this.currentStreamData = {
            chunks: [],
            totalChunks: 0,
            startTime: performance.now(),
            responseId: null,
            conversationId: conversationId
        };

        // Get session token for authentication
        const sessionToken = window.loginManager?.getSessionToken();
        if (!sessionToken) {
            console.error('❌ No session token available for streaming');
            this.handleError('Authentication required for streaming');
            return false;
        }

        try {
            // Prepare streaming request payload
            const payload = {
                message: message,
                superclient: superclient
            };

            if (conversationId) {
                payload.conversation_id = conversationId;
            }

            // Start Server-Sent Events connection
            let streamUrl = `${this.getBaseUrl()}/api/chat/stream`;
            
            // Check if we should use local search mode
            if (window.conversationManager && window.conversationManager.useLocalSearch) {
                streamUrl = `${this.getBaseUrl()}/api/chat/local/stream`;
            }
            
            // Note: EventSource doesn't support POST, so we need to use fetch with streaming
            const response = await fetch(streamUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionToken}`,
                    'Accept': 'text/event-stream'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`Streaming request failed: ${response.status} ${response.statusText}`);
            }

            // Process streaming response
            await this.processStreamingResponse(response);
            return true;

        } catch (error) {
            console.error('❌ Failed to start streaming:', error);
            this.handleError(`Failed to start streaming: ${error.message}`);
            return false;
        }
    }

    /**
     * Process streaming response from server
     */
    async processStreamingResponse(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        this.isStreaming = true;
        console.log('✅ Streaming connection established');

        try {
            while (this.isStreaming) {
                const { done, value } = await reader.read();
                
                if (done) {
                    console.log('🏁 Streaming completed by server');
                    break;
                }

                // Decode chunk and add to buffer
                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;

                // Process complete SSE messages from buffer
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6)); // Remove 'data: ' prefix
                            await this.handleStreamingMessage(data);
                        } catch (error) {
                            console.error('❌ Failed to parse streaming message:', line, error);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('❌ Error during streaming:', error);
            this.handleError(`Streaming error: ${error.message}`);
        } finally {
            this.isStreaming = false;
            reader.releaseLock();
        }
    }

    /**
     * Handle individual streaming message
     */
    async handleStreamingMessage(data) {
        console.log('📦 Received streaming message:', data);

        switch (data.type) {
            case 'status':
                this.handleStatusMessage(data);
                break;

            case 'chunk':
                this.handleChunkMessage(data);
                break;

            case 'complete':
                this.handleCompleteMessage(data);
                break;

            case 'error':
            case 'storage_error':
                this.handleErrorMessage(data);
                break;

            default:
                console.log('📝 Unknown message type:', data.type, data);
        }
    }

    /**
     * Handle status messages (initial connection, progress updates)
     */
    handleStatusMessage(data) {
        console.log('📊 Status:', data.message);
        
        // Update UI with status
        if (this.onMessageCallback) {
            this.onMessageCallback({
                type: 'status',
                content: data.message,
                timestamp: data.timestamp
            });
        }
    }

    /**
     * Handle chunk messages (system message objects from CA API)
     */
    handleChunkMessage(data) {
        console.log('🧩 Processing chunk:', data.data);

        // Store chunk data
        this.currentStreamData.chunks.push(data.data);
        this.currentStreamData.totalChunks++;
        
        // Store response/conversation IDs if available
        if (data.response_id) {
            this.currentStreamData.responseId = data.response_id;
        }
        if (data.conversation_id) {
            this.currentStreamData.conversationId = data.conversation_id;
        }

        // Process the chunk data based on its type
        const chunkData = data.data;
        
        if (chunkData.type === 'text_chunk') {
            // Handle text content from CVS Pharmacy responses
            if (this.onMessageCallback) {
                this.onMessageCallback({
                    type: 'text_chunk',
                    content: chunkData.content,
                    sequence: chunkData.sequence,
                    is_complete: chunkData.is_complete,
                    conversation_id: data.conversation_id,
                    message_id: data.message_id
                });
            }
        } else if (chunkData.type === 'system_message') {
            // This is a transformed system message from our server
            this.processTransformedSystemMessage(chunkData);
        } else if (chunkData.error) {
            // Handle error chunks
            this.handleError(`Chunk error: ${chunkData.message}`);
        }
    }

    /**
     * Process transformed system message from server
     */
    processTransformedSystemMessage(transformedMessage) {
        console.log(`🎯 Processing transformed message #${transformedMessage.sequence}:`, transformedMessage);

        // Server has already extracted and transformed the data - just pass it along
        if (this.onMessageCallback) {
            this.onMessageCallback({
                type: 'system_message',
                message_type: transformedMessage.message_type,
                sequence: transformedMessage.sequence,
                data: transformedMessage.data,
                rawMessage: transformedMessage.raw_message,
                timestamp: transformedMessage.timestamp
            });
        }
    }

    /**
     * Handle completion message
     */
    handleCompleteMessage(data) {        
        const totalTime = performance.now() - this.currentStreamData.startTime;
        
        const completionData = {
            type: 'complete',
            message: data.message,
            totalChunks: data.total_chunks || this.currentStreamData.totalChunks,
            responseId: data.response_id || this.currentStreamData.responseId,
            conversationId: data.conversation_id || this.currentStreamData.conversationId,
            messageId: data.message_id,
            streamingTime: Math.round(totalTime),
            timestamp: data.timestamp
        };

        if (this.onCompleteCallback) {
            this.onCompleteCallback(completionData);
        }

        this.stopStreaming();
    }

    /**
     * Handle error messages
     */
    handleErrorMessage(data) {
        console.error('❌ Streaming error:', data);
        
        if (this.onErrorCallback) {
            this.onErrorCallback({
                type: 'error',
                message: data.message,
                error: data.error || 'Unknown streaming error',
                timestamp: data.timestamp
            });
        }

        this.stopStreaming();
    }

    /**
     * Handle general errors
     */
    handleError(message) {
        console.error('❌ Streaming handler error:', message);
        
        if (this.onErrorCallback) {
            this.onErrorCallback({
                type: 'error',
                message: message,
                timestamp: new Date().toISOString()
            });
        }

        this.stopStreaming();
    }

    /**
     * Stop streaming
     */
    stopStreaming() {
        console.log('🛑 Stopping streaming...');
        
        this.isStreaming = false;
        
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        this.removeProgressiveThinkingIndicator();
    }

    /**
     * Set callback for streaming messages
     */
    onMessage(callback) {
        this.onMessageCallback = callback;
    }

    /**
     * Set callback for streaming completion
     */
    onComplete(callback) {
        this.onCompleteCallback = callback;
    }

    /**
     * Set callback for streaming errors
     */
    onError(callback) {
        this.onErrorCallback = callback;
    }


    // =============================================================================
    // UI INTEGRATION METHODS
    // =============================================================================

    /**
     * Handle streaming chat with full UI integration
     * Main entry point that combines protocol handling with UI updates
     */
    async handleStreamingChatWithUI(message, selectedSuperClient, conversationId = null) {
        console.log('🌊 Starting streaming chat integration...');
        
        // 🎯 STEP 1: Create dedicated assistant message container for this streaming response
        const streamingMessageId = `streaming-message-${Date.now()}`;
        const assistantMessageContainer = this.messageRenderer.createAssistantMessage(streamingMessageId, { 
            streaming: true, 
            scrollToBottom: true 
        });
        
        console.log('✅ Created dedicated assistant message container:', streamingMessageId);
        
        // 🎯 STEP 2: Create progressive thinking indicator
        this.createProgressiveThinkingIndicator(assistantMessageContainer);

        // Create a promise to track streaming completion
        return new Promise((resolve, reject) => {
            const streamingResult = {
                success: false,
                message: 'Streaming in progress...',
                streaming: true,
                chunks: [],
                sql_query: null,
                chart_spec: null,
                data: null,
                ai_insights: null,
                response_id: null,
                conversation_id: conversationId,
                execution_time: 0
            };

            const startTime = performance.now();
            
            // Set up streaming event handlers
            this.onMessage((messageData) => {
                console.log('📦 Streaming message received:', messageData);
                console.log('🔍 Message type:', messageData.type);
                console.log('🔍 Message data preview:', JSON.stringify(messageData, null, 2).substring(0, 300) + '...');
                
                switch (messageData.type) {
                    case 'status':
                        // Keep progressive thinking indicator running (status updates handled by rotation)
                        console.log('📊 Status received:', messageData.content);
                        break;
                        
                    case 'system_message':
                        // Process system message data with dedicated container
                        console.log('🎯 SYSTEM MESSAGE DETECTED - calling processStreamingSystemMessage');
                        this.processStreamingSystemMessage(messageData, streamingResult, assistantMessageContainer);
                        break;
                        
                    default:
                        console.log('⚠️ Unknown message type in onMessage handler:', messageData.type);
                }
            });

            this.onComplete((completionData) => {
                console.log('🎉 Streaming completed:', completionData);
                
                streamingResult.success = true;
                streamingResult.streaming = false;
                streamingResult.message = 'Analysis completed via streaming';
                streamingResult.execution_time = completionData.streamingTime || (performance.now() - startTime);
                streamingResult.response_id = completionData.responseId;
                
                if (completionData.conversationId) {
                    streamingResult.conversation_id = completionData.conversationId;
                }
                
                // Store database message_id on DOM element for feedback submission
                if (completionData.messageId && assistantMessageContainer) {
                    assistantMessageContainer.dataset.messageId = completionData.messageId;
                    console.log('✅ Stored database message_id for feedback:', completionData.messageId);
                }
                
                // 🧹 Clean up streaming indicators and finalize the message
                this.removeProgressiveThinkingIndicator();
                this.messageRenderer.finalizeAssistantMessage(assistantMessageContainer, { 
                    streaming: true, 
                    addFeedback: true 
                });
                
                console.log('✅ Final streaming result:', streamingResult);
                resolve(streamingResult);
            });

            this.onError((errorData) => {
                console.error('❌ Streaming error:', errorData);
                
                const errorResult = {
                    success: false,
                    message: errorData.message || 'Streaming failed',
                    error: errorData.error || 'streaming_error',
                    streaming: false,
                    execution_time: performance.now() - startTime
                };
                
                resolve(errorResult);
            });

            // Start the streaming process
            this.startStreamingChat(message, selectedSuperClient, conversationId)
                .then((started) => {
                    if (!started) {
                        resolve({
                            success: false,
                            message: 'Failed to start streaming',
                            error: 'streaming_start_failed',
                            execution_time: performance.now() - startTime
                        });
                    }
                })
                .catch((error) => {
                    console.error('❌ Error starting streaming:', error);
                    resolve({
                        success: false,
                        message: `Failed to start streaming: ${error.message}`,
                        error: 'streaming_start_error',
                        execution_time: performance.now() - startTime
                    });
                });
        });
    }

    /**
     * Process system message data from streaming (with UI integration)
     */
    processStreamingSystemMessage(messageData, streamingResult, assistantMessageContainer) {
        console.log('🎯 Processing transformed streaming system message:', messageData);
        console.log('🔍 Message data keys:', Object.keys(messageData));
        console.log('🔍 Message_type value:', messageData.message_type);
        
        const { message_type, data } = messageData;
        streamingResult.chunks.push(messageData);
        
        console.log('🔍 Extracted message_type:', message_type);
        console.log('🔍 Extracted data keys:', data ? Object.keys(data) : 'DATA IS NULL/UNDEFINED');
        
        // Process based on message type (server has already transformed the data)
        switch (message_type) {
            case 'text_response':
                // Handle text-based responses (CVS Pharmacy Knowledge Assist)
                if (data.content) {
                    console.log('💬 Text response received via streaming');
                    this.messageRenderer.renderTextResponse(data.content, assistantMessageContainer, data.is_final);
                    
                    if (data.is_final) {
                        // Remove thinking indicator after final response
                        setTimeout(() => {
                            this.removeProgressiveThinkingIndicator();
                        }, 500);
                    }
                }
                break;
                
            case 'sql':
                if (data.sql_query && !streamingResult.sql_query) {
                    streamingResult.sql_query = data.sql_query;
                    console.log('📊 SQL query received via streaming');
                    this.messageRenderer.renderSQL(data.sql_query, assistantMessageContainer);
                    
                    // Move thinking indicator to bottom after SQL Query container renders
                    setTimeout(() => {
                        this.moveThinkingIndicatorToBottom(assistantMessageContainer);
                    }, 100);
                }
                break;
                
            case 'data':
                if (data.result_data && !streamingResult.data) {
                    streamingResult.data = data.result_data;
                    streamingResult.result_schema = data.result_schema;
                    streamingResult.result_name = data.result_name;
                    console.log('📋 Data received via streaming:', streamingResult.data.length, 'rows');
                    this.messageRenderer.renderData(data.result_data, assistantMessageContainer);
                    
                    // Move thinking indicator to bottom after data renders
                    setTimeout(() => {
                        this.moveThinkingIndicatorToBottom(assistantMessageContainer);
                    }, 100);
                }
                break;
                
            case 'chart':
                if (data.chart_config && !streamingResult.chart_spec) {
                    streamingResult.chart_spec = data.chart_config;
                    console.log('📈 Chart config received via streaming');
                    this.messageRenderer.renderChart(data.chart_config, assistantMessageContainer);
                    
                    // Remove thinking indicator after final component
                    setTimeout(() => {
                        this.removeProgressiveThinkingIndicator();
                    }, 1000);
                }
                break;
                
            case 'insights':
                console.log('✅ Processing AI insights...', data);
                console.log('🔍 Insights data structure:', JSON.stringify(data, null, 2));
                console.log('🔍 AI insights content preview:', data.ai_insights ? data.ai_insights.substring(0, 100) + '...' : 'NOT FOUND');
                console.log('🔍 Document references:', data.document_references ? data.document_references.length : 'NONE');
                console.log('🔍 Container available:', !!assistantMessageContainer);
                console.log('🔍 StreamingResult state:', !!streamingResult.ai_insights);
                
                if (data.ai_insights && !streamingResult.ai_insights) {
                    streamingResult.ai_insights = data.ai_insights;
                    console.log('🧠 AI insights received via streaming - length:', data.ai_insights.length);
                    
                    // Call renderInsights with document references
                    const insightsElement = this.messageRenderer.renderInsights(
                        data.ai_insights, 
                        assistantMessageContainer,
                        data.document_references || null
                    );
                    console.log('🎯 Insights element created:', !!insightsElement);
                    console.log('📎 Document references passed:', data.document_references ? data.document_references.length : 0);
                    
                    // Move thinking indicator to bottom after insights render, then remove it
                    setTimeout(() => {
                        this.moveThinkingIndicatorToBottom(assistantMessageContainer);
                        // Remove thinking indicator after final component
                        setTimeout(() => {
                            this.removeProgressiveThinkingIndicator();
                        }, 1000);
                    }, 100);
                } else {
                    console.log('❌ AI insights not found in data or already processed');
                    console.log('   data.ai_insights exists:', !!data.ai_insights);
                    console.log('   streamingResult.ai_insights exists:', !!streamingResult.ai_insights);
                    console.log('   Available data keys:', Object.keys(data));
                }
                break;
                
            default:
                console.log('⚠️ Unknown message type:', message_type);
        }
        
        // Update progress indicator
        this.updateStreamingProgress(messageData.sequence, { [message_type]: true });
    }

    // =============================================================================
    // PROGRESSIVE THINKING INDICATOR METHODS
    // =============================================================================

    /**
     * Create progressive thinking indicator with rotating messages
     */
    createProgressiveThinkingIndicator(assistantMessageContainer) {
        console.log('🤔 Creating progressive thinking indicator...');
        
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'progressive-thinking-indicator';
        thinkingDiv.innerHTML = `
            <div class="thinking-content">
                <div class="thinking-text-container">
                    <span class="thinking-message">${this.progressiveThinkingState.messages[0]}</span>
                    <div class="thinking-loader"></div>
                </div>
            </div>
        `;
        
        // Add smooth transition styles
        thinkingDiv.style.cssText = `
            transition: transform 0.5s ease, opacity 0.3s ease;
            opacity: 1;
            transform: translateY(0);
        `;
        
        // Add to message container
        const messageContent = assistantMessageContainer.querySelector('.message-content');
        if (messageContent) {
            messageContent.appendChild(thinkingDiv);
            this.progressiveThinkingState.currentIndicator = thinkingDiv;
            
            // Start message rotation
            this.startMessageRotation();
            
            console.log('✅ Progressive thinking indicator created and rotation started');
        }
        
        return thinkingDiv;
    }

    /**
     * Start rotating thinking messages
     */
    startMessageRotation() {
        if (this.progressiveThinkingState.rotationTimer) {
            clearInterval(this.progressiveThinkingState.rotationTimer);
        }
        
        this.progressiveThinkingState.rotationTimer = setInterval(() => {
            if (this.progressiveThinkingState.currentIndicator) {
                this.progressiveThinkingState.messageIndex = (this.progressiveThinkingState.messageIndex + 1) % this.progressiveThinkingState.messages.length;
                const messageElement = this.progressiveThinkingState.currentIndicator.querySelector('.thinking-message');
                
                if (messageElement) {
                    // Smooth message transition with fade effect
                    messageElement.style.opacity = '0.6';
                    messageElement.style.transform = 'translateX(-5px)';
                    setTimeout(() => {
                        messageElement.textContent = this.progressiveThinkingState.messages[this.progressiveThinkingState.messageIndex];
                        messageElement.style.opacity = '1';
                        messageElement.style.transform = 'translateX(0)';
                    }, 200);
                }
            }
        }, this.progressiveThinkingState.rotationInterval);
        
        console.log('🔄 Message rotation started');
    }

    /**
     * Move thinking indicator to bottom of message container with smooth transition
     */
    moveThinkingIndicatorToBottom(assistantMessageContainer) {
        if (!this.progressiveThinkingState.currentIndicator || !assistantMessageContainer) return;
        
        console.log('📍 Moving thinking indicator to bottom...');
        
        const messageContent = assistantMessageContainer.querySelector('.message-content');
        if (!messageContent) return;
        
        // Smooth transition: fade out, move, fade in
        this.progressiveThinkingState.currentIndicator.style.opacity = '0.7';
        this.progressiveThinkingState.currentIndicator.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            // Move to bottom
            messageContent.appendChild(this.progressiveThinkingState.currentIndicator);
            
            // Fade back in at new position
            this.progressiveThinkingState.currentIndicator.style.opacity = '1';
            this.progressiveThinkingState.currentIndicator.style.transform = 'translateY(0)';
            
            console.log('✅ Thinking indicator moved to bottom with smooth transition');
        }, 200);
    }

    /**
     * Remove progressive thinking indicator with smooth transition
     */
    removeProgressiveThinkingIndicator() {
        console.log('🧹 Removing progressive thinking indicator...');
        
        // Clear rotation timer
        if (this.progressiveThinkingState.rotationTimer) {
            clearInterval(this.progressiveThinkingState.rotationTimer);
            this.progressiveThinkingState.rotationTimer = null;
        }
        
        // Smooth fade out and removal
        if (this.progressiveThinkingState.currentIndicator) {
            this.progressiveThinkingState.currentIndicator.style.opacity = '0';
            this.progressiveThinkingState.currentIndicator.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                if (this.progressiveThinkingState.currentIndicator && this.progressiveThinkingState.currentIndicator.parentNode) {
                    this.progressiveThinkingState.currentIndicator.parentNode.removeChild(this.progressiveThinkingState.currentIndicator);
                }
                this.progressiveThinkingState.currentIndicator = null;
                this.progressiveThinkingState.messageIndex = 0;
                
                console.log('✅ Progressive thinking indicator removed');
            }, 300);
        }
    }

    // =============================================================================
    // CONTENT DISPLAY METHODS - Now handled by MessageRenderer
    // =============================================================================
    
    // Note: All content display methods (displayStreamingSQL, displayStreamingData, etc.)
    // have been moved to MessageRenderer class for consistency between streaming and historical messages
    // The MessageRenderer handles both streaming (with animations) and static (historical) rendering

    /**
     * Update streaming progress indicator
     */
    updateStreamingProgress(sequence, messageTypes) {
        console.log(`⏳ Streaming progress: Message #${sequence}`);
        
        // Update progress indicator if available
        const progressIndicator = document.querySelector('.streaming-progress');
        if (progressIndicator) {
            const progressText = document.querySelector('.streaming-progress-text');
            if (progressText) {
                let statusText = `Processing message #${sequence}`;
                
                if (messageTypes.sql) statusText += ' • SQL ✓';
                if (messageTypes.data) statusText += ' • Data ✓';
                if (messageTypes.chart) statusText += ' • Chart ✓';
                if (messageTypes.insights) statusText += ' • Insights ✓';
                
                progressText.textContent = statusText;
            }
        }
    }
}

// =============================================================================
// GLOBAL INSTANCE AND BACKWARD COMPATIBILITY
// =============================================================================

// Create global instance for backward compatibility
window.streamingHandler = new StreamingHandler();

// Export main streaming function for backward compatibility
// This maintains the original API from streaming-integration.js
window.handleStreamingChat = function(message, selectedSuperClient, conversationId = null) {
    return window.streamingHandler.handleStreamingChatWithUI(message, selectedSuperClient, conversationId);
};

// Initialize streaming integration when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Consolidated streaming system initialized');
    console.log('✅ Streaming integration ready');
});
