/**
 * Conversation Manager for PSS Knowledge Assist
 * Handles conversation creation, switching, and management
 */

class ConversationManager {
    constructor() {
        this.conversations = [];
        this.currentConversationId = null;
        this.loadingConversations = false;
        this.isFirstLoad = true;
        this.conversationTitlesUpdated = new Set(); // Track which conversations have had titles updated
        
        // Message renderer instance for consistent UI between streaming and historical
        this.messageRenderer = window.messageRenderer || new MessageRenderer();
        
        this.initializeElements();
        this.setupEventListeners();
    }

    /**
     * Initialize conversations after user authentication is confirmed
     * This should be called after loginManager is available and user is authenticated
     */
    async initializeAfterAuth() {
        console.log('🔐 Initializing conversations after authentication...');
        
        // Wait a bit to ensure loginManager is fully initialized
        await new Promise(resolve => setTimeout(resolve, 100));
        
        if (this.getSessionToken()) {
            console.log('✅ Session token available, loading conversations...');
            await this.loadConversations();
        } else {
            console.log('⏳ Waiting for authentication to complete...');
            // Try again in a moment
            setTimeout(() => this.initializeAfterAuth(), 500);
        }
    }

    /**
     * Refresh conversations when user re-authenticates
     * This can be called after login or when session is refreshed
     */
    async refreshConversations() {
        console.log('🔄 Refreshing conversations...');
        if (this.getSessionToken()) {
            await this.loadConversations();
        }
    }

    initializeElements() {
        this.conversationsList = document.getElementById('conversationsList');
        this.newConversationBtn = document.getElementById('newConversationBtn');
        this.clearAllChatsBtn = document.getElementById('clearAllChatsBtn');
        this.clearHistoryBtn = document.getElementById('clearHistoryBtn');
        this.searchModeToggle = document.getElementById('searchModeToggle');
        this.searchModeDescription = document.getElementById('searchModeDescription');
        this.dataAgentSidebar = document.getElementById('dataAgentSidebar');
        this.toggleDataAgentBtn = document.getElementById('toggleDataAgentBtn');
        this.chatMessages = document.getElementById('chatMessages');
        
        // Initialize search mode state
        this.isVertexAIMode = true; // Default to Vertex AI
    }

    setupEventListeners() {
        // New conversation button
        this.newConversationBtn?.addEventListener('click', () => {
            this.startNewConversation();
        });

        // Clear all chats button
        this.clearAllChatsBtn?.addEventListener('click', () => {
            this.clearAllConversations();
        });

        // Clear history button (same as clear all chats)
        this.clearHistoryBtn?.addEventListener('click', () => {
            this.clearAllConversations();
        });

        // Search mode toggle
        this.searchModeToggle?.addEventListener('change', (e) => {
            this.toggleSearchMode(e.target.checked);
        });

        // Data agent sidebar toggle
        this.toggleDataAgentBtn?.addEventListener('click', () => {
            this.toggleDataAgentSidebar();
        });

        // 🎯 MASTER CLICK HANDLER - Single event delegation for all conversation interactions
        document.addEventListener('click', (e) => {
            this.handleMasterClick(e);
        });
        
        // Focus-based dropdown management (backup for better UX)
        document.addEventListener('focusin', (e) => {
            // Only hide dropdowns if focus moves to input fields or other interactive elements
            if ((e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'BUTTON') &&
                !e.target.closest('.conversation-dropdown') && 
                !e.target.closest('.conversation-menu-btn')) {
                
                if (this.hasOpenDropdowns()) {
                    console.log('📋 Dropdowns hidden - focus moved to interactive element');
                    this.hideAllDropdowns();
                }
            }
        });

        // Handle title edit blur (save changes)
        document.addEventListener('blur', (e) => {
            if (e.target.classList.contains('title-edit')) {
                const conversationId = e.target.closest('.conversation-title').dataset.conversationId;
                this.finishEditTitle(conversationId);
            }
        }, true);

        // Handle title edit enter key
        document.addEventListener('keydown', (e) => {
            if (e.target.classList.contains('title-edit') && e.key === 'Enter') {
                e.target.blur(); // Trigger the blur event to save
            }
            
            // Close dropdowns with Escape key
            if (e.key === 'Escape') {
                this.hideAllDropdowns();
                console.log('📋 Dropdowns hidden - Escape key pressed');
            }
        });
    }

