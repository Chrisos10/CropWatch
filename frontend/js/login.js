/**
 * Login Page - Frontend Integration
 */

document.addEventListener('DOMContentLoaded', () => {
    // Check if already logged in
    if (CropWatchAPI.isLoggedIn()) {
        window.location.href = 'index.html';
        return;
    }
    
    const form = document.querySelector('.login-form form');
    const usernameInput = document.querySelector('input[type="text"]');
    const passwordInput = document.querySelector('input[type="password"]');
    const loginButton = document.querySelector('.btn');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = usernameInput.value.trim();
        const password = passwordInput.value;
        
        // Validation
        if (!username || !password) {
            showMessage('Please enter both username and password', 'error');
            return;
        }
        
        // Disable button during request
        loginButton.disabled = true;
        loginButton.textContent = 'Logging in...';
        
        try {
            // Call login API
            const response = await CropWatchAPI.Auth.login(username, password);
            
            showMessage('Login successful! Redirecting...', 'success');
            
            // Redirect to home page after short delay
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
            
        } catch (error) {
            showMessage(error.message || 'Login failed. Please check your credentials.', 'error');
            loginButton.disabled = false;
            loginButton.textContent = 'Login';
        }
    });
});

function showMessage(message, type) {
    // Remove existing message
    const existingMsg = document.querySelector('.message');
    if (existingMsg) {
        existingMsg.remove();
    }
    
    // Create message element
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.textContent = message;
    msgDiv.style.cssText = `
        padding: 12px 20px;
        margin: 10px 0;
        border-radius: 5px;
        text-align: center;
        font-size: 14px;
        ${type === 'error' ? 'background: #fee; color: #c33;' : 'background: #efe; color: #3c3;'}
    `;
    
    const form = document.querySelector('.login-form form');
    form.insertBefore(msgDiv, form.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => msgDiv.remove(), 5000);
}