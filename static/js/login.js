/**
 * Login Authentication System
 * Handles user authentication with session management
 */

class LoginManager {
    constructor() {
        console.log('🔐 LoginManager constructor starting...');
        
        // Get DOM elements with error checking
        this.loginOverlay = document.getElementById('loginOverlay');
        this.loginForm = document.getElementById('loginForm');
        this.loginBtn = document.getElementById('loginBtn');
        this.loginError = document.getElementById('loginError');
        this.passwordToggle = document.getElementById('passwordToggle');
        this.passwordInput = document.getElementById('password');
        
        // Check if required elements exist
        if (!this.loginOverlay) {
            console.error('❌ loginOverlay element not found!');
            return;
        }
        if (!this.loginForm) {
            console.error('❌ loginForm element not found!');
            return;
        }
        
        console.log('🔐 LoginManager DOM elements found, initializing...');
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthStatus();
    }

    bindEvents() {
        // Form submission
        if (this.loginForm) {
            this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
        
        // Password toggle
        if (this.passwordToggle) {
            this.passwordToggle.addEventListener('click', () => this.togglePassword());
        }
        
        // Enter key on inputs
        const emailInput = document.getElementById('email');
        if (emailInput) {
            emailInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const passwordInput = document.getElementById('password');
                    if (passwordInput) passwordInput.focus();
                }
            });
        }
        
        // Forgot password link
        const forgotLink = document.querySelector('.forgot-password');
        if (forgotLink) {
            forgotLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleForgotPassword();
            });
        }
        
        // Clear error on input
        ['email', 'password'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('input', () => {
                    this.hideError();
                });
            }
        });
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('rememberMe').checked;
        
        console.log('🔐 Login attempt:', { email, rememberMe });
        
        // Basic validation
        if (!email || !password) {
            this.showError('Please enter both email and password');
            return;
        }
        
        this.setLoading(true);
        this.hideError();
        
        try {
            console.log('🔐 Calling authenticate...');
            const result = await this.authenticate(email, password, rememberMe);
            console.log('🔐 Authenticate result:', result);
            
            if (result.success) {
                console.log('🔐 Login successful, calling handleLoginSuccess...');
                this.handleLoginSuccess(result);
            } else {
                console.log('🔐 Login failed:', result.message);
                this.showError(result.message || 'Invalid credentials');
            }
        } catch (error) {
            console.error('🔐 Login error:', error);
            this.showError('Connection error. Please try again.');
        } finally {
            this.setLoading(false);
        }
    }

    async authenticate(email, password, rememberMe) {
        // Call the backend login API endpoint
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email, 
                    password: password,
                    remember_me: rememberMe
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                // Store session data with new database user fields
                const sessionData = {
                    // Legacy fields (keep for backward compatibility)
                    username: result.user.username,
                    email: result.user.email,
                    loginTime: new Date().toISOString(),
                    rememberMe: rememberMe,
                    sessionDuration: result.session_duration,
                    
                    // New database fields
                    userId: result.user.id || null,
                    isActive: result.user.is_active !== undefined ? result.user.is_active : true,
                    createdAt: result.user.created_at || null,
                    lastLoginAt: result.user.last_login_at || null,
                    
                    // Session authentication token
                    sessionToken: result.session_token || null
                };
                
                // Log successful database authentication
                console.log('✅ Database authentication successful:', {
                    userId: sessionData.userId,
                    email: sessionData.email,
                    username: sessionData.username,
                    isActive: sessionData.isActive
                });
                
                if (rememberMe) {
                    localStorage.setItem('pss_auth_session', JSON.stringify(sessionData));
                } else {
                    sessionStorage.setItem('pss_auth_session', JSON.stringify(sessionData));
                }
                
                return { 
                    success: true, 
                    user: result.user,
                    message: result.message
                };
            } else {
                return { 
                    success: false, 
                    message: result.message
                };
            }
        } catch (error) {
            console.error('Error authenticating user:', error);
            
            // Enhanced error handling for database authentication
            if (error.message.includes('fetch') || error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
                return { 
                    success: false, 
                    message: '🔌 Cannot connect to authentication server. Please ensure the backend is running and database is accessible.'
                };
            } else if (error.message.includes('500')) {
                return { 
                    success: false, 
                    message: '🗄️ Database authentication service temporarily unavailable. Please try again.'
                };
            } else if (error.message.includes('400')) {
                return { 
                    success: false, 
                    message: '❌ Invalid login credentials format. Please check your email and password.'
                };
            } else {
                return { 
                    success: false, 
                    message: '⚠️ Authentication system error. Please try again or contact support.'
                };
            }
        }
    }

    handleLoginSuccess(result) {
        console.log('🔐 handleLoginSuccess called with:', result);
        
        // Hide login overlay with animation
        this.loginOverlay.classList.add('hidden');
        console.log('🔐 Login overlay hidden');
        
        // Update UI to show logged-in state
        this.updateHeaderForLoggedInUser(result.user);
        console.log('🔐 Header updated for logged-in user');
        
        // Trigger conversation loading if conversation manager is available
        if (window.conversationManager && window.conversationManager.initializeAfterAuth) {
            console.log('🔐 Login successful, initializing conversations...');
            window.conversationManager.initializeAfterAuth();
        }
        
        // Show success message
        //this.showSuccessMessage(`Welcome back, ${result.user.username}!`);        
    }

    updateHeaderForLoggedInUser(user) {
        const userStatus = document.getElementById('userStatus');
        
        if (userStatus) {
            // Update to show welcome message
            userStatus.className = 'welcome logged-in';
            userStatus.innerHTML = `Welcome, ${user.username}`;
            
            // Get the parent container
            const userSignOut = userStatus.parentElement;
            
            if (userSignOut) {
                // Remove any existing logout button
                const existingLogoutBtn = userSignOut.querySelector('.logout-btn');
                if (existingLogoutBtn) {
                    existingLogoutBtn.remove();
                }
                
                // Create new logout button
                const logoutBtn = document.createElement('button');
                logoutBtn.className = 'button logout-btn';
                logoutBtn.onclick = () => {
                    loginManager.logout();
                };
                logoutBtn.title = 'Logout';
                logoutBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M16 17L21 12L16 7M21 12H9" stroke="#1A1A19" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M14 3H7C5.89543 3 5 3.89543 5 5V19C5 20.1046 5.89543 21 7 21H14" stroke="#1A1A19" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                `;
                
                // Style the button
                logoutBtn.style.display = 'flex';
                logoutBtn.style.alignItems = 'center';
                logoutBtn.style.justifyContent = 'center';
                logoutBtn.style.cursor = 'pointer';
                logoutBtn.style.border = 'none';
                logoutBtn.style.background = 'none';
                logoutBtn.style.padding = '4px';
                
                // Append to container
                userSignOut.appendChild(logoutBtn);
            }
        }
    }

    showSuccessMessage(message) {
        const validationMessage = document.getElementById('validationMessage');
        if (validationMessage) {
            validationMessage.innerHTML = `
                <div class="success-message">
                    <i class="fas fa-check-circle"></i>
                    ${message}
                </div>
            `;
            validationMessage.style.display = 'block';
            
            setTimeout(() => {
                validationMessage.style.display = 'none';
            }, 3000);
        }
    }

    checkAuthStatus() {
        const sessionData = this.getSessionData();
        
        if (sessionData) {
            // Check if user account is active (new database field)
            if (sessionData.isActive === false) {
                console.warn('🚫 User account is inactive, clearing session');
                this.clearSession();
                this.showError('Your account has been deactivated. Please contact support.');
                return;
            }
            
            // Check if session is still valid using backend-provided duration or fallback
            const loginTime = new Date(sessionData.loginTime);
            const now = new Date();
            
            // Use session duration from backend if available, otherwise fallback to default
            let maxAge;
            if (sessionData.sessionDuration) {
                maxAge = sessionData.sessionDuration * 1000; // Convert seconds to milliseconds
            } else {
                // Fallback to original logic
                maxAge = sessionData.rememberMe ? 24 * 60 * 60 * 1000 : 8 * 60 * 60 * 1000;
            }
            
            if (now - loginTime < maxAge) {
                // Session is valid, hide login overlay
                this.loginOverlay.classList.add('hidden');
                
                // Enhanced user display with database fields
                const displayUser = {
                    username: sessionData.username || sessionData.email?.split('@')[0] || 'User',
                    email: sessionData.email,
                    userId: sessionData.userId,
                    lastLoginAt: sessionData.lastLoginAt
                };
                
                this.updateHeaderForLoggedInUser(displayUser);
                
                console.log('✅ Session valid for user:', displayUser.email);
                
                // Trigger conversation loading if conversation manager is available
                if (window.conversationManager && window.conversationManager.initializeAfterAuth) {
                    console.log('🔐 Valid session found, initializing conversations...');
                    window.conversationManager.initializeAfterAuth();
                }
                
                return;
            } else {
                // Session expired
                console.log('⏰ Session expired, clearing session');
                this.clearSession();
            }
        }
        
        // Show login overlay
        this.loginOverlay.classList.remove('hidden');
    }

    getSessionData() {
        const sessionData = localStorage.getItem('pss_auth_session') || 
                           sessionStorage.getItem('pss_auth_session');
        
        if (sessionData) {
            try {
                return JSON.parse(sessionData);
            } catch (e) {
                console.error('Invalid session data:', e);
                this.clearSession();
            }
        }
        
        return null;
    }

    getSessionToken() {
        const sessionData = this.getSessionData();
        return sessionData ? sessionData.sessionToken : null;
    }

    isSessionValid() {
        const sessionData = this.getSessionData();
        if (!sessionData || !sessionData.sessionToken) {
            return false;
        }

        // Check if session has expired (client-side check)
        if (sessionData.sessionDuration) {
            const loginTime = new Date(sessionData.loginTime);
            const expiryTime = new Date(loginTime.getTime() + (sessionData.sessionDuration * 1000));
            const now = new Date();
            
            if (now > expiryTime) {
                console.log('⏰ Session expired, clearing local session');
                this.clearSession();
                return false;
            }
        }

        return true;
    }

    clearSession() {
        localStorage.removeItem('pss_auth_session');
        sessionStorage.removeItem('pss_auth_session');
    }

    async logout() {
        const sessionToken = this.getSessionToken();
        
        // If we have a session token, try to logout from the server
        if (sessionToken) {
            try {
                const response = await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${sessionToken}`
                    }
                });
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('✅ Server logout successful:', result.message);
                } else {
                    console.warn('⚠️ Server logout failed, but clearing local session anyway');
                }
            } catch (error) {
                console.error('❌ Logout request failed:', error);
                // Continue with local logout even if server logout fails
            }
        }
        
        // Always clear local session
        this.clearSession();
        
        // Reset UI to show clean "Please log in" state
        const userStatus = document.getElementById('userStatus');
        if (userStatus) {
            userStatus.className = 'welcome';
            userStatus.innerHTML = 'Please log in';
            
            // Remove logout button
            const userSignOut = userStatus.parentElement;
            if (userSignOut) {
                const logoutBtn = userSignOut.querySelector('.logout-btn');
                if (logoutBtn) {
                    logoutBtn.remove();
                }
            }
        }
        if (userStatus) {
            userStatus.innerHTML = `Please log in`;
            userStatus.className = 'user-status checking';
        }
        
        // Show login overlay
        this.loginOverlay.classList.remove('hidden');
        
        // Clear form
        this.loginForm.reset();
        this.hideError();
        
        // Show logout message
        this.showSuccessMessage('You have been logged out successfully');
    }

    togglePassword() {
        const type = this.passwordInput.type === 'password' ? 'text' : 'password';
        this.passwordInput.type = type;
        
        const icon = this.passwordToggle.querySelector('i');
        icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
    }

    setLoading(loading) {
        const btnText = this.loginBtn.querySelector('.btn-text');
        const btnSpinner = this.loginBtn.querySelector('.btn-spinner');
        
        if (loading) {
            btnText.style.display = 'none';
            btnSpinner.style.display = 'inline-block';
            this.loginBtn.disabled = true;
        } else {
            btnText.style.display = 'inline-block';
            btnSpinner.style.display = 'none';
            this.loginBtn.disabled = false;
        }
    }

    showError(message) {
        const errorText = this.loginError.querySelector('.error-text');
        errorText.textContent = message;
        this.loginError.style.display = 'flex';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideError();
        }, 5000);
    }

    hideError() {
        this.loginError.style.display = 'none';
    }

    handleForgotPassword() {
        alert('Please contact your system administrator to reset your password.\n\nFor login credentials, please check the users.json file or contact your administrator.');
    }


}

// Initialize login manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('🔐 Initializing LoginManager...');
        window.loginManager = new LoginManager();
        console.log('🔐 LoginManager initialized successfully');
    } catch (error) {
        console.error('🔐 Failed to initialize LoginManager:', error);
    }
});

// Also try to initialize on window load as backup
window.addEventListener('load', () => {
    if (!window.loginManager) {
        try {
            console.log('🔐 Backup initialization of LoginManager...');
            window.loginManager = new LoginManager();
            console.log('🔐 LoginManager backup initialization successful');
        } catch (error) {
            console.error('🔐 Failed backup initialization of LoginManager:', error);
        }
    }
});
