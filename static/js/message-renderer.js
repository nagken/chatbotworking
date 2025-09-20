/**
 * Message Renderer for PSS Knowledge Assist
 * Core rendering logic abstracted for reuse between streaming and historical messages
 * Single responsibility: Pure message rendering without streaming-specific logic
 */

class MessageRenderer {
    constructor() {
        // Default options for rendering
        this.defaultOptions = {
            streaming: false,        // Controls animations/progressive loading
            showThinking: false,     // Controls thinking indicators  
            scrollToBottom: true,    // Controls auto-scroll behavior
            addFeedback: true,       // Controls feedback UI elements
            addActions: true         // Controls action buttons (copy, export, etc.)
        };
    }

    /**
     * Enhanced base URL getter with API_CONFIG integration
     */
    getBaseUrl() {
        // Use centralized API configuration if available
        if (window.API_CONFIG?.baseUrl) {
            return window.API_CONFIG.baseUrl;
        }

        // Fallback to environment-specific backend port
        if (window.BACKEND_PORT) {
            return `${window.location.protocol}//${window.location.hostname}:${window.BACKEND_PORT}`;
        }
        
        // Use frontend port + offset (common pattern)
        if (window.location.port) {
            const frontendPort = parseInt(window.location.port);
            const backendPort = frontendPort + 1;
            return `${window.location.protocol}//${window.location.hostname}:${backendPort}`;
        }
        
        // Default fallback - try to detect current port first
        const currentPort = window.location.port;
        if (currentPort) {
            return `${window.location.protocol}//${window.location.hostname}:${currentPort}`;
        }
        return `${window.location.protocol}//${window.location.hostname}:8000`;
    }

    /**
     * Utility function to escape HTML
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return String(text);
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Create assistant message container for both streaming and historical messages
     */
    createAssistantMessage(messageId, options = {}) {
        const opts = { ...this.defaultOptions, ...options };
        console.log(`🏗️ Creating assistant message container: ${messageId} (streaming: ${opts.streaming})`);
        
        // Get chatMessages element
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) {
            console.error('❌ chatMessages element not found');
            return null;
        }
        
        // Create the assistant message structure
        const messageDiv = document.createElement('div');
        messageDiv.className = `message bot-message ${opts.streaming ? 'streaming-message' : 'historical-message'}`;
        messageDiv.id = messageId;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        // Add to chat messages
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom if requested
        if (opts.scrollToBottom) {
            if (typeof window.scrollToBottomOfChat === 'function') {
                window.scrollToBottomOfChat();
            } else if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }
        
