/**
 * Notifications Page
 */

document.addEventListener('DOMContentLoaded', () => {
    // Require authentication
    if (!CropWatchAPI.requireAuth()) {
        return;
    }
    
    loadNotifications();
    loadUpcomingCheckin();
    setupImageRotation();
    
    // Clear the notification badge when page loads
    clearNotificationBadge();
});

// Load all notifications
async function loadNotifications() {
    try {
        const notifications = await CropWatchAPI.Notification.getAll();
        
        if (notifications.length === 0) {
            displayEmptyState();
            return;
        }
        
        displayNotifications(notifications);
        
    } catch (error) {
        console.error('Error loading notifications:', error);
        displayError('Failed to load notifications');
    }
}

// Display notifications in the list
function displayNotifications(notifications) {
    const container = document.querySelector('.notifications-list');
    
    const filterDropdown = container.querySelector('.filter-dropdown');
    
    // Clear existing notifications
    container.querySelectorAll('.notification-card').forEach(card => card.remove());
    
    // Add new notifications
    notifications.forEach((notification, index) => {
        const card = createNotificationCard(notification, index + 1);
        container.appendChild(card);
    });
    
    // Apply dynamic risk class assignment
    applyDynamicRiskClasses();
    setupCardSelection();
}

// Create notification card HTML
function createNotificationCard(notification, number) {
    const card = document.createElement('div');
    card.className = 'notification-card';
    const content = parseNotificationContent(notification.message_content);
    const date = new Date(notification.sent_at);
    
    // Determine risk color
    const riskColors = {
        low: '#4b6b3e',
        medium: '#d97706',
        high: '#dc2626'
    };
    
    const riskLevel = extractRiskLevel(notification.message_content);
    const riskColor = riskColors[riskLevel] || '#4b6b3e';
    
    card.innerHTML = `
        <div class="notification-header">
            <span class="notification-id">Notification_${String(number).padStart(2, '0')}</span>
            <div class="notification-meta">
                <span class="date">Date: ${formatDate(date)}</span>
                <span class="time">Time: ${formatTime(date)}</span>
            </div>
        </div>
        <div class="notification-body">
            <p class="location-label">Location: <span class="location-value">${content.location}</span></p>
            <p class="spoilage-risk" style="color: ${riskColor};">${content.spoilageText}</p>
            <p class="recommendation">
                <span class="recommendation-label">Recommendation:</span> ${content.recommendation}
            </p>
        </div>
    `;
    
    return card;
}

// Parse notification message content
function parseNotificationContent(message) {
    const lines = message.split('\n');
    
    let location = 'Unknown';
    let spoilageText = 'Status unknown';
    let recommendation = 'No recommendation available';
    
    lines.forEach(line => {
        if (line.startsWith('Location:')) {
            location = line.replace('Location:', '').trim();
        } else if (line.includes('spoilage') || line.includes('condition')) {
            spoilageText = line.trim();
        } else if (line.startsWith('Recommendation:')) {
            recommendation = line.replace('Recommendation:', '').trim();
        }
    });
    
    return { location, spoilageText, recommendation };
}

// Extract risk level from notification content
function extractRiskLevel(message) {
    const lowerMsg = message.toLowerCase();
    if (lowerMsg.includes('high') || lowerMsg.includes('critical') || lowerMsg.includes('alert')) {
        return 'high';
    } else if (lowerMsg.includes('medium') || lowerMsg.includes('warning')) {
        return 'medium';
    }
    return 'low';
}

// Load upcoming check-in information
async function loadUpcomingCheckin() {
    try {
        const checkin = await CropWatchAPI.Session.getUpcomingCheckin();
        
        const checkinCard = document.querySelector('.checkin-card ul');
        checkinCard.innerHTML = `
            <li>Time: <span>${checkin.next_check_time} (${checkin.next_check_date})</span></li>
            <li>Weather: <span>${checkin.weather_description}</span></li>
            <li>Location: <span>${checkin.location}</span></li>
            <li>Temperature: <span>${checkin.current_temperature}°C</span></li>
            <li>Humidity: <span>${checkin.current_humidity}%</span></li>
        `;
        
    } catch (error) {
        console.error('Error loading check-in info:', error);
        // If no active session, show message
        const checkinCard = document.querySelector('.checkin-card ul');
        checkinCard.innerHTML = `
            <li style="text-align: center; color: #666; font-style: italic;">
                No active session. Start a session in Analysis page to see upcoming check-ins.
            </li>
        `;
    }
}

