/**
 * Simplified CVS Pharmacy Knowledge Assist Frontend
 * Core application initialization and event handling only
 * All specialized functionality moved to modular components
 */

// DOM Elements
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const validationMessage = document.getElementById('validationMessage');
const quickActionBtns = document.querySelectorAll('.quick-action-btn');

// Global variables
let conversationManager;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeDataAgentConfig();
    setupEventListeners();
    initializeConversationManager();
});

/**
 * Initialize conversation management
 */
function initializeConversationManager() {
    if (window.ConversationManager) {
        conversationManager = new window.ConversationManager();
        
        // Also assign to window for global access (needed for delete confirmation)
        window.conversationManager = conversationManager;
        
        console.log('Conversation manager initialized and assigned to window object');
        
        // Initialize conversations after authentication is confirmed
        if (window.loginManager && window.loginManager.isSessionValid && window.loginManager.isSessionValid()) {
            console.log('✅ User already authenticated, initializing conversations...');
            conversationManager.initializeAfterAuth();
        } else {
            console.log('⏳ Waiting for user authentication...');
            // Wait for login success or auth status check
            setTimeout(() => {
                if (conversationManager && window.loginManager) {
                    conversationManager.initializeAfterAuth();
                }
            }, 1000);
        }
    } else {
        console.error('ConversationManager not available');
    }
}

/**
 * Initialize data agent configuration
 */
function initializeDataAgentConfig() {
    console.log('🔧 Initializing Data Agent Configuration');
    
    // Populate SuperClient dropdown
    populateSuperClientDropdown();
    
    // Set up event listeners for configuration changes
    setupConfigEventListeners();
    
    // Restore saved SuperClient selection
    restoreSuperClientSelection();
}

/**
 * Populate SuperClient dropdown with available options
 */
function populateSuperClientDropdown() {
    const superClientSelect = document.getElementById('superClientSelect');
    if (!superClientSelect) return;
    
    // For now, use the known SuperClient - this could be fetched from backend later
    const superClients = [
        'EMPLOYERS HEALTH PURCHASING CORPORATION OF OHIO (EHPCO)',
        'STATE OF INDIANA'
    ];
    
    // Clear existing options
    superClientSelect.innerHTML = '';
    
    // Add options
    superClients.forEach(superClient => {
        const option = document.createElement('option');
        option.value = superClient;
        option.textContent = superClient;
        if (superClient !== 'EMPLOYERS HEALTH PURCHASING CORPORATION OF OHIO (EHPCO)') {
            option.disabled = true;
        }
        superClientSelect.appendChild(option);
    });
    
    // Set default value
    if (superClients.length > 0) {
        superClientSelect.value = superClients[0];
    }
}

/**
 * Setup event listeners for configuration changes
 */
function setupConfigEventListeners() {
    const superClientSelect = document.getElementById('superClientSelect');
    if (superClientSelect) {
        superClientSelect.addEventListener('change', function() {
            const selectedSuperClient = this.value;
            console.log('SuperClient changed to:', selectedSuperClient);
            
            // Store selection in localStorage for persistence
            localStorage.setItem('selectedSuperClient', selectedSuperClient);
            
        });
    }
}

/**
 * Get currently selected SuperClient
 */
function getSelectedSuperClient() {
    const superClientSelect = document.getElementById('superClientSelect');
    if (superClientSelect) {
        return superClientSelect.value;
    }
    
    // Fallback to localStorage or default
    return localStorage.getItem('selectedSuperClient') || 'EMPLOYERS HEALTH PURCHASING CORPORATION OF OHIO (EHPCO)';
}

/**
 * Restore SuperClient selection from localStorage
 */
function restoreSuperClientSelection() {
    const savedSuperClient = localStorage.getItem('selectedSuperClient');
    if (savedSuperClient) {
        const superClientSelect = document.getElementById('superClientSelect');
        if (superClientSelect) {
            superClientSelect.value = savedSuperClient;
        }
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Chat form submission
    chatForm.addEventListener('submit', handleChatSubmission);
    
    // Quick action buttons
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const query = this.getAttribute('data-query');
            if (query) {
                chatInput.value = query;
                handleChatSubmission(new Event('submit'));
            }
        });
    });

    
    // Input validation and send button state management
    chatInput.addEventListener('input', function() {
        validateInput();
        toggleSendButtonState();
    });
    
    // Initialize send button state
    toggleSendButtonState();
    
}

/**
 * Handle chat form submission
 */