        console.log('✅ Assistant message container created and added to DOM');
        return messageDiv;
    }

    /**
     * Render SQL query in unified container
     */
    renderSQL(sqlQuery, assistantMessageContainer) {
        console.log('📊 Creating SQL Query container');

        if (!assistantMessageContainer) {
            console.error('❌ No assistant message container provided for SQL Query container');
            return;
        }
        
        const messageContent = assistantMessageContainer.querySelector('.message-content');
        if (!messageContent) {
            console.error('❌ No message content found in assistant container for SQL Query container');
            return;
        }
        
        // Create SQL Results container
        const sqlQueryContainer = document.createElement('div');
        sqlQueryContainer.className = 'sql-results-container unified-streaming-container';
        sqlQueryContainer.innerHTML = `
            <div class="sql-query-info">
                <div class="query-header">
                    <i class="fas fa-database"></i>
                    <span class="query-title">SQL Query</span>
                </div>
                <div class="sql-query-text">
                    <code>${this.escapeHtml(sqlQuery).trim()}</code>
                </div>
            </div>
        `;
        
        // Add to message container
        messageContent.appendChild(sqlQueryContainer);
        
        console.log('✅ SQL Query container created:', assistantMessageContainer.id);
    }

    /**
     * Render data table, extending existing SQL container or creating standalone
     */
    renderData(data, assistantMessageContainer) {
        console.log('📋 Creating Data Table container');
        
        if (!assistantMessageContainer) {
            console.error('❌ No assistant message container provided for data table container');
            return;
        }
        
        const messageContent = assistantMessageContainer.querySelector('.message-content');
        if (!messageContent || !Array.isArray(data)) {
            console.error('❌ Invalid container or data for data table container');
            return;
        }
        
                
        const columns = data.length > 0 ? Object.keys(data[0]) : [];
        const displayRows = data.slice(0, 5);
        const hasMoreRows = data.length > 5;
        
        const dataContainer = document.createElement('div');
        dataContainer.className = 'sql-results-container';
        dataContainer.dataset.fullData = JSON.stringify(data); // Store the complete dataset for pagination
        dataContainer.innerHTML = `
            <div class="sql-query-info">
                <div class="query-header">
                    <i class="fas fa-table"></i>
                    <span class="query-title">Data Generated</span>
                </div>
            </div>
            
            <div class="data-table-container">
                <div class="table-scroll-wrapper">
                    <table class="sql-data-table">
                        <thead>
                            <tr>
                                ${columns.map(col => `<th class="table-header">${this.escapeHtml(col)}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${displayRows.map((row, index) => `
                                <tr class="table-row ${index % 2 === 0 ? 'even' : 'odd'}">
                                    ${columns.map(col => `<td class="table-cell">${this.escapeHtml(String(row[col] || ''))}</td>`).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                
                ${hasMoreRows ? `
                    <div class="table-pagination">
                        <button class="pagination-btn" onclick="expandSQLResults(this)">
                            <i class="fas fa-chevron-down"></i>
                            Show ${data.length - 5} more rows
                        </button>
                        <div class="pagination-info">
                            Showing 1-5 of ${data.length} rows
                        </div>
                    </div>
                ` : ''}
            </div>
            
            <div class="data-actions">
                <button class="action-btn export-btn" onclick="exportSQLData(this)">
                    <i class="fas fa-download"></i>
                    Export CSV
                </button>
                <button class="action-btn copy-btn" onclick="copySQLQuery(this)">
                    <i class="fas fa-copy"></i>
                    Copy Query
                </button>
            </div>
        `;
        
        messageContent.appendChild(dataContainer);
        
        // Initialize interactive table features for the newly added data table
        requestAnimationFrame(() => {
            setTimeout(() => {
                if (window.initializeInteractiveTables) {
                    console.log('🔧 Initializing interactive table features for streaming data...');
                    window.initializeInteractiveTables();
                }
            }, 100); // Small delay to ensure DOM is fully rendered
        });

        console.log('✅ Data table added to unified SQL container:', assistantMessageContainer.id);
    }

    /**
     * Render chart visualization
     */
    renderChart(chartConfig, assistantMessageContainer) {
        console.log('📈 Displaying chart in dedicated container...');
        console.log('📈 Chart config received:', chartConfig);
        
        if (!assistantMessageContainer) {
            console.error('❌ No assistant message container provided for chart display');
            return;
        }
        
        const messageContent = assistantMessageContainer.querySelector('.message-content');
        if (!messageContent || !chartConfig || !chartConfig.vega_spec) {
            console.error('❌ Invalid container or chart config for chart display');
            console.error('❌ Chart config:', chartConfig);
            return;
        }
        
        // Extract chart data from vega_spec
        const chartData = chartConfig.vega_spec.data?.values || [];
        const chartTitle = chartConfig.chart_metadata?.title || 'Data Visualization';
        const chartType = chartConfig.chart_metadata?.chart_type || 'unknown';
        
        console.log('📈 Chart details:', { chartTitle, chartType, dataLength: chartData.length });
        
        // Use modular chart renderer
        setTimeout(async () => {
            try {
                // Check if chart renderer is available
                if (window.chartRenderer) {
                    await window.chartRenderer.displayChart(chartConfig, chartData);
                } else {
                    console.error('❌ Chart renderer not available');
                    this.displayChartError(assistantMessageContainer, 'Chart rendering system not available');
                }
            } catch (error) {
                console.error('❌ Error displaying chart:', error);
                this.displayChartError(assistantMessageContainer, error.message);
            }
        }, 100);
        
        console.log('✅ Chart rendering initiated for container:', assistantMessageContainer.id);
    }

    /**
     * Display chart error in message container
     */
    displayChartError(assistantMessageContainer, errorMessage) {
        const messageContent = assistantMessageContainer.querySelector('.message-content');
        if (!messageContent) return;

        const errorDiv = document.createElement('div');
        errorDiv.className = 'chart-error-container';
        errorDiv.innerHTML = `
            <div class="chart-error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to render chart: ${this.escapeHtml(errorMessage)}</p>
                <small>Please check the browser console for more details</small>
            </div>
        `;
        
        messageContent.appendChild(errorDiv);
    }

    /**
     * Render AI insights
     */
    renderInsights(insights, assistantMessageContainer) {        
        console.log('🧠 Displaying insights in dedicated container...');
        console.log('🔍 Insights content (first 200 chars):', insights ? insights.substring(0, 200) + '...' : 'NULL/UNDEFINED');
        console.log('🔍 Assistant container:', assistantMessageContainer ? assistantMessageContainer.id || 'no-id' : 'NULL');
        
        if (!assistantMessageContainer) {
            console.error('❌ No assistant message container provided for insights display');
            return;
        }
        
        const messageContent = assistantMessageContainer.querySelector('.message-content');
        console.log('🔍 Message content found:', !!messageContent);
        if (!messageContent) {
            console.error('❌ No message content found in assistant container');
            console.log('🔍 Container HTML:', assistantMessageContainer.outerHTML.substring(0, 300) + '...');
            return;
        }
        
        // Create AI insights component
        const insightsElement = document.createElement('div');
        insightsElement.className = `ai-insights-container`;
        insightsElement.innerHTML = `
            <h4>🧠 AI Insights</h4>
            <div class="insights-content">${insights}</div>
        `;
        
        console.log('🔍 Created insights element HTML:', insightsElement.outerHTML.substring(0, 300) + '...');
        
        // Append to dedicated message container
        messageContent.appendChild(insightsElement);
        
        console.log('✅ Insights component added to container:', assistantMessageContainer.id);
        console.log('🔍 Message content now has children:', messageContent.children.length);
        return insightsElement;
    }

    /**
     * Finalize assistant message by cleaning up indicators and updating state
     */
    finalizeAssistantMessage(assistantMessageContainer, options = {}) {
        const opts = { ...this.defaultOptions, ...options };
        console.log('🧹 Finalizing assistant message...', {
            container: assistantMessageContainer,
            options: opts,
            addFeedback: opts.addFeedback,
            existingFeedback: !!assistantMessageContainer?.querySelector('.message-feedback')
        });
        
        if (!assistantMessageContainer) {
            console.error('❌ No assistant message container to finalize');
            return;
        }
        
        // Add feedback UI if requested and not already present
        if (opts.addFeedback && !assistantMessageContainer.querySelector('.message-feedback')) {
            // Use the new unified feedback system
            if (window.messageFeedbackHandler) {
                // Use the database message ID if stored, otherwise fall back to DOM element ID
                const messageId = assistantMessageContainer.dataset.messageId || assistantMessageContainer.id;
                console.log('🔧 Adding feedback to message:', {
                    messageId: messageId,
                    domId: assistantMessageContainer.id,
                    datasetMessageId: assistantMessageContainer.dataset.messageId
                });
                
                window.messageFeedbackHandler.addFeedbackToMessage(
                    assistantMessageContainer, 
                    messageId
                );
            } else {
                console.error('❌ messageFeedbackHandler not available - feedback buttons will not be added');
            }
        } else if (opts.addFeedback) {
            console.log('⚠️ Feedback requested but already exists, skipping');
        } else {
            console.log('ℹ️ Feedback not requested in options');
        }
        
        console.log('✅ Assistant message finalized:', assistantMessageContainer.id);
    }


    /**
     * Render complete assistant message from chunks (for historical messages)
     */
    renderAssistantMessageFromChunks(message, options = {}) {
        const opts = { ...this.defaultOptions, streaming: false, ...options };
        console.log('🎯 Rendering complete assistant message from chunks:', message.id);
        
        if (!message.chunks || !Array.isArray(message.chunks)) {
            console.error('❌ No chunks available for message:', message.id);
            return null;
        }
        
        // Create assistant message container
        const container = this.createAssistantMessage(`historical-${message.id}`, opts);
        if (!container) {
            console.error('❌ Failed to create assistant message container');
            return null;
        }
        
        // Sort chunks by sequence to maintain order
        const sortedChunks = [...message.chunks].sort((a, b) => (a.sequence || 0) - (b.sequence || 0));
        
        // Render each chunk using appropriate method
        sortedChunks.forEach((chunk, index) => {
            console.log(`🧩 Rendering chunk ${index + 1}/${sortedChunks.length}:`, chunk.message_type);
            
            try {
                switch (chunk.message_type) {
                    case 'sql':
                        if (chunk.data.sql_query) {
                            this.renderSQL(chunk.data.sql_query, container);
                        }
                        break;
                        
                    case 'data':
                        if (chunk.data.result_data) {
                            this.renderData(chunk.data.result_data, container);
                        }
                        break;
                        
                    case 'chart':
                        if (chunk.data.chart_config) {
                            this.renderChart(chunk.data.chart_config, container);
                        }
                        break;
                        
                    case 'insights':
                        if (chunk.data.ai_insights) {
                            console.log('Skipping AI insights...');
                            //this.renderInsights(chunk.data.ai_insights, container);
                        }
                        break;
                        
                    default:
                        console.warn('⚠️ Unknown chunk type:', chunk.message_type);
                }
            } catch (error) {
                console.error(`❌ Error rendering chunk ${chunk.message_type}:`, error);
            }
        });
        
        // Finalize the message
        this.finalizeAssistantMessage(container, opts);
        
        console.log('✅ Complete assistant message rendered from chunks');
        return container;
    }

    /**
     * Render text response in unified container (for CVS Pharmacy Knowledge Assist)
     */
    renderTextResponse(content, assistantMessageContainer, isFinal = false) {
        console.log('💬 Rendering text response', { contentLength: content.length, isFinal });
        
        // DEBUG: Check if content contains document results
        const hasDocuments = content.includes('Related Documents');
        console.log('🔍 Content contains "Related Documents":', hasDocuments);
        if (hasDocuments) {
            console.log('📚 Document results found in content:', content.substring(content.indexOf('Related Documents'), content.indexOf('Related Documents') + 200));
            console.log('📝 Full content being processed:', content);
        }

        if (!assistantMessageContainer) {
            console.error('❌ No assistant message container provided for text response');
            return;
        }
        
        const messageContent = assistantMessageContainer.querySelector('.message-content');
        if (!messageContent) {
            console.error('❌ No message content found in assistant container for text response');
            return;
        }
        
        // Find existing text container or create new one
        let textContainer = messageContent.querySelector('.text-response-container');
        
        if (!textContainer) {
            // Create text response container
            textContainer = document.createElement('div');
            textContainer.className = 'text-response-container unified-streaming-container';
            textContainer.innerHTML = `
                <div class="text-response-content">
                    <div class="response-text"></div>
                </div>
            `;
            messageContent.appendChild(textContainer);
            console.log('✅ Created new text response container');
        }
        
        // Update the text content
        const responseTextElement = textContainer.querySelector('.response-text');
        if (responseTextElement) {
            // Convert markdown-style content to HTML
            const htmlContent = this.convertMarkdownToHtml(content);
            responseTextElement.innerHTML = htmlContent;
            
            // DEBUG: Log final HTML content
            if (hasDocuments) {
                console.log('📝 Final HTML content:', htmlContent.substring(0, 500));
                console.log('🎯 Text container element:', textContainer);
                console.log('🎯 Response text element:', responseTextElement);
                console.log('🎯 HTML in DOM:', responseTextElement.innerHTML.substring(0, 500));
            }
        }
        
        // Scroll to bottom for real-time updates
        if (window.UI_CONFIG?.autoScroll !== false) {
            if (typeof window.scrollToBottomOfChat === 'function') {
                window.scrollToBottomOfChat();
            }
        }
        
        console.log('✅ Text response rendered successfully');
    }

    /**
     * Convert basic markdown to HTML for text responses
     */
    convertMarkdownToHtml(text) {
        if (!text) return '';
        
        // DEBUG: Log the original text to see exact format
        console.log('🔍 Converting markdown text:', text.substring(0, 300));
        
        // FIRST: Handle document-specific patterns BEFORE converting line breaks
        // Enhanced: Handle "Related Documents Found:" section with special styling
        text = text.replace(/📚 \*\*Related Documents Found:\*\*/g, '<div class="related-documents-section"><h4>📚 Related Documents Found:</h4>');
        
        // Enhanced: Better numbered list handling for documents (more flexible pattern)
        text = text.replace(/^\*\*(\d+)\.\s*([^*]+)\*\*\s*\(Relevance:\s*([\d.]+)\)/gm, '<div class="document-item"><h5><strong>$1. $2</strong> <span class="relevance-score">(Relevance: $3)</span></h5>');
        
        // Enhanced: Handle preview text (more flexible)
        text = text.replace(/^\*Preview:\*\s*"([^"]+)"/gm, '<p class="document-preview"><em>Preview:</em> "$1"</p>');
        
        // Enhanced: Handle file paths (more flexible)
        text = text.replace(/^📁\s*\*Path:\*\s*(.+)$/gm, '<p class="document-path">📁 <em>Path:</em> $1</p></div>');
        
        // THEN: Convert general markdown patterns
        // Convert **bold** to <strong> (but avoid already processed ones)
        text = text.replace(/\*\*([^<]*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert *italic* to <em> (but avoid already processed ones)
        text = text.replace(/\*([^<]*?)\*/g, '<em>$1</em>');
        
        // Convert numbered lists (fallback for other lists)
        text = text.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
        
        // Wrap consecutive <li> elements in <ol>
        text = text.replace(/(<li>.*<\/li>)/gs, '<ol>$1</ol>');
        
        // Convert bullet points  
        text = text.replace(/^[-•]\s+(.+)$/gm, '<li>$1</li>');
        
        // Convert URLs to links
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        // FINALLY: Convert line breaks to <br> (after all multiline patterns are processed)
        text = text.replace(/\n/g, '<br>');
        
        // Close the related documents section if it was opened
        if (text.includes('related-documents-section')) {
            text += '</div>';
        }
        
        // DEBUG: Log the final converted HTML
        if (text.includes('Related Documents')) {
            console.log('🔍 Final converted HTML:', text.substring(0, 500));
        }
        
        return text;
    }

    // ...existing code...
}

// =============================================================================
// GLOBAL INSTANCE AND BACKWARD COMPATIBILITY
// =============================================================================

// Create global instance for easy access
window.messageRenderer = new MessageRenderer();

// Initialize message renderer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Message Renderer initialized');
    console.log('✅ Core rendering system ready');
});
