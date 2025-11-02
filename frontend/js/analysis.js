/**
Analysis Page - Frontend Integration
*/

document.addEventListener('DOMContentLoaded', () => {
    // Require authentication
    if (!CropWatchAPI.requireAuth()) {
        return;
    }
    
    loadActiveSession();
    setupAutomatedForm();
    setupManualForm();
});

// Load and display active session if exists
async function loadActiveSession() {
    try {
        const response = await CropWatchAPI.Session.check();
        
        if (response.has_active_session) {
            const session = response.session;
            populateSessionForm(session);
            
            // Show end session button
            document.querySelector('.end-session-btn').style.display = 'block';
        } else {
            // No active session - show send button, hide end session
            document.querySelector('.end-session-btn').style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading session:', error);
    }
}

// Populate form with existing session data
function populateSessionForm(session) {
    document.getElementById('setup-technology').value = session.storage_technology;
    document.getElementById('setup-variety').value = session.variety;
    document.getElementById('setup-duration').value = session.initial_storage_time_days;
    document.getElementById('setup-damage').value = session.initial_total_damage_pct;
    document.getElementById('setup-impurities').value = session.grain_impurities_pct;
    
    // Disable inputs when session is active
    document.querySelectorAll('.setup-form input').forEach(input => {
        input.disabled = true;
    });
}

// Setup automated session form
function setupAutomatedForm() {
    const form = document.querySelector('.setup-form');
    const sendBtn = form.querySelector('.send-btn');
    const endBtn = form.querySelector('.end-session-btn');
    
    // Send button = Start new session
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const sessionData = {
            storage_technology: document.getElementById('setup-technology').value.trim(),
            variety: document.getElementById('setup-variety').value.trim().toLowerCase(),
            storage_time_days: parseInt(document.getElementById('setup-duration').value),
            initial_total_damage_pct: parseFloat(document.getElementById('setup-damage').value),
            grain_impurities_pct: parseFloat(document.getElementById('setup-impurities').value),
            initial_storage_time_days: parseInt(document.getElementById('setup-duration').value)
        };
        
        // Validation
        if (!validateSessionData(sessionData)) {
            return;
        }
        
        sendBtn.disabled = true;
        sendBtn.innerHTML = 'Starting... <span class="icon">➤</span>';
        
        try {
            await CropWatchAPI.Session.start(sessionData);
            showMessage('Automated session started successfully!', 'success', 'setup');
            
            // Reload session data
            setTimeout(() => {
                loadActiveSession();
            }, 1500);
            
        } catch (error) {
            showMessage(error.message || 'Failed to start session', 'error', 'setup');
            sendBtn.disabled = false;
            sendBtn.innerHTML = 'Send <span class="icon">➤</span>';
        }
    });
    
    // End session button
    endBtn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to end this storage session?')) {
            return;
        }
        
        endBtn.disabled = true;
        endBtn.textContent = 'Ending...';
        
        try {
            await CropWatchAPI.Session.end();
            showMessage('Session ended successfully!', 'success', 'setup');
            
            // Reset form
            document.querySelector('.setup-form').reset();
            document.querySelectorAll('.setup-form input').forEach(input => {
                input.disabled = false;
            });
            
            endBtn.style.display = 'none';
            endBtn.disabled = false;
            endBtn.textContent = 'End Session';
            
        } catch (error) {
            showMessage(error.message || 'Failed to end session', 'error', 'setup');
            endBtn.disabled = false;
            endBtn.textContent = 'End Session';
        }
    });
}