async function handleChatSubmission(event) {
    event.preventDefault();
    
    const message = chatInput.value.trim();
    if (!message) return;
    
    // Validate input
    if (!validateInput()) return;
    
    // Start timing the execution
    const executionStartTime = performance.now();
    
    // Display user message
    displayMessage(message, 'user');
    
    // Collapse data agent sidebar when user sends a message
    if (conversationManager) {
        conversationManager.collapseDataAgentSidebar();
    }
    
    // Clear input
    chatInput.value = '';
    
    
    try {
        let result;
        
        if (window.streamingHandler) {
            console.log('Processing with backend...');
            
            // Get selected SuperClient
            const selectedSuperClient = getSelectedSuperClient();
            console.log('Using SuperClient:', selectedSuperClient);
            
            // Get current conversation ID (null for new conversations)
            const conversationId = conversationManager ? conversationManager.getCurrentConversationId() : null;
            console.log('Message:', `"${message.substring(0, 50)}..."`);
            console.log('ConversationId:', conversationId || 'NULL (new conversation)');
            
            result = await window.streamingHandler.handleStreamingChatWithUI(message, selectedSuperClient, conversationId);
        } else {
            result = {
                success: false,
                message: 'Analytics service not available. Please refresh the page and try again.',
                error: 'Service not initialized'
            };
        }
        
        // Calculate total execution time
        const executionEndTime = performance.now();
        const totalExecutionTime = executionEndTime - executionStartTime;
        
        // Add execution time to result
        if (result) {
            result.execution_time = Math.round(totalExecutionTime);
        }
        
        
        // Handle post-chat actions
        if (conversationManager && result && result.success) {
            let currentConversationId = conversationManager.getCurrentConversationId();
            
            console.log('🔄 Post-chat conversation handling:');
            console.log('  - Current conversation ID:', currentConversationId || 'NULL');
            console.log('  - Result conversation ID:', result.conversation_id || 'NULL');
            console.log('  - This is a new conversation:', !currentConversationId && result.conversation_id);
            
            // If we didn't have a conversation but got one back, this was a new conversation
            if (!currentConversationId && result.conversation_id) {
                console.log('✅ New conversation created:', result.conversation_id);
                conversationManager.setCurrentConversationId(result.conversation_id);

                // Refresh conversations list to show the new/updated conversation - backend api creates the conversation
                setTimeout(() => {
                    console.log('🔄 Refreshing conversations list after new conversation creation');
                    conversationManager.loadConversations();
                }, 300); // Small delay to ensure backend has processed
            } else if (currentConversationId && result.conversation_id && currentConversationId !== result.conversation_id) {
                // This shouldn't normally happen, but handle it just in case
                console.warn('⚠️ Conversation ID mismatch! Updating to match backend response');
                console.warn('  - Expected:', currentConversationId);
                console.warn('  - Received:', result.conversation_id);
                conversationManager.setCurrentConversationId(result.conversation_id);
            }
        }
        
    } catch (error) {
        console.error('Error processing query:', error);
        displayMessage('Database connection failed. Please check your credentials and try again.', 'bot', 'error');
    }
}

/**
 * Display a message in the chat
 */
function displayMessage(content, sender, type = 'normal', responseId = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    if (type === 'error') {
        messageDiv.classList.add('error-message');
    } else if (type === 'warning') {
        messageDiv.classList.add('warning-message');
    }
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    
    if (sender === 'user') {
        avatar.innerHTML = '<i class="fas fa-user"></i>';
    } else {
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
    }
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = content;
    
    messageContent.appendChild(messageText);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottomOfChat();
}



/**
 * Validate input
 */
function validateInput() {
    const message = chatInput.value.trim();
    const isValid = message.length >= 3;
    
    if (!isValid && message.length > 0) {
        validationMessage.textContent = 'Please enter at least 3 characters';
        validationMessage.style.display = 'block';
        return false;
    } else {
        validationMessage.style.display = 'none';
        return true;
    }
}

/**
 * Toggle send button disabled state based on input content
 */
function toggleSendButtonState() {
    const message = chatInput.value.trim();
    const hasText = message.length > 0;
    
    if (hasText) {
        sendBtn.disabled = false;
        sendBtn.classList.remove('disabled');
    } else {
        sendBtn.disabled = true;
        sendBtn.classList.add('disabled');
    }
}

/**
 * Show validation message
 */
function showValidationMessage(message, type = 'error') {
    const validationMessage = document.getElementById('validationMessage');
    if (validationMessage) {
        validationMessage.textContent = message;
        validationMessage.className = `validation-message ${type}`;
        validationMessage.style.display = 'block';
        
        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                validationMessage.style.display = 'none';
            }, 5000);
        }
    }
}

/**
 * Scroll to bottom of chat
 */
function scrollToBottomOfChat() {
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// GLOBAL EXPORTS FOR BACKWARD COMPATIBILITY
// =============================================================================

// Make essential functions globally available
window.conversationManager = conversationManager;
window.displayMessage = displayMessage;
window.scrollToBottomOfChat = scrollToBottomOfChat;
window.showValidationMessage = showValidationMessage;

console.log('✅ Simplified CVS Pharmacy Knowledge Assist Frontend loaded');