// Setup image rotation
function setupImageRotation() {
    const imageElement = document.getElementById('rotatingImage');
    const dots = document.querySelectorAll('.image-dots .dot');
    
    // Check if elements exist
    if (!imageElement || dots.length === 0) {
        console.warn("Image rotation elements not found. Skipping rotation logic.");
        return;
    }
    
    const images = [
        "../images/maize.png",
        "../images/farmer.jpeg", 
        "../images/cornnn.jpeg", 
        "../images/corn_damaged.jpg"
    ];
    
    let currentIndex = 0;
    
    function rotateImage() {
        currentIndex = (currentIndex + 1) % images.length;
        imageElement.src = images[currentIndex];
        imageElement.alt = `Close-up of corn storage ${currentIndex + 1}`;
        
        // Update dots
        dots.forEach((dot, index) => {
            dot.classList.remove('active');
            if (index === currentIndex) {
                dot.classList.add('active');
            }
        });
    }
    
    // Rotate every 5 seconds
    setInterval(rotateImage, 5000);
    
    // Make dots clickable
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            currentIndex = index;
            imageElement.src = images[currentIndex];
            imageElement.alt = `Close-up of corn storage ${currentIndex + 1}`;
            dots.forEach((d, i) => {
                d.classList.remove('active');
                if (i === currentIndex) {
                    d.classList.add('active');
                }
            });
        });
    });
}

// Display empty state
function displayEmptyState() {
    const container = document.querySelector('.notifications-list');
    const filterDropdown = container.querySelector('.filter-dropdown');
    
    container.querySelectorAll('.notification-card').forEach(card => card.remove());
    
    const emptyState = document.createElement('div');
    emptyState.className = 'notification-card';
    emptyState.style.textAlign = 'center';
    emptyState.style.padding = '40px 20px';
    emptyState.innerHTML = `
        <p style="font-size: 18px; color: #666; margin-bottom: 10px;">No notifications yet</p>
        <p style="font-size: 14px; color: #999;">
            Start an automated session in the Analysis page to receive daily updates
        </p>
    `;
    
    container.appendChild(emptyState);
}

// Display error message
function displayError(message) {
    const container = document.querySelector('.notifications-list');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'notification-card';
    errorDiv.style.textAlign = 'center';
    errorDiv.style.padding = '30px 20px';
    errorDiv.style.background = '#fee';
    errorDiv.innerHTML = `<p style="color: #c33;">${message}</p>`;
    
    container.appendChild(errorDiv);
}

// Clear notification badge when user visits notifications page
function clearNotificationBadge() {
    localStorage.setItem('notificationsViewed', 'true');
    localStorage.setItem('lastViewedTime', new Date().toISOString());
    
    // Clear badge immediately on this page
    const badge = document.querySelector('.badge');
    if (badge) {
        badge.style.display = 'none';
    }
}

// Format date
function formatDate(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}-${month}-${year}`;
}

// Format time
function formatTime(date) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
}

// Apply dynamic risk class assignment based on spoilage percentage
function applyDynamicRiskClasses() {
    const notificationCards = document.querySelectorAll('.notification-card');
    
    notificationCards.forEach(card => {
        const spoilageElement = card.querySelector('.spoilage-risk');
        
        if (spoilageElement && spoilageElement.textContent) {
            // Regex to find the number before the '%' sign
            const textContent = spoilageElement.textContent;
            const match = textContent.match(/(\d+(?:\.\d+)?)%/);
            
            if (match) {
                const spoilagePercent = parseFloat(match[1]);
                let riskClass = '';
                
                // DEFINITION OF THE DYNAMIC RANGES
                if (spoilagePercent <= 10) {
                    riskClass = 'low-risk';
                } 
                else if (spoilagePercent <= 39) { 
                    // Medium Risk: 11% to 39%
                    riskClass = 'medium-risk';
                } 
                else {
                    // High Risk: 40% and above
                    riskClass = 'high-risk';
                }
                
                // Remove any existing risk classes before adding the new one
                card.classList.remove('low-risk', 'medium-risk', 'high-risk', 'placeholder-card');
                card.classList.add(riskClass);
            }
        }
    });
}

// Setup click selection for notification cards
function setupCardSelection() {
    const notificationCards = document.querySelectorAll('.notification-card');
    
    notificationCards.forEach(card => {
        card.addEventListener('click', () => {
            notificationCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
        });
    });
}