/**
 * Common JavaScript for all pages, Navigation & Authentication
 */

document.addEventListener('DOMContentLoaded', () => {
    setupLogoutHandler();
    updateUserDisplay();
    setupNavigationGuards();
    
    // Update notification badge on all pages
    const isNotificationsPage = window.location.pathname.includes('notifications.html');
    if (!isNotificationsPage && CropWatchAPI.isLoggedIn()) {
        updateNotificationBadge();
    }
});

// Setup logout button
function setupLogoutHandler() {
    const logoutBtn = document.querySelector('.logout');
    
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to logout?')) {
                return;
            }
            
            try {
                await CropWatchAPI.Auth.logout();
                
                // Clear notification tracking on logout
                localStorage.removeItem('notificationsViewed');
                localStorage.removeItem('lastViewedTime');
                
                window.location.href = 'login.html';
            } catch (error) {
                console.error('Logout error:', error);
                // Clear local storage anyway
                CropWatchAPI.Token.remove();
                CropWatchAPI.User.remove();
                localStorage.removeItem('notificationsViewed');
                localStorage.removeItem('lastViewedTime');
                window.location.href = 'login.html';
            }
        });
    }
}

// Update user display in header
function updateUserDisplay() {
    const user = CropWatchAPI.getCurrentUser();
    
    if (user) {
        const profileIcon = document.querySelector('.profile-icon');
        if (profileIcon) {
            profileIcon.title = `${user.first_name} ${user.last_name}`;
        }
    }
}

// Setup navigation guards for protected pages
function setupNavigationGuards() {
    const currentPage = window.location.pathname.split('/').pop();
    const protectedPages = ['index.html', 'analysis.html', 'notifications.html', 'profile.html'];
    
    // If on a protected page and not logged in, redirect to login
    if (protectedPages.includes(currentPage) && !CropWatchAPI.isLoggedIn()) {
        window.location.href = 'login.html';
    }
    
    // If on login/register page and already logged in, redirect to home
    if ((currentPage === 'login.html' || currentPage === 'register.html') && CropWatchAPI.isLoggedIn()) {
        window.location.href = 'index.html';
    }
}

// Update notification badge with unread logic
async function updateNotificationBadge() {
    if (!CropWatchAPI.isLoggedIn()) {
        return;
    }
    
    try {
        const notifications = await CropWatchAPI.Notification.getAll();
        const lastViewedTime = localStorage.getItem('lastViewedTime');
        const notificationsViewed = localStorage.getItem('notificationsViewed');
        
        const badge = document.querySelector('.badge');
        
        if (!badge) {
            return;
        }
        
        // If user has never viewed notifications, show all notifications count
        if (!notificationsViewed || !lastViewedTime) {
            if (notifications.length > 0) {
                badge.textContent = notifications.length;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
            return;
        }
        
        // Count notifications newer than last viewed time
        const lastViewed = new Date(lastViewedTime);
        const newNotifications = notifications.filter(notif => {
            const notifDate = new Date(notif.sent_at);
            return notifDate > lastViewed;
        });
        
        // Show badge only if there are NEW (unread) notifications
        if (newNotifications.length > 0) {
            badge.textContent = newNotifications.length;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
        
    } catch (error) {
        console.error('Error updating notification badge:', error);
        // Hide badge on error
        const badge = document.querySelector('.badge');
        if (badge) {
            badge.style.display = 'none';
        }
    }
}

// Auto-refresh badge every 5 minutes to catch new notifications
if (CropWatchAPI.isLoggedIn()) {
    setInterval(() => {
        const isNotificationsPage = window.location.pathname.includes('notifications.html');
        if (!isNotificationsPage) {
            updateNotificationBadge();
        }
    }, 5 * 60 * 1000); // 5 minutes
}

// Show global loading indicator
function showGlobalLoading(message = 'Loading...') {
    let loader = document.getElementById('global-loader');
    
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'global-loader';
        loader.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        
        loader.innerHTML = `
            <div style="background: white; padding: 30px; border-radius: 10px; text-align: center;">
                <div style="border: 4px solid #f3f3f3; border-top: 4px solid #4b6b3e; 
                            border-radius: 50%; width: 40px; height: 40px; 
                            animation: spin 1s linear infinite; margin: 0 auto 15px;"></div>
                <p style="margin: 0; color: #333; font-size: 16px;">${message}</p>
            </div>
        `;
        
        // Add spin animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(loader);
    }
    
    loader.style.display = 'flex';
}

// Hide global loading indicator
function hideGlobalLoading() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.style.display = 'none';
    }
}

// Make utilities available globally
window.showGlobalLoading = showGlobalLoading;
window.hideGlobalLoading = hideGlobalLoading;