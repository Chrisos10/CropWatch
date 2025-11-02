/**
 * Register Page frontend Integration
 */

document.addEventListener('DOMContentLoaded', () => {
    // Check if already logged in
    if (CropWatchAPI.isLoggedIn()) {
        window.location.href = 'index.html';
        return;
    }
    
    const form = document.querySelector('.register-form form');
    const submitButton = form.querySelector('.btn');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Get form values
        const formData = {
            first_name: document.getElementById('firstname').value.trim(),
            last_name: document.getElementById('lastname').value.trim(),
            username: document.getElementById('username').value.trim(),
            email: document.getElementById('email').value.trim(),
            telephone: document.getElementById('telephone').value.trim(),
            district: document.getElementById('address').value.trim(),
            password: document.getElementById('password').value
        };
        
        // Validation
        if (!validateForm(formData)) {
            return;
        }
        
        // Disable button during request
        submitButton.disabled = true;
        submitButton.textContent = 'Creating account...';
        
        try {
            // Call register API
            const response = await CropWatchAPI.Auth.register(formData);
            
            showMessage('Registration successful! Redirecting...', 'success');
            
            // Redirect to home page after short delay
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
            
        } catch (error) {
            const errorMsg = error.message || 'Registration failed. Please try again.';
            showMessage(errorMsg, 'error');
            submitButton.disabled = false;
            submitButton.textContent = 'Register';
        }
    });
});

function validateForm(data) {
    // Check required fields
    if (!data.first_name || !data.last_name || !data.username || 
        !data.email || !data.telephone || !data.district || !data.password) {
        showMessage('Please fill in all fields', 'error');
        return false;
    }
    
    // Username validation
    if (data.username.length < 3) {
        showMessage('Username must be at least 3 characters', 'error');
        return false;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
        showMessage('Please enter a valid email address', 'error');
        return false;
    }
    
    // Phone validation (Rwanda format)
    if (!data.telephone.startsWith('+250') && !data.telephone.startsWith('250')) {
        showMessage('Phone number must be a Rwanda number (+250...)', 'error');
        return false;
    }
    
    // Password validation
    if (data.password.length < 6) {
        showMessage('Password must be at least 6 characters', 'error');
        return false;
    }
    
    return true;
}

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
        margin: 15px 0;
        border-radius: 5px;
        text-align: center;
        font-size: 14px;
        ${type === 'error' ? 'background: #fee; color: #c33;' : 'background: #efe; color: #3c3;'}
    `;
    
    const form = document.querySelector('.register-form form');
    form.insertBefore(msgDiv, form.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => msgDiv.remove(), 5000);
}