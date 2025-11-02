/**
 * Profile Page frontend Integration
 */

document.addEventListener('DOMContentLoaded', () => {
    // Require authentication
    if (!CropWatchAPI.requireAuth()) {
        return;
    }
    
    loadUserProfile();
    setupEditMode();
    setupFormSubmit();
});

// Load and display user profile
async function loadUserProfile() {
    try {
        const user = await CropWatchAPI.Auth.getProfile();
        populateForm(user);
        updateHeaderName(user);
        
    } catch (error) {
        console.error('Error loading profile:', error);
        showMessage('Failed to load profile data', 'error');
    }
}

// Populate form with user data
function populateForm(user) {
    document.getElementById('username').value = user.username;
    document.getElementById('email').value = user.email;
    document.getElementById('first-name').value = user.first_name;
    document.getElementById('last-name').value = user.last_name;
    document.getElementById('telephone').value = user.telephone;
    document.getElementById('district').value = user.district;
    
    // Username cannot be edited
    document.getElementById('username').disabled = true;
    
    // Initially disable all other inputs
    disableFormInputs();
}

// Update header name
function updateHeaderName(user) {
    const nameElement = document.querySelector('.profile-header h2');
    nameElement.textContent = `${user.first_name} ${user.last_name}`;
}

// Setup edit mode toggle
function setupEditMode() {
    const editBtn = document.querySelector('.edit-btn');
    const form = document.querySelector('.profile-form');
    
    editBtn.addEventListener('click', () => {
        const isEditing = editBtn.textContent === 'Cancel';
        
        if (isEditing) {
            // Cancel editing and reload original data
            loadUserProfile();
            editBtn.textContent = 'Edit';
            hideActionButtons();
        } else {
            // Enable editing
            enableFormInputs();
            editBtn.textContent = 'Cancel';
            showActionButtons();
        }
    });
}

// Setup form submission
function setupFormSubmit() {
    const form = document.querySelector('.profile-form');
    const saveBtn = form.querySelector('.save-btn');
    const cancelBtn = form.querySelector('.cancel-btn');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const updates = {
            email: document.getElementById('email').value.trim(),
            first_name: document.getElementById('first-name').value.trim(),
            last_name: document.getElementById('last-name').value.trim(),
            telephone: document.getElementById('telephone').value.trim(),
            district: document.getElementById('district').value.trim()
        };
        
        // Validation
        if (!validateUpdates(updates)) {
            return;
        }
        
        saveBtn.disabled = true;
        saveBtn.innerHTML = `
            Saving... 
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-save">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                <polyline points="17 21 17 13 7 13 7 21"/>
                <polyline points="7 3 7 8 15 8"/>
            </svg>
        `;
        
        try {
            const updatedUser = await CropWatchAPI.Auth.updateProfile(updates);
            
            showMessage('Profile updated successfully!', 'success');
            updateHeaderName(updatedUser);
            
            // Exit edit mode
            document.querySelector('.edit-btn').textContent = 'Edit';
            disableFormInputs();
            hideActionButtons();
            
            saveBtn.disabled = false;
            saveBtn.innerHTML = `
                Save 
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-save">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                    <polyline points="17 21 17 13 7 13 7 21"/>
                    <polyline points="7 3 7 8 15 8"/>
                </svg>
            `;
            
        } catch (error) {
            showMessage(error.message || 'Failed to update profile', 'error');
            saveBtn.disabled = false;
            saveBtn.innerHTML = `
                Save 
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-save">
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                    <polyline points="17 21 17 13 7 13 7 21"/>
                    <polyline points="7 3 7 8 15 8"/>
                </svg>
            `;
        }
    });
    
    // Cancel button
    cancelBtn.addEventListener('click', () => {
        loadUserProfile();
        document.querySelector('.edit-btn').textContent = 'Edit';
        hideActionButtons();
    });
}

// Enable form inputs for editing
function enableFormInputs() {
    const inputs = document.querySelectorAll('.profile-form input:not(#username)');
    inputs.forEach(input => input.disabled = false);
}

// Disable form inputs
function disableFormInputs() {
    const inputs = document.querySelectorAll('.profile-form input:not(#username)');
    inputs.forEach(input => input.disabled = true);
}

// Show action buttons
function showActionButtons() {
    const buttonGroup = document.querySelector('.button-group');
    buttonGroup.style.display = 'flex';
}

// Hide action buttons
function hideActionButtons() {
    const buttonGroup = document.querySelector('.button-group');
    buttonGroup.style.display = 'none';
}

// Validate updates
function validateUpdates(updates) {
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(updates.email)) {
        showMessage('Please enter a valid email address', 'error');
        return false;
    }
    
    // Phone validation (Rwanda format)
    if (!updates.telephone.startsWith('+250') && !updates.telephone.startsWith('250')) {
        showMessage('Phone number must be a Rwanda number (+250...)', 'error');
        return false;
    }
    
    // Check all fields are filled
    if (!updates.first_name || !updates.last_name || !updates.district) {
        showMessage('Please fill in all fields', 'error');
        return false;
    }
    
    return true;
}

// Show message
function showMessage(message, type) {
    // Remove existing message
    const existingMsg = document.querySelector('.message');
    if (existingMsg) {
        existingMsg.remove();
    }
    
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
    
    const form = document.querySelector('.profile-form');
    form.insertBefore(msgDiv, form.firstChild);
    
    setTimeout(() => msgDiv.remove(), 5000);
}

// Initially hide action buttons
document.addEventListener('DOMContentLoaded', () => {
    const buttonGroup = document.querySelector('.button-group');
    if (buttonGroup) {
        buttonGroup.style.display = 'none';
    }
});