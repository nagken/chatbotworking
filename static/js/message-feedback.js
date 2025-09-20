/**
 * Message Feedback Handler for PSS Knowledge Assist
 * Clean, unified feedback system for Assistant messages
 * Works directly with ChatMessage IDs
 */

class MessageFeedbackHandler {
    constructor() {
        this.feedbackStates = new Map(); // Track feedback states by message ID
    }

    /**
     * Add feedback UI to an assistant message
     * Only works for Assistant message types
     */
    addFeedbackToMessage(assistantMessageContainer, messageId) {
        console.log('🎯 addFeedbackToMessage called:', {
            container: assistantMessageContainer,
            messageId: messageId,
            hasBotMessage: assistantMessageContainer?.classList?.contains('bot-message'),
            existingFeedback: !!assistantMessageContainer?.querySelector('.message-feedback')
        });
        
        // Only add feedback to bot messages
        if (!assistantMessageContainer.classList.contains('bot-message')) {
            console.log('❌ Not a bot message, skipping feedback');
            return;
        }

        // Don't add feedback twice
        if (assistantMessageContainer.querySelector('.message-feedback')) {
            console.log('⚠️ Feedback already exists, skipping');
            return;
        }

        const messageContent = assistantMessageContainer.querySelector('.message-content');
        if (!messageContent) {
            console.log('❌ No message content found, skipping feedback');
            return;
        }

        // Create feedback UI
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'message-feedback';
        feedbackDiv.innerHTML = this.createFeedbackHTML(messageId);
        
        messageContent.appendChild(feedbackDiv);
        console.log('✅ Feedback UI added to message:', messageId);
        
        setTimeout(() => {
            this.initializeFeedbackListeners(feedbackDiv, messageId);
            console.log('✅ Feedback listeners initialized for message:', messageId);
        }, 250);
    }

    /**
     * Create the feedback HTML structure
     */
    createFeedbackHTML(messageId) {
        return `
            <div class="feedback-buttons">
                <button class="feedback-btn thumbs-up" data-rating="positive" title="This was helpful">
                    <i class="fas fa-thumbs-up"></i>
                </button>
                <button class="feedback-btn thumbs-down" data-rating="negative" title="This wasn't helpful">
                    <i class="fas fa-thumbs-down"></i>
                </button>
            </div>
            <div class="feedback-expanded" style="display: none;">
                <div class="feedback-comment-section">
                    <label for="feedback-comment-${messageId}" class="feedback-label">
                        <span class="comment-text">Tell us more (optional):</span>
                    </label>
                    <textarea 
                        id="feedback-comment-${messageId}"
                        class="feedback-comment-input" 
                        placeholder="Your feedback helps us improve..."
                        maxlength="255"
                        rows="3"></textarea>
                    <div class="feedback-actions">
                        <button class="feedback-submit-btn">
                            <i class="fas fa-paper-plane"></i> Submit
                        </button>
                        <button class="feedback-cancel-btn">Cancel</button>
                    </div>
                    <div class="feedback-status"></div>
                </div>
            </div>
            <div class="feedback-submitted" style="display: none;">
                <div class="feedback-result">
                    <span class="feedback-result-text"></span>
                    <button class="feedback-edit-btn">Edit</button>
                </div>
            </div>
        `;
    }

    /**
     * Initialize event listeners for feedback UI
     */
    initializeFeedbackListeners(feedbackDiv, messageId) {
        const thumbsUp = feedbackDiv.querySelector('.thumbs-up');
        const thumbsDown = feedbackDiv.querySelector('.thumbs-down');
        const expandedSection = feedbackDiv.querySelector('.feedback-expanded');
        const commentInput = feedbackDiv.querySelector('.feedback-comment-input');
        const commentLabel = feedbackDiv.querySelector('.comment-text');
        const submitBtn = feedbackDiv.querySelector('.feedback-submit-btn');
        const cancelBtn = feedbackDiv.querySelector('.feedback-cancel-btn');
        const statusDiv = feedbackDiv.querySelector('.feedback-status');
        const submittedSection = feedbackDiv.querySelector('.feedback-submitted');
        const editBtn = feedbackDiv.querySelector('.feedback-edit-btn');

        let selectedRating = null;

        // Store state for this message
        this.feedbackStates.set(messageId, {
            selectedRating: null,
            isSubmitting: false,
            elements: {
                thumbsUp, thumbsDown, expandedSection, commentInput, 
                commentLabel, submitBtn, cancelBtn, statusDiv, 
                submittedSection, editBtn
            }
        });

        // Thumbs up click
        thumbsUp.addEventListener('click', () => {
            selectedRating = 'positive';
            this.selectRating(messageId, 'positive');
            this.showExpandedSection(messageId, 'positive');
        });

        // Thumbs down click
        thumbsDown.addEventListener('click', () => {
            selectedRating = 'negative';
            this.selectRating(messageId, 'negative');
            this.showExpandedSection(messageId, 'negative');
        });

        // Submit feedback
        submitBtn.addEventListener('click', async () => {
            await this.submitFeedback(messageId);
        });

        // Cancel feedback
        cancelBtn.addEventListener('click', () => {
            this.cancelFeedback(messageId);
        });

        // Edit existing feedback
        editBtn.addEventListener('click', () => {
            this.editFeedback(messageId);
        });
    }