// Setup manual prediction form
function setupManualForm() {
    const form = document.querySelector('.check-form');
    const submitBtn = form.querySelector('.manual-btn');
    const resultBox = document.querySelector('.feedback-area');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const predictionData = {
            storage_technology: document.getElementById('check-technology').value.trim(),
            variety: document.getElementById('check-variety').value.trim().toLowerCase(),
            temperature: parseFloat(document.getElementById('check-temperature').value),
            humidity: parseFloat(document.getElementById('check-humidity').value),
            storage_time_days: parseInt(document.getElementById('check-duration').value),
            initial_total_damage_pct: parseFloat(document.getElementById('check-damage').value),
            grain_impurities_pct: parseFloat(document.getElementById('check-impurities').value)
        };
        
        // Validation
        if (!validateManualData(predictionData)) {
            return;
        }
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Analyzing... <span class="icon">➤</span>';
        resultBox.textContent = 'Processing...';
        
        try {
            const result = await CropWatchAPI.Prediction.manual(predictionData);
            
            // Display result
            displayPredictionResult(result, resultBox);
            
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Send <span class="icon">➤</span>';
            
        } catch (error) {
            resultBox.textContent = `Error: ${error.message}`;
            resultBox.style.color = '#c33';
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Send <span class="icon">➤</span>';
        }
    });
}

// Display prediction result with VERTICAL divider (25% | 75% split)
function displayPredictionResult(result, container) {
    const riskColors = {
        low: '#4b6b3e',
        medium: '#d97706',
        high: '#dc2626'
    };
    
    // Format like notification message
    const spoilageText = result.predicted_damage_pct === 0 
        ? 'No spoilage detected. Grain is in perfect condition.'
        : `Potential ${result.predicted_damage_pct.toFixed(1)}% spoilage detected.`;
    
    container.innerHTML = `
        <div style="display: flex; align-items: center; gap: 20px;">
            <div style="flex: 0.25;">
                <p style="margin: 0; font-size: 15px; color: ${riskColors[result.risk_level]}; font-weight: 500;">
                    ${spoilageText}
                </p>
            </div>
            
            <div style="
                width: 2px;
                height: 60px;
                background-color: #ddd;
                flex-shrink: 0;
            "></div>
            
            <div style="flex: 0.75;">
                <p style="margin: 0; line-height: 1.6; color: #333;">
                    <strong>Recommendation:</strong> ${result.recommendation_text}
                </p>
            </div>
        </div>
    `;
    container.style.color = '#333';
}

// Validation functions
function validateSessionData(data) {
    if (!data.storage_technology || !data.variety) {
        showMessage('Please fill in all fields', 'error', 'setup');
        return false;
    }
    
    if (data.variety !== 'native' && data.variety !== 'hybrid') {
        showMessage('Variety must be "native" or "hybrid"', 'error', 'setup');
        return false;
    }
    
    if (data.initial_total_damage_pct < 0 || data.initial_total_damage_pct > 100) {
        showMessage('Damage percentage must be between 0-100', 'error', 'setup');
        return false;
    }
    
    if (data.grain_impurities_pct < 0 || data.grain_impurities_pct > 100) {
        showMessage('Impurities percentage must be between 0-100', 'error', 'setup');
        return false;
    }
    
    return true;
}

function validateManualData(data) {
    if (!data.storage_technology || !data.variety) {
        showMessage('Please fill in all fields', 'error', 'manual');
        return false;
    }
    
    if (data.variety !== 'native' && data.variety !== 'hybrid') {
        showMessage('Variety must be "native" or "hybrid"', 'error', 'manual');
        return false;
    }
    
    if (data.temperature < 10 || data.temperature > 40) {
        showMessage('Temperature must be between 10-40°C', 'error', 'manual');
        return false;
    }
    
    if (data.humidity < 0 || data.humidity > 100) {
        showMessage('Humidity must be between 0-100%', 'error', 'manual');
        return false;
    }
    
    return true;
}

function showMessage(message, type, section) {
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
    
    const targetForm = section === 'setup' ? 
        document.querySelector('.setup-form') : 
        document.querySelector('.check-form');
    
    targetForm.insertBefore(msgDiv, targetForm.firstChild);
    
    setTimeout(() => msgDiv.remove(), 5000);
}