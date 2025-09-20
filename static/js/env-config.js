/**
 * Environment Configuration for PSS Knowledge Assist
 * Simplified configuration - processing logic moved to Python backend
 */

// Basic application configuration
const APP_CONFIG = {
    name: 'PSS Knowledge Assist',
    version: '1.0.0',
    environment: 'development',
    debug: true
};

// Centralized API configuration - single source of truth
// All other services should reference this configuration
const API_CONFIG = {
    // Dynamic base URL that works in both development and production
    baseUrl: getBaseUrl(),
    endpoints: {
        chat: '/api/chat',
        login: '/api/auth/login',
        logout: '/api/auth/logout',
        validate: '/api/auth/validate',
        feedback: '/api/feedback'
    }
};

/**
 * Get the appropriate base URL for API calls
 * Production: Use same origin as frontend (FastAPI serves both)
 * Development: Use explicit port configuration
 */
function getBaseUrl() {
    // Production mode: Use same origin as the current page
    if (window.USE_SAME_ORIGIN) {
        return window.location.origin;
    }
    
    // Development mode: Use explicit port configuration
    return `${window.location.protocol}//${window.location.hostname}:${getBackendPort()}`;
}

/**
 * Get backend port dynamically
 * Priority: Environment config > Frontend port + offset > Auto-detect > Default fallback
 */
function getBackendPort() {
    // Option 1: Check for environment-specific backend port
    if (window.BACKEND_PORT) {
        return window.BACKEND_PORT;
    }
    
    // Option 2: Use frontend port + offset (common pattern)
    if (window.location.port) {
        const frontendPort = parseInt(window.location.port);
        const backendPort = frontendPort + 1; // Common pattern: frontend:3000, backend:3001
        return backendPort;
    }
    
    // Option 3: Auto-detect based on current page port
    const currentPort = window.location.port;
    if (currentPort) {
        return parseInt(currentPort);
    }
    
    // Option 4: Try common ports in order
    const commonPorts = [5000, 8000, 3000, 8080];
    return commonPorts[0]; // Default to 5000
}

// UI configuration
const UI_CONFIG = {
    maxMessageLength: 255,  // Updated to match database feedback_comment constraint
    minMessageLength: 3,
    typingIndicatorDelay: 1000,
    autoScroll: true
};

// Export configuration
window.APP_CONFIG = APP_CONFIG;
window.API_CONFIG = API_CONFIG;
window.UI_CONFIG = UI_CONFIG;

// Log configuration details
console.log('⚙️ Configuration loaded:', APP_CONFIG);
console.log('🔗 API Configuration:', {
    baseUrl: API_CONFIG.baseUrl,
    protocol: window.location.protocol,
    hostname: window.location.hostname,
    frontendPort: window.location.port || 'default (80/443)',
    backendPort: getBackendPort(),
    endpoints: API_CONFIG.endpoints
}); 