    /**
     * Select a rating (thumbs up/down)
     */
    selectRating(messageId, rating) {
        console.log('🔄 Selecting rating:', rating);
        console.log('🔄 Feedback states:', this.feedbackStates);
        const state = this.feedbackStates.get(messageId);
        console.log('🔄 Current State:', state);
        if (!state) return;

        const { thumbsUp, thumbsDown } = state.elements;
        
        // Update button states
        thumbsUp.classList.toggle('active', rating === 'positive');
        thumbsDown.classList.toggle('active', rating === 'negative');
        
        // Store selected rating
        state.selectedRating = rating;
    }

    /**
     * Show expanded comment section
     */
    showExpandedSection(messageId, rating) {
        const state = this.feedbackStates.get(messageId);
        if (!state) return;

        const { expandedSection, commentLabel, commentInput } = state.elements;
        
        // Update label based on rating
        if (rating === 'negative') {
            commentLabel.textContent = 'Help us understand what could be improved:';
            commentInput.placeholder = 'What could we improve?';
            commentInput.classList.add('required');
        } else {
            commentLabel.textContent = 'Any additional feedback (optional):';
            commentInput.placeholder = 'Tell us what you liked...';
            commentInput.classList.remove('required');
        }
        
        // Show expanded section
        expandedSection.style.display = 'block';
        commentInput.focus();
    }

    /**
     * Cancel feedback and reset UI
     */
    cancelFeedback(messageId) {
        const state = this.feedbackStates.get(messageId);
        if (!state) return;

        const { thumbsUp, thumbsDown, expandedSection, commentInput } = state.elements;
        
        // Reset button states
        thumbsUp.classList.remove('active');
        thumbsDown.classList.remove('active');
        
        // Hide expanded section
        expandedSection.style.display = 'none';
        
        // Clear comment
        commentInput.value = '';
        
        // Reset state
        state.selectedRating = null;
    }

    /**
     * Submit feedback to backend
     */
    async submitFeedback(messageId) {
        const state = this.feedbackStates.get(messageId);
        if (!state || !state.selectedRating) return;

        const { commentInput, submitBtn, statusDiv } = state.elements;
        const comment = commentInput.value.trim();
        
        // Validate required comment for negative feedback
        if (state.selectedRating === 'negative' && !comment) {
            this.showStatus(statusDiv, 'Please tell us what could be improved', 'error');
            commentInput.focus();
            return;
        }

        // Prevent double submission
        if (state.isSubmitting) return;
        state.isSubmitting = true;

        // Update UI
        this.setSubmitButtonLoading(submitBtn, true);
        this.showStatus(statusDiv, 'Submitting feedback...', 'pending');

        try {
            const result = await this.submitFeedbackToAPI(
                messageId, 
                state.selectedRating === 'positive',
                comment
            );

            console.log('🔍 Feedback API result:', result);
            console.log('🔍 Result success property:', result.success);
            console.log('🔍 Result type:', typeof result.success);

            if (result && result.success === true) {
                // Reset submitting state before showing success UI
                state.isSubmitting = false;
                this.setSubmitButtonLoading(submitBtn, false);
                
                this.showFeedbackSubmitted(messageId, state.selectedRating === 'positive', comment);
                console.log('✅ Feedback submitted successfully for message:', messageId);
            } else {
                console.error('❌ API response indicates failure:', result);
                throw new Error(result?.message || 'Failed to submit feedback');
            }

        } catch (error) {
            console.error('❌ Feedback submission failed:', error);
            this.showStatus(statusDiv, 'Failed to submit feedback. Please try again.', 'error');
            
            // Always reset state on error
            state.isSubmitting = false;
            this.setSubmitButtonLoading(submitBtn, false);
            
            // Re-enable the form for retry
            commentInput.disabled = false;
            
            // Auto-hide error message after 5 seconds
            setTimeout(() => {
                this.showStatus(statusDiv, '', '');
            }, 5000);
        } finally {
            // Ensure we always reset the submitting state if it's still set
            if (state.isSubmitting) {
                console.log('⚠️ Force resetting submit state in finally block for message:', messageId);
                state.isSubmitting = false;
                this.setSubmitButtonLoading(submitBtn, false);
            }
        }
    }