    async loadConversations(showLoading = true) {
        if (this.loadingConversations) return;
        
        this.loadingConversations = true;

        if (showLoading) {
            this.showLoadingState();
        }

        try {
            const token = this.getSessionToken();
            if (!token) {
                console.log('⏳ No session token available yet, conversations will load after authentication');
                this.showEmptyState('Please log in to view conversations');
                return;
            }

            const response = await fetch('/api/conversations', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load conversations: ${response.status}`);
            }

            const data = await response.json();
            this.conversations = data.conversations || [];
            this.renderConversations();

            // Manage sidebar state based on conversations
                if (this.conversations.length === 0) {
                // No conversations - expand sidebar and show welcome message with quick actions
                    this.expandDataAgentSidebar();
                this.showWelcomeMessage();
            } else if (this.isFirstLoad) {
                // Has conversations - collapse sidebar and load last conversation
                    this.collapseDataAgentSidebar();
                // Load the most recent conversation
                if (this.conversations.length > 0) {
                    const lastConversation = this.conversations[0]; // Assuming sorted by most recent
                    console.log('🔄 Loading most recent conversation:', lastConversation.id);
                    await this.switchToConversation(lastConversation.id);  // ✅ FIX: Use .id instead of .conversation_id
                }
                this.isFirstLoad = false;
            }

        } catch (error) {
            console.error('Error loading conversations:', error);
            this.showEmptyState('Failed to load conversations');
        } finally {
            this.loadingConversations = false;
        }
    }

    renderConversations() {
        if (!this.conversationsList) return;

        if (this.conversations.length === 0) {
            this.showEmptyState('Ready to get started?<br><br>Click <strong>"New Chat"</strong> above or just start chatting with your data agent!');
            return;
        }

        const conversationsHTML = this.conversations.map(conversation => 
            this.createConversationHTML(conversation)
        ).join('');

        this.conversationsList.innerHTML = conversationsHTML;
        this.attachConversationEventListeners();
    }

    createConversationHTML(conversation) {
        const timeAgo = this.formatTimeAgo(new Date(conversation.updated_at));
        const isActive = conversation.id === this.currentConversationId;
        
        const lastMessage = conversation.last_message;
        const preview = lastMessage ? 
            (lastMessage.content || lastMessage.user_message || '').substring(0, 80) + (lastMessage.content ? '...' : '') : 
            'No messages yet';

        return `
            <div class="conversation-item ${isActive ? 'active' : ''}" data-conversation-id="${conversation.id}">
                <div class="conversation-main">
                    <div class="conversation-title" data-conversation-id="${conversation.id}">
                        <span class="title-display">${this.escapeHtml(conversation.title)}</span>
                        <input class="title-edit" type="text" value="${this.escapeHtml(conversation.title)}" style="display: none;">
                    </div>
                    <div class="conversation-actions">
                        <button class="conversation-menu-btn" 
                                data-conversation-id="${conversation.id}" 
                                title="More options">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <div class="conversation-dropdown" data-conversation-id="${conversation.id}">
                            <div class="dropdown-item rename-option" 
                                 data-conversation-id="${conversation.id}">
                                <i class="fas fa-edit"></i>
                                <span>Rename</span>
                            </div>
                            <div class="dropdown-item delete-option" 
                                 data-conversation-id="${conversation.id}">
                                <i class="fas fa-trash"></i>
                                <span>Delete</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="conversation-hover-details">
                <div class="conversation-preview">${this.escapeHtml(preview)}</div>
                <div class="conversation-time">${timeAgo}</div>
                </div>
            </div>
        `;
    }

    attachConversationEventListeners() {
        // ✅ No longer needed! All conversation clicks are handled by the master click handler
        // This eliminates the event listener multiplication and race conditions
        console.log('📋 Conversation event listeners managed by master click handler');
    }

    startNewConversation() {
        console.log('🆕 ConversationManager.startNewConversation() called');
        console.log('  - Current conversation ID before clear:', this.currentConversationId || 'NULL');
        console.trace('📍 Call stack trace:');
        
        // Hide any open dropdowns
        this.hideAllDropdowns();
        
        // Clear current chat and show welcome message with quick actions
        this.clearChatMessages();
        this.showWelcomeMessage();
        
        // IMPORTANT: Clear current conversation (no conversation until first message is sent)
        this.currentConversationId = null;
        console.log('✅ Conversation ID cleared, ready for new conversation');
        
        // Switch to 'new' conversation history (empty history)
        if (window.switchConversationHistory) {
            console.log('🔄 Switching conversation history to: new');
            window.switchConversationHistory('new');
        } else {
            console.log('⚠️ switchConversationHistory not available, skipping history switch');
        }
        
        // Update active state in UI (no conversation should be active)
        this.updateActiveConversation();
        
        // Focus on chat input
        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
            chatInput.focus();
        }

        // DEBUG: Add a temporary debug verification
        setTimeout(() => {
            console.log('🔍 DEBUG: Post-new-chat verification:');
            console.log('  - Current conversation ID:', this.currentConversationId || 'NULL');
            console.log('  - Chat messages content length:', this.chatMessages?.innerHTML?.length || 0);
            console.log('  - Chat messages contains welcome:', this.chatMessages?.innerHTML?.includes('CVS Pharmacy Knowledge Assist') || false);
        }, 100);

        // Expand data agent sidebar for new conversations (user needs to configure)
        this.expandDataAgentSidebar();
        
        console.log('✅ New conversation interface ready (no conversation ID set until first message)');
    }

    async clearAllConversations() {
        console.log('🗑️ ConversationManager.clearAllConversations() called');
        
        // Show confirmation dialog
        const confirmed = confirm('Are you sure you want to clear all conversations? This action cannot be undone.');
        if (!confirmed) {
            console.log('❌ Clear all conversations cancelled by user');
            return;
        }
        
        try {
            // Show loading state
            const clearBtn = document.getElementById('clearAllChatsBtn');
            if (clearBtn) {
                clearBtn.disabled = true;
                clearBtn.textContent = 'Clearing...';
            }
            
            console.log('🗑️ Sending request to clear all conversations...');
            
            // Get session token for authentication (same method as other functions)
            const token = this.getSessionToken();
            if (!token) {
                throw new Error('Authentication required. Please log in again.');
            }
            
            // Call backend API to clear all conversations
            const response = await fetch('/api/conversations/clear-all', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('✅ Clear all conversations response:', result);
            
            // Clear local state
            this.currentConversationId = null;
            this.conversations = [];
            
            // Clear UI elements
            this.clearChatMessages();
            await this.loadConversations(); // Reload conversations list
            this.updateActiveConversation();
            
            // Reset to welcome state
            this.showWelcomeMessage();
            
            // Focus chat input
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {
                chatInput.focus();
            }
            
            console.log('✅ All conversations cleared successfully');
            
            // Show success message
            alert(`Successfully cleared ${result.deleted_count || 0} conversations!`);
            
        } catch (error) {
            console.error('❌ Error clearing conversations:', error);
            
            // More specific error messages
            let errorMessage = 'Failed to clear conversations. ';
            if (error.message.includes('Authentication')) {
                errorMessage += 'Please refresh the page and try again.';
            } else if (error.message.includes('HTTP 5')) {
                errorMessage += 'Server error occurred. Please try again.';
            } else if (error.message.includes('fetch')) {
                errorMessage += 'Network error. Please check your connection.';
            } else {
                errorMessage += `Error: ${error.message}`;
            }
            
            alert(errorMessage);
        } finally {
            // Reset button state
            const clearBtn = document.getElementById('clearAllChatsBtn');
            if (clearBtn) {
                clearBtn.disabled = false;
                clearBtn.textContent = 'Clear All Chats';
            }
        }
    }

    async switchToConversation(conversationId) {
        console.log('🔄 ConversationManager.switchToConversation() called with ID:', conversationId || 'NULL');
        console.log('🔄 Current conversation ID:', this.currentConversationId || 'NULL');
        
        if (!conversationId) {
            console.error('❌ Cannot switch to conversation: conversationId is null/undefined');
            return;
        }
        
        if (conversationId === this.currentConversationId) {
            console.log('🔄 Already on this conversation, skipping switch');
            return;
        }
        
        // 1. Update current conversation immediately
        this.currentConversationId = conversationId;
        
        // 2. Switch message history to this conversation
        if (window.switchConversationHistory) {
            console.log('🔄 Switching conversation history to:', conversationId);
            window.switchConversationHistory(conversationId);
        } else {
            console.log('⚠️ switchConversationHistory not available, skipping history switch');
        }
        
        // 3. Update active state in UI immediately  
        this.updateActiveConversation();
        
        // 4. Show loading indicator immediately
        this.showChatLoading();
        
        // 5. Collapse data agent sidebar for existing conversations
        this.collapseDataAgentSidebar();

        // 🔄 ASYNC CONTENT LOADING - Fetch and display content in background
        try {
            const token = this.getSessionToken();
            if (!token) {
                console.error('No session token available');
                this.clearChatMessages();
                this.showWelcomeMessage(); // Fallback to welcome message
                return;
            }

            const response = await fetch(`/api/conversations/${conversationId}/messages`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to load conversation: ${response.status}`);
            }

            const data = await response.json();
            
            // Clear loading indicator and show content
            this.clearChatMessages();
            
            // Handle new MessageHistoryResponse format with full message history
            if (data.messages && data.messages.length > 0) {
                console.log(`✅ Loading ${data.messages.length} messages for conversation:`, conversationId);
                console.log('📋 Message data structure:', data.messages[0]); // Log first message structure
                
                // Display all messages in chronological order
                data.messages.forEach((message, index) => {
                    const sender = message.message_type === 'user' ? 'user' : 'bot';
                    console.log(`📝 Message ${index + 1}:`, { 
                        type: message.message_type, 
                        sender, 
                        content: message.content?.substring(0, 50) + '...',
                        hasChunks: !!(message.chunks && message.chunks.length > 0),
                        chunkTypes: message.chunks?.map(c => c.message_type) || [],
                        // Legacy checks for backward compatibility
                        hasSql: !!message.sql_query,
                        hasChart: !!message.chart_config
                    });
                    this.displayConversationMessage(message, sender);
                });
                
                console.log('✅ Conversation content loaded successfully:', conversationId);
            } else {
                // Show welcome message for empty conversations
                this.showWelcomeMessage();
                console.log('✅ Empty conversation loaded, showing welcome message:', conversationId);
            }

        } catch (error) {
            console.error('❌ Error loading conversation content:', error);
            
            // Clear loading and show error state
            this.clearChatMessages();
            
            // Show error message instead of alert (less disruptive)
            if (this.chatMessages) {
                this.chatMessages.innerHTML = `
                    <div class="message bot-message error-message">
                        <div class="message-avatar">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <div class="message-content">
                            <div class="message-text">
                                ⚠️ Failed to load conversation messages. Please try again.
                                <br><br>
                                <button class="retry-btn" onclick="conversationManager.switchToConversation('${conversationId}')">
                                    <i class="fas fa-redo"></i> Retry
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }
        }
    }

    toggleDropdown(conversationId) {
        const dropdown = document.querySelector(`.conversation-dropdown[data-conversation-id="${conversationId}"]`);
        const menuBtn = document.querySelector(`.conversation-menu-btn[data-conversation-id="${conversationId}"]`);
        
        if (!dropdown || !menuBtn) return;
        
        // Check if this dropdown is currently showing BEFORE hiding others
        const isCurrentlyShowing = dropdown.classList.contains('show');
        
        // Hide all dropdowns first
        this.hideAllDropdowns();
        
        // If it wasn't showing before, show it now (true toggle behavior)
        if (!isCurrentlyShowing) {
            dropdown.classList.add('show');
            menuBtn.classList.add('active');
            console.log('📋 Dropdown opened for conversation:', conversationId);
        } else {
            console.log('📋 Dropdown closed for conversation:', conversationId);
        }
    }
    
    hasOpenDropdowns() {
        return document.querySelectorAll('.conversation-dropdown.show').length > 0;
    }

    handleMasterClick(e) {
        // 🎯 Single event delegation system - routes all clicks predictably

        // 1. Handle conversation three-dot menu button clicks
        if (e.target.closest('.conversation-menu-btn')) {
            e.stopPropagation();
            const btn = e.target.closest('.conversation-menu-btn');
            const conversationId = btn.dataset.conversationId;
            console.log('🔘 Three-dot menu clicked:', conversationId);
            this.toggleDropdown(conversationId);
            return;
        }

        // 2. Handle dropdown option clicks (rename/delete)
        if (e.target.closest('.rename-option')) {
            e.stopPropagation();
            const option = e.target.closest('.rename-option');
            const conversationId = option.dataset.conversationId;
            console.log('✏️ Rename clicked:', conversationId);
            this.hideAllDropdowns();
            this.startEditTitle(conversationId);
            return;
        }

        if (e.target.closest('.delete-option')) {
            e.stopPropagation();
            const option = e.target.closest('.delete-option');
            const conversationId = option.dataset.conversationId;
            console.log('🗑️ Delete clicked:', conversationId);
            this.hideAllDropdowns();
            this.showDeleteConfirmModal(conversationId);
            return;
        }

        // 3. Handle conversation item clicks (switch conversation)
        const conversationItem = e.target.closest('.conversation-item');
        if (conversationItem && 
            !e.target.closest('.conversation-actions') && 
            !e.target.closest('.conversation-dropdown') && 
            !e.target.classList.contains('title-edit')) {
            
            e.stopPropagation();
            const conversationId = conversationItem.dataset.conversationId;
            
            if (conversationId) {
                const hadOpenDropdowns = this.hasOpenDropdowns();
                console.log('👆 Conversation clicked:', conversationId, '(full item including preview area)');
                
                // Always close dropdowns when switching conversations
                if (hadOpenDropdowns) {
                    this.hideAllDropdowns();
                }
                
                this.switchToConversation(conversationId);
            }
            return;
        }

        // 4. Handle delete modal clicks (close modal when clicking outside)
        const deleteModal = document.getElementById('deleteModal');
        if (deleteModal && e.target === deleteModal) {
            window.closeDeleteModal();
            return;
        }

        // 5. Handle clicks outside conversations sidebar (close dropdowns)
        const clickedInSidebar = e.target.closest('.conversations-sidebar');
        if (!clickedInSidebar) {
            if (this.hasOpenDropdowns()) {
                this.hideAllDropdowns();
                console.log('📋 Dropdowns hidden - outside sidebar');
            }
            return;
        }

        // 6. Handle clicks inside sidebar but not on specific elements (close dropdowns)
        const clickedOnDropdownElements = e.target.closest('.conversation-dropdown') || 
                                         e.target.closest('.conversation-menu-btn') ||
                                         e.target.closest('.conversation-main');
        
        if (clickedInSidebar && !clickedOnDropdownElements) {
            if (this.hasOpenDropdowns()) {
                this.hideAllDropdowns();
                console.log('📋 Dropdowns hidden - elsewhere in sidebar');
            }
        }
    }

    hideAllDropdowns() {
        const dropdowns = document.querySelectorAll('.conversation-dropdown.show');
        const menuBtns = document.querySelectorAll('.conversation-menu-btn.active');
        
        // Only log if there were actually dropdowns to hide
        if (dropdowns.length > 0) {
            console.log('📋 Hiding', dropdowns.length, 'open dropdown(s)');
        }
        
        dropdowns.forEach(dropdown => {
            dropdown.classList.remove('show');
        });
        
        menuBtns.forEach(btn => {
            btn.classList.remove('active');
        });
    }

    showDeleteConfirmModal(conversationId) {
        const conversation = this.conversations.find(c => c.id === conversationId);
        const title = conversation ? conversation.title : 'this conversation';
        
        // Store conversation ID for later use
        this.conversationToDelete = conversationId;
        
        // Update modal content
        const conversationNameElement = document.getElementById('conversationToDelete');
        if (conversationNameElement) {
            conversationNameElement.textContent = `"${title}"`;
        }
        
        // Show modal
        const modal = document.getElementById('deleteModal');
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    startEditTitle(conversationId) {
        const conversationItem = document.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (!conversationItem) return;
        
        const titleContainer = conversationItem.querySelector('.conversation-title');
        const titleDisplay = titleContainer.querySelector('.title-display');
        const titleEdit = titleContainer.querySelector('.title-edit');
        
        if (titleDisplay && titleEdit) {
            // Hide display, show input
            titleDisplay.style.display = 'none';
            titleEdit.style.display = 'block';
            titleEdit.focus();
            titleEdit.select(); // Select all text for easy editing
        }
    }

    async finishEditTitle(conversationId) {
        const conversationItem = document.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (!conversationItem) return;
        
        const titleContainer = conversationItem.querySelector('.conversation-title');
        const titleDisplay = titleContainer.querySelector('.title-display');
        const titleEdit = titleContainer.querySelector('.title-edit');
        
        if (titleDisplay && titleEdit) {
            const newTitle = titleEdit.value.trim();
            const oldTitle = titleDisplay.textContent;
            
            // Show display, hide input
            titleEdit.style.display = 'none';
            titleDisplay.style.display = 'block';
            
            // If title changed, update it
            if (newTitle && newTitle !== oldTitle) {
                console.log('💬 Updating conversation title:', conversationId, 'from', `"${oldTitle}"`, 'to', `"${newTitle}"`);
                
                // Optimistically update UI
                titleDisplay.textContent = newTitle;
                
                // Update backend
                const success = await this.updateConversationTitle(conversationId, newTitle);
                if (!success) {
                    // Revert on failure
                    titleDisplay.textContent = oldTitle;
                    titleEdit.value = oldTitle;
                    console.error('❌ Failed to update conversation title');
                }
            } else {
                // Reset to original title if empty or unchanged
                titleEdit.value = oldTitle;
            }
        }
    }

    async deleteConversation(conversationId) {
        try {
            const token = this.getSessionToken();
            if (!token) {
                console.error('No session token available for delete request');
                alert('Authentication required. Please log in again.');
                return;
            }

            const response = await fetch(`/api/conversations/${conversationId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('DELETE request failed:', response.status, errorText);
                throw new Error(`Failed to delete conversation: ${response.status} - ${errorText}`);
            }

            console.log('✅ Conversation deleted successfully:', conversationId);
            if (conversationId === this.currentConversationId) {
                this.clearChatMessages();
                this.showWelcomeMessage();
                this.currentConversationId = null;
            }

            // Reload conversations
            await this.loadConversations();

        } catch (error) {
            console.error('Error deleting conversation:', error);
            alert(`Failed to delete conversation: ${error.message}. Please try again.`);
        }
    }

    getCurrentConversationId() {
        console.log('📖 ConversationManager.getCurrentConversationId() called, returning:', this.currentConversationId || 'NULL');
        return this.currentConversationId;
    }

    setCurrentConversationId(conversationId) {
        console.log('🔄 ConversationManager.setCurrentConversationId() called');
        console.log('  - Old ID:', this.currentConversationId || 'NULL');
        console.log('  - New ID:', conversationId || 'NULL');
        console.trace('📍 Call stack trace:');
        
        this.currentConversationId = conversationId;
        
        // Verify the change was applied
        console.log('✅ Conversation ID updated to:', this.currentConversationId || 'NULL');
        
        this.updateActiveConversation();
    }

    async updateConversationTitleIfNew(conversationId, newTitle) {
        // Only update title if we haven't already updated it for this conversation
        if (this.conversationTitlesUpdated.has(conversationId)) {
            return false; // Already updated
        }

        const success = await this.updateConversationTitle(conversationId, newTitle);
        
        if (success) {
            this.conversationTitlesUpdated.add(conversationId);
        }
        
        return success;
    }

    async updateConversationTitle(conversationId, newTitle) {
        try {
            const token = this.getSessionToken();
            if (!token) {
                console.error('No session token available');
                return false;
            }

            // Truncate title if too long
            let title = newTitle.trim();
            title = title.split(/\s+/).join(" "); // Clean whitespace
            if (title.length > 50) {
                title = title.substring(0, 47) + "...";
            }

            const response = await fetch(`/api/conversations/${conversationId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: title
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to update conversation title: ${response.status}`);
            }

            console.log('Conversation title updated:', title);
            return true;

        } catch (error) {
            console.error('Error updating conversation title:', error);
            return false;
        }
    }

    // UI Helper Methods
    clearChatMessages() {
        console.log('🧹 Clearing chat messages...');
        if (this.chatMessages) {
            // Force clear all content
            this.chatMessages.innerHTML = '';
            
            // Verify it was cleared
            console.log('✅ Chat messages cleared, element content length:', this.chatMessages.innerHTML.length);
        } else {
            console.warn('⚠️ Chat messages element not found during clear');
        }
    }

    showChatLoading() {
        if (this.chatMessages) {
            this.chatMessages.innerHTML = `
                <div class="chat-loading">
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                    </div>
                    <div class="loading-text">Loading conversation...</div>
                </div>
            `;
        }
    }

    hideChatLoading() {
        const loadingEl = this.chatMessages?.querySelector('.chat-loading');
        if (loadingEl) {
            loadingEl.remove();
        }
    }

    showWelcomeMessage() {
        const welcomeHTML = `
            <div class="message bot-message">
                <div class="message-avatar">
                    <i class="fas fa-pills"></i>
                </div>
                <div class="message-content">
                    <div class="message-text">
                        Hello! I'm your CVS Pharmacy Knowledge Assist, here to help you with pharmacy policies, procedures, medication coverage, and member services.
                        <br><br>
                        Try asking me about:
                    </div>
                    
                    <!-- Quick Action Buttons -->
                    <div class="quick-actions">
                        <!-- Original basic questions -->
                        <button class="quick-action-btn" data-query="How do I add a credit card to a member's profile?">
                            "How do I add a credit card to a member's profile?"
                        </button>
                        <button class="quick-action-btn" data-query="How do I transfer a prescription from mail to retail?">
                            "How do I transfer a prescription from mail to retail?"
                        </button>
                        <button class="quick-action-btn" data-query="How do I submit a test claim for a commercial plan?">
                            "How do I submit a test claim for a commercial plan?"
                        </button>
                        
                        <!-- PDF retrieval test question -->
                        <button class="quick-action-btn" data-query="What is contraceptive coverage?">
                            "What is contraceptive coverage?"
                        </button>
                        
                        <!-- Advanced CVS pharmacy questions -->
                        <button class="quick-action-btn" data-query="How do I access a member's mail order history?">
                            "How do I access a member's mail order history?"
                        </button>
                        <button class="quick-action-btn" data-query="How does the Automatic Refill Program work?">
                            "How does the Automatic Refill Program work?"
                        </button>
                        <button class="quick-action-btn" data-query="What are the SilverScript enrollment procedures?">
                            "What are the SilverScript enrollment procedures?"
                        </button>
                        <button class="quick-action-btn" data-query="How do I handle prescription labels?">
                            "How do I handle prescription labels?"
                        </button>
                        <button class="quick-action-btn" data-query="What are the Medicare Part D top drugs?">
                            "What are the Medicare Part D top drugs?"
                        </button>
                        <button class="quick-action-btn" data-query="How do I process prior authorization claims?">
                            "How do I process prior authorization claims?"
                        </button>
                        <button class="quick-action-btn" data-query="What is the ScriptSync program?">
                            "What is the ScriptSync program?"
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        if (this.chatMessages) {
            this.chatMessages.innerHTML = welcomeHTML;
            
            // Add event listeners for quick action buttons
            this.setupQuickActionButtons();
        }
    }

    setupQuickActionButtons() {
        const quickActionButtons = this.chatMessages.querySelectorAll('.quick-action-btn');
        
        quickActionButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const query = btn.getAttribute('data-query');
                if (query) {
                    // Fill the chat input with the query
                    const chatInput = document.getElementById('chatInput');
                    if (chatInput) {
                        chatInput.value = query;
                        
                        // Trigger form submission
                        const chatForm = document.getElementById('chatForm');
                        if (chatForm) {
                            // Create and dispatch a submit event
                            const submitEvent = new Event('submit', { 
                                bubbles: true, 
                                cancelable: true 
                            });
                            chatForm.dispatchEvent(submitEvent);
                        }
                    }
                }
            });
        });
    }

    displayMessage(content, sender) {
        // Use the existing displayMessage function from script.js
        if (typeof window.displayMessage === 'function') {
            window.displayMessage(content, sender);
        } else {
            console.warn('displayMessage function not available');
        }
    }
    
    /**
     * Display a conversation message using the unified MessageRenderer for consistency
     */
    displayConversationMessage(message, sender) {
        if (sender === 'bot' || sender === 'assistant') {
            // Use MessageRenderer for assistant messages with chunks (new approach)
            if (message.chunks && Array.isArray(message.chunks) && message.chunks.length > 0) {
                console.log('🎯 Rendering historical assistant message with chunks:', message.id);
                console.log('📋 Available chunks:', message.chunks.map(c => c.message_type));
                
                // Use the MessageRenderer's method for rendering complete messages from chunks
                this.messageRenderer.renderAssistantMessageFromChunks(message, {
                    streaming: false,
                    scrollToBottom: false,
                    addFeedback: true,
                    addActions: true
                });
            } else {
                // Fallback for assistant messages without chunks (legacy or failed reconstruction)
                console.log('⚠️ Assistant message has no chunks, using fallback display:', message.id);
                if (typeof window.displayMessage === 'function') {
                    window.displayMessage(message.content, sender);
                } else {
                    console.error('❌ displayMessage function not available for fallback');
                }
            }
        } else {
            // Use basic display for user messages
            if (typeof window.displayMessage === 'function') {
                window.displayMessage(message.content, sender);
            } else {
                console.error('❌ displayMessage function not available for user messages');
            }
        }
    }
    
    /**
     * Add re-execute button to the last bot message
     */
    addReexecuteButtonToLastBotMessage(message) {
        const lastBotMessage = document.querySelector('.bot-message:last-child');
        if (!lastBotMessage) return;
        
        const messageContent = lastBotMessage.querySelector('.message-content');
        if (!messageContent) return;
        
        // Create re-execute button container
        const reexecuteContainer = document.createElement('div');
        reexecuteContainer.className = 'reexecute-container';
        
        // Create re-execute button
        const reexecuteBtn = document.createElement('button');
        reexecuteBtn.className = 'reexecute-btn';
        reexecuteBtn.innerHTML = '<i class="fas fa-redo"></i> Re-execute Query';
        
        // Add hover effect
        reexecuteBtn.addEventListener('mouseenter', () => {
            reexecuteBtn.style.background = '#0056b3';
        });
        reexecuteBtn.addEventListener('mouseleave', () => {
            reexecuteBtn.style.background = '#007bff';
        });
        
        // Add click handler
        reexecuteBtn.addEventListener('click', () => {
            this.handleReexecuteQuery(message);
        });
        
        // Create context input
        const contextInput = document.createElement('input');
        contextInput.type = 'text';
        contextInput.placeholder = 'Add context (optional)...';
        contextInput.className = 'reexecute-context';
        
        // Add elements to container
        reexecuteContainer.appendChild(reexecuteBtn);
        reexecuteContainer.appendChild(contextInput);
        
        // Add to message content
        messageContent.appendChild(reexecuteContainer);
    }
    


    updateActiveConversation() {
        const conversationItems = this.conversationsList?.querySelectorAll('.conversation-item');
        
        conversationItems?.forEach(item => {
            const conversationId = item.dataset.conversationId;
            if (conversationId === this.currentConversationId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    showLoadingState() {
        if (this.conversationsList) {
            this.conversationsList.innerHTML = `
                <div class="conversation-loading">
                    <i class="fas fa-spinner fa-spin"></i> Loading conversations...
                </div>
            `;
        }
    }

    showEmptyState(message) {
        if (this.conversationsList) {
            this.conversationsList.innerHTML = `
                <div class="conversation-loading">
                    ${message}
                </div>
            `;
        }
    }

    toggleDataAgentSidebar() {
        if (this.dataAgentSidebar) {
            this.dataAgentSidebar.classList.toggle('collapsed');
            
            const icon = this.toggleDataAgentBtn?.querySelector('i');
            if (icon) {
                if (this.dataAgentSidebar.classList.contains('collapsed')) {
                    icon.classList.remove('fa-chevron-right');
                    icon.classList.add('fa-chevron-left');
                } else {
                    icon.classList.remove('fa-chevron-left');
                    icon.classList.add('fa-chevron-right');
                }
            }
        }
    }

    expandDataAgentSidebar() {
        if (this.dataAgentSidebar) {
            this.dataAgentSidebar.classList.remove('collapsed');
            const icon = this.toggleDataAgentBtn?.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-chevron-left');
                icon.classList.add('fa-chevron-right');
            }
        }
    }

    collapseDataAgentSidebar() {
        if (this.dataAgentSidebar) {
            this.dataAgentSidebar.classList.add('collapsed');
            const icon = this.toggleDataAgentBtn?.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-chevron-right');
                icon.classList.add('fa-chevron-left');
            }
        }
    }

    // Utility Methods
    getSessionToken() {
        // Use the same method as BackendIntegrationService
        if (window.loginManager && window.loginManager.getSessionToken) {
            const token = window.loginManager.getSessionToken();
            if (token) {
                console.log('🔑 Session token retrieved successfully');
            } else {
                console.log('⚠️ No session token available from loginManager');
            }
            return token;
        } else {
            console.log('⚠️ loginManager not available yet');
            return null;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTimeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString();
    }

    toggleSearchMode() {
        const toggle = document.getElementById('searchModeToggle');
        const description = document.getElementById('searchModeDescription');
        
        if (toggle && description) {
            this.useLocalSearch = toggle.checked;
            
            if (this.useLocalSearch) {
                description.textContent = 'Using local search with instant template responses';
                console.log('🔄 Switched to local search mode');
            } else {
                description.textContent = 'Using AI-powered responses with document search';
                console.log('🔄 Switched to AI search mode');
            }
            
            // Save preference to localStorage
            localStorage.setItem('useLocalSearch', this.useLocalSearch.toString());
        }
    }

    getChatEndpoint() {
        return this.useLocalSearch ? '/api/chat/local' : '/api/chat';
    }
}

// Export for global usage
window.ConversationManager = ConversationManager;

// Global method to refresh conversations
window.refreshConversations = function() {
    if (window.conversationManager && window.conversationManager.refreshConversations) {
        window.conversationManager.refreshConversations();
    }
};

// Global modal functions for delete confirmation
window.closeDeleteModal = function() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.style.display = 'none';
    }
};

window.confirmDelete = function() {
    // Get the conversation manager instance
    const conversationManager = window.conversationManager;
    
    if (conversationManager && conversationManager.conversationToDelete) {
        conversationManager.deleteConversation(conversationManager.conversationToDelete);
        conversationManager.conversationToDelete = null;
    } else {
        console.error('❌ Missing conversation manager or conversationToDelete');
        alert('Error: Unable to delete conversation. Please refresh the page and try again.');
    }
    
    // Close modal
    window.closeDeleteModal();
};

// ✅ Modal closing is now handled by the master click handler
// No duplicate event listeners needed

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        window.closeDeleteModal();
    }
});
