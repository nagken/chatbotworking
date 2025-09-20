/**
 * Backend Integration Service for PSS Knowledge Assist
 * Handles communication between frontend and FastAPI backend
 */

class BackendIntegrationService {
    constructor() {
        // Use centralized configuration from env-config.js (single source of truth)
        this.baseUrl = window.API_CONFIG?.baseUrl || this.getDynamicBaseUrl();
        this.apiEndpoints = window.API_CONFIG?.endpoints || {};
        this.sessionId = this.generateSessionId();
        this.isConnected = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        // Log the determined base URL for debugging
        console.log('🔗 Backend Integration Service initialized with base URL:', this.baseUrl);
        console.log('🔗 API Endpoints:', this.apiEndpoints);
    }
    
    /**
     * Get session token from LoginManager
     */
    getSessionToken() {
        if (window.loginManager && window.loginManager.getSessionToken) {
            return window.loginManager.getSessionToken();
        }
        return null;
    }
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        if (window.loginManager && window.loginManager.isSessionValid) {
            return window.loginManager.isSessionValid();
        }
        return false;
    }
    
    /**
     * Get headers for authenticated requests
     */
    getAuthenticatedHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        const sessionToken = this.getSessionToken();
        if (sessionToken) {
            headers['Authorization'] = `Bearer ${sessionToken}`;
        }
        
        return headers;
    }
    
    /**
     * Handle 401 responses by redirecting to login
     */
    handleUnauthorizedResponse() {
        console.warn('🔐 Authentication required - redirecting to login');
        
        // Clear any invalid session data
        if (window.loginManager && window.loginManager.clearSession) {
            window.loginManager.clearSession();
        }
        
        // Show login overlay if available
        const loginOverlay = document.getElementById('loginOverlay');
        if (loginOverlay) {
            loginOverlay.classList.remove('hidden');
        }
        
        return {
            success: false,
            message: 'Authentication required. Please log in to continue.',
            error: 'unauthorized',
            requiresAuth: true
        };
    }
    
    /**
     * Get dynamic base URL with fallback logic
     */
    getDynamicBaseUrl() {
        // Check for environment-specific backend port
        if (window.BACKEND_PORT) {
            const url = `${window.location.protocol}//${window.location.hostname}:${window.BACKEND_PORT}`;
            console.log('🔧 Using environment BACKEND_PORT:', window.BACKEND_PORT);
            return url;
        }
        
        // Use frontend port + offset (common pattern)
        if (window.location.port) {
            const frontendPort = parseInt(window.location.port);
            const backendPort = frontendPort + 1; // Common pattern: frontend:3000, backend:3001
            const url = `${window.location.protocol}//${window.location.hostname}:${backendPort}`;
            console.log('🔧 Using frontend port + 1 pattern:', `${frontendPort} → ${backendPort}`);
            return url;
        }
        
        // Default fallback - try to detect current port first
        const currentPort = window.location.port;
        if (currentPort) {
            const url = `${window.location.protocol}//${window.location.hostname}:${currentPort}`;
            console.log(`🔧 Using current page port ${currentPort}`);
            return url;
        }
        
        const url = `${window.location.protocol}//${window.location.hostname}:8000`;
        console.log('🔧 Using default port 8000');
        return url;
    }

    /**
     * Generate a unique session ID for this chat session
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }



    /**
     * Process natural language query through backend
     */
    async processNaturalLanguageQuery(message, superclient, conversationId = null) {
        console.log('Processing query with backend:', message, 'SuperClient:', superclient, 'Conversation:', conversationId);
        
        // Check authentication before making request
        if (!this.isAuthenticated()) {
            console.warn('🔐 User not authenticated, redirecting to login');
            return this.handleUnauthorizedResponse();
        }
        
        // Prepare request payload
        const payload = {
            message: message,
            superclient: superclient
        };
        
        // Include conversation_id if provided
        if (conversationId) {
            payload.conversation_id = conversationId;
        }
        
        try {
            const response = await fetch(`${this.baseUrl}${this.apiEndpoints.chat}`, {
                method: 'POST',
                headers: this.getAuthenticatedHeaders(),
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Backend response received:', result);
                this.isConnected = true;
                
                // Validate the response structure
                const validation = this.validateBackendResponse(result);
                if (!validation.isValid) {
                    console.error('Backend response validation failed:', validation.error);
                    return {
                        success: false,
                        message: `Backend response validation failed: ${validation.error}`,
                        error: validation.error
                    };
                }
                
                return this.formatBackendResponse(result);
            } else if (response.status === 401) {
                // Handle unauthorized response
                console.warn('🔐 Received 401 Unauthorized from backend');
                return this.handleUnauthorizedResponse();
            } else {
                console.error('Backend error:', response.status, response.statusText);
                const errorText = await response.text();
                console.error('Error details:', errorText);
                throw new Error(`Backend error: ${response.status} - ${errorText}`);
            }
        } catch (error) {
            console.error('Backend query failed:', error);
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
            
            // Return error instead of fallback - NO DEFAULT DATA
            return {
                success: false,
                message: 'Backend connection failed. Please ensure the backend server is running and try again.',
                sql_query: null,
                chart_spec: null,
                data: null,
                execution_time: 0,
                row_count: 0,
                error: error.message
            };
        }
    }
    
    /**
     * Make authenticated API request
     */
    async makeAuthenticatedRequest(endpoint, options = {}) {
        // Check authentication
        if (!this.isAuthenticated()) {
            console.warn('🔐 User not authenticated for request to:', endpoint);
            return this.handleUnauthorizedResponse();
        }
        
        const url = `${this.baseUrl}${endpoint}`;
        const requestOptions = {
            method: 'GET',
            headers: this.getAuthenticatedHeaders(),
            ...options
        };
        
        try {
            const response = await fetch(url, requestOptions);
            
            if (response.ok) {
                const result = await response.json();
                console.log(`✅ ${requestOptions.method} ${endpoint} successful:`, result);
                return { success: true, data: result };
            } else if (response.status === 401) {
                console.warn('🔐 Received 401 Unauthorized from:', endpoint);
                return this.handleUnauthorizedResponse();
            } else {
                const errorText = await response.text();
                console.error(`❌ ${requestOptions.method} ${endpoint} failed:`, response.status, errorText);
                return {
                    success: false,
                    message: `Request failed: ${response.status} ${response.statusText}`,
                    error: errorText
                };
            }
        } catch (error) {
            console.error(`❌ ${requestOptions.method} ${endpoint} error:`, error);
            return {
                success: false,
                message: `Network error: ${error.message}`,
                error: error.message
            };
        }
    }
    
    /**
     * Submit feedback for a chat response
     */
    async submitFeedback(responseId, isPositive, comment = null) {
        console.log('Submitting feedback:', { responseId, isPositive, comment });
        
        return await this.makeAuthenticatedRequest('/api/feedback/submit', {
            method: 'POST',
            body: JSON.stringify({
                response_id: responseId,
                is_positive: isPositive,
                feedback_comment: comment
            })
        });
    }
    
    /**
     * Get existing feedback for a response
     */
    async getFeedback(responseId) {
        console.log('Getting feedback for response:', responseId);
        
        return await this.makeAuthenticatedRequest(`/api/feedback/${responseId}`);
    }
    
    /**
     * Update existing feedback
     */
    async updateFeedback(responseId, isPositive, comment = null) {
        console.log('Updating feedback:', { responseId, isPositive, comment });
        
        return await this.makeAuthenticatedRequest(`/api/feedback/${responseId}`, {
            method: 'PUT',
            body: JSON.stringify({
                response_id: responseId,
                is_positive: isPositive,
                feedback_comment: comment
            })
        });
    }



    /**
     * Format backend response to match frontend expectations
     */
    formatBackendResponse(backendResult) {
        if (!backendResult.success) {
            return {
                success: false,
                message: backendResult.message || 'Query failed',
                error: backendResult.detail || 'Unknown error'
            };
        }

        // Extract data from the backend structure (old working format)
        const extractedData = backendResult.data;
        
        // Map backend fields to frontend-expected format
        const formattedResponse = {
            success: true,
            message: backendResult.message || 'Query processed successfully',
            timestamp: new Date().toISOString(),
            conversation_id: backendResult.conversation_id
        };

        // Map SQL query field (backend: generated_sql -> frontend: sql_query)
        if (extractedData?.generated_sql) {
            formattedResponse.sql_query = extractedData.generated_sql;
        }

        // Map insight field (backend: insight -> frontend: insight)
        if (extractedData?.insight) {
            formattedResponse.insight = extractedData.insight;
        }

        // Map chart configuration (backend: chart_config -> frontend: chart_spec)
        if (extractedData?.chart_config) {
            formattedResponse.chart_spec = extractedData.chart_config;
        }

        // Map response_id for feedback tracking (backend: response_id -> frontend: data.response_id)
        if (extractedData?.response_id) {
            if (!formattedResponse.data) {
                formattedResponse.data = {};
            }
            formattedResponse.data.response_id = extractedData.response_id;
        }

        // Map execution result data (backend: execution_result.data -> frontend: data)
        if (extractedData?.execution_result?.data) {
            formattedResponse.data = extractedData.execution_result.data;
            formattedResponse.row_count = extractedData.execution_result.data.length;
            
            // Preserve response_id if we overwrite the data object
            if (extractedData?.response_id) {
                if (!formattedResponse.data) {
                    formattedResponse.data = {};
                }
                formattedResponse.data.response_id = extractedData.response_id;
            }
        }

        // Map metadata if available
        if (extractedData?.metadata) {
            if (extractedData.metadata.execution_time) {
                formattedResponse.execution_time = extractedData.metadata.execution_time;
            }
        }

        // Add execution time if available (default to 0)
        // Note: This might be overridden by the frontend's measured execution time
        if (!formattedResponse.execution_time) {
            formattedResponse.execution_time = 0;
        }

        // DEBUG: Log field mapping results (can be removed in production)
        console.log('📊 Field mapping results:', {
            sql_query: !!formattedResponse.sql_query,
            insight: !!formattedResponse.insight,
            chart_spec: !!formattedResponse.chart_spec,
            response_id: !!formattedResponse.data?.response_id,
            data_array: !!formattedResponse.data,
            row_count: formattedResponse.row_count || 0,
            execution_time: formattedResponse.execution_time || 0
        });

        console.log('Formatted backend response:', formattedResponse);
        
        // Debug the transformation process
        this.debugDataTransformation(backendResult, formattedResponse);
        
        return formattedResponse;
    }

    /**
     * Validate backend response structure
     */
    validateBackendResponse(backendResult) {
        if (!backendResult) {
            return { isValid: false, error: 'No response received from backend' };
        }

        if (typeof backendResult !== 'object') {
            return { isValid: false, error: 'Invalid response format from backend' };
        }

        if (backendResult.success === undefined) {
            return { isValid: false, error: 'Missing success field in backend response' };
        }

        if (backendResult.success) {
            // Check if we have the new MessageDetail structure
            const messageDetail = backendResult.assistant_message || backendResult;
            
            // Check if we have any meaningful data in the new structure
            const hasData = messageDetail.sql_query || 
                           messageDetail.chart_config || 
                           messageDetail.result_data;
            
            if (!hasData) {
                console.warn('Backend response has no extractable data in MessageDetail structure');
            }
        }

        return { isValid: true, error: null };
    }

    /**
     * Debug function to log data transformation process
     */
    debugDataTransformation(backendResult, formattedResponse) {
        console.group('🔍 Backend Data Transformation Debug');
        console.log('Original backend response:', backendResult);
        
        // Check for new MessageDetail structure
        const messageDetail = backendResult.assistant_message || backendResult;
        console.log('MessageDetail data:', messageDetail);
        
        console.log('Formatted frontend response:', formattedResponse);
        
        if (messageDetail?.chart_config) {
            console.log('Chart config found:', messageDetail.chart_config);
            console.log('Vega spec:', messageDetail.chart_config.vega_spec);
            console.log('Chart metadata:', messageDetail.chart_config.chart_metadata);
        }
        
        if (messageDetail?.result_data) {
            console.log('Result data found:', messageDetail.result_data);
            console.log('Data rows:', messageDetail.result_data.length || 0);
        }
        
        if (messageDetail?.sql_query) {
            console.log('Generated SQL found:', messageDetail.sql_query);
        }
        
        if (messageDetail?.ai_insights) {
            console.log('🧠 AI Insight found:', messageDetail.ai_insights);
        }
        
        console.groupEnd();
    }

    /**
     * Update backend connection status in UI
     */
    updateConnectionStatus(status) {
        // Backend connection status element has been removed from UI
        // Connection status is now handled silently in background
        console.log(`Backend connection status: ${status}`);
    }

    /**
     * Initialize the integration service
     */
    async initialize() {
        console.log('Initializing Backend Integration Service...');
        
        // Assume backend is available and will be tested on first request
        this.isConnected = true;
        console.log('Backend integration ready - will test connectivity on first request');
        this.updateConnectionStatus('connected');

        return true;
    }
}

// Create global instance
window.backendIntegration = new BackendIntegrationService();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    await window.backendIntegration.initialize();
});