    /**
     * Show feedback submitted state
     */
    showFeedbackSubmitted(messageId, isPositive, comment) {
        console.log('🔍 showFeedbackSubmitted called:', { messageId, isPositive, comment });
        
        const state = this.feedbackStates.get(messageId);
        if (!state) {
            console.error('❌ No state found for message:', messageId);
            return;
        }

        const { expandedSection, submittedSection } = state.elements;
        const resultText = submittedSection.querySelector('.feedback-result-text');
        
        console.log('🔍 UI elements found:', { 
            expandedSection: !!expandedSection,
            submittedSection: !!submittedSection,
            resultText: !!resultText
        });
        
        if (!expandedSection || !submittedSection || !resultText) {
            console.error('❌ Missing UI elements for feedback submitted state');
            return;
        }
        
        // Update result text
        const ratingText = isPositive ? '👍 Helpful' : '👎 Not helpful';
        const commentText = comment ? ` - "${comment}"` : '';
        resultText.textContent = `${ratingText}${commentText}`;
        
        console.log('🔍 Updated result text to:', resultText.textContent);
        
        // Hide expanded section, show submitted section
        expandedSection.style.display = 'none';
        submittedSection.style.display = 'block';
        
        // Reset state
        state.isSubmitting = false;
        
        console.log('✅ Feedback UI updated to submitted state');
        
        // Add a small delay and verify the UI state changed
        setTimeout(() => {
            console.log('🔍 Post-update verification:', {
                expandedVisible: expandedSection.style.display !== 'none',
                submittedVisible: submittedSection.style.display !== 'none',
                resultTextContent: resultText.textContent
            });
        }, 100);
    }

    /**
     * Edit existing feedback
     */
    editFeedback(messageId) {
        const state = this.feedbackStates.get(messageId);
        if (!state) return;

        const { expandedSection, submittedSection } = state.elements;
        
        // Show expanded section, hide submitted section
        submittedSection.style.display = 'none';
        expandedSection.style.display = 'block';
        
        console.log('🔄 Editing feedback for message:', messageId);
    }

    /**
     * Submit feedback to API
     */
    async submitFeedbackToAPI(messageId, isPositive, comment) {
        try {
            console.log('🔍 Starting feedback submission for messageId:', messageId);
            
            // First, test basic connectivity
            console.log('🔍 Testing server connectivity...');
            try {
                const pingResponse = await fetch('/quick-test');
                console.log('🔍 Server ping status:', pingResponse.status);
            } catch (pingError) {
                console.error('❌ Server ping failed:', pingError);
                return { success: false, message: 'Server not accessible' };
            }
            
            // Get session token for authentication
            const sessionToken = window.loginManager?.getSessionToken();
            console.log('🔍 Session token available:', !!sessionToken);
            
            if (!sessionToken) {
                console.error('❌ No session token available');
                return { success: false, message: 'Authentication required' };
            }
            
            // Try to get database message ID from DOM element
            const messageElement = document.getElementById(messageId);
            let databaseMessageId = messageElement?.dataset?.messageId;
            
            // If no database message ID, generate a UUID for testing/mock purposes
            if (!databaseMessageId) {
                console.log('⚠️ No dataset.messageId found, generating test UUID');
                // Generate a proper UUID format for the API
                databaseMessageId = 'aaaaaaaa-bbbb-cccc-dddd-' + Date.now().toString().slice(-12);
            }
            
            console.log('📤 Submitting feedback for message_id:', databaseMessageId);
            
            const requestBody = {
                is_positive: isPositive,
                feedback_comment: comment || null
            };
            
            console.log('� Request body:', requestBody);
            
            // Submit feedback to API with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
            
            const response = await fetch(`/api/feedback/messages/${databaseMessageId}/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionToken}`
                },
                body: JSON.stringify(requestBody),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            console.log('📥 Response status:', response.status);
            console.log('📥 Response ok:', response.ok);
            console.log('📥 Response headers:', Object.fromEntries(response.headers.entries()));
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Response not OK:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const result = await response.json();
            console.log('📥 Raw feedback response data:', result);
            console.log('📥 Response success field:', result.success);
            console.log('📥 Response success type:', typeof result.success);
            
            return result;

        } catch (error) {
            console.error('❌ Error submitting feedback:', error);
            
            let errorMessage = 'Network error occurred';
            if (error.name === 'AbortError') {
                errorMessage = 'Request timed out. Please try again.';
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            return {
                success: false,
                message: errorMessage
            };
        }
    }

    /**
     * Set submit button loading state
     */
    setSubmitButtonLoading(submitBtn, loading) {
        if (loading) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
            submitBtn.disabled = true;
        } else {
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit';
            submitBtn.disabled = false;
        }
    }

    /**
     * Show status message
     */
    showStatus(statusDiv, message, type) {
        statusDiv.textContent = message;
        statusDiv.className = `feedback-status ${type}`;
        
        // Clear status after delay for non-error messages
        if (type !== 'error') {
            setTimeout(() => {
                statusDiv.textContent = '';
                statusDiv.className = 'feedback-status';
            }, 3000);
        }
    }
}

// Create global instance
window.messageFeedbackHandler = new MessageFeedbackHandler();

// Backward compatibility function
window.addFeedbackToMessage = (messageContainer, messageId) => {
    window.messageFeedbackHandler.addFeedbackToMessage(messageContainer, messageId);
};
