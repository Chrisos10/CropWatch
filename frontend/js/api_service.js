/**
 * CropWatch API Service
 * Handles all communication with the backend hosted on Render
 * Base URL: https://cropwatch-1.onrender.com
 */

const API_BASE_URL = 'https://cropwatch-1.onrender.com';

// Token management
const TokenManager = {
    set: (token) => localStorage.setItem('cropwatch_token', token),
    get: () => localStorage.getItem('cropwatch_token'),
    remove: () => localStorage.removeItem('cropwatch_token'),
    exists: () => !!localStorage.getItem('cropwatch_token')
};

// User data management
const UserManager = {
    set: (user) => localStorage.setItem('cropwatch_user', JSON.stringify(user)),
    get: () => {
        const user = localStorage.getItem('cropwatch_user');
        return user ? JSON.parse(user) : null;
    },
    remove: () => localStorage.removeItem('cropwatch_user'),
    exists: () => !!localStorage.getItem('cropwatch_user')
};

// Base API request handler
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = TokenManager.get();
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token && !options.skipAuth) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        ...options,
        headers
    };
    
    try {
        const response = await fetch(url, config);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Authentication API
const AuthAPI = {
    /**
     * Register new user
     * @param {Object} userData - User registration data
     * @returns {Promise<Object>} Token and user data
     */
    register: async (userData) => {
        const response = await apiRequest('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
            skipAuth: true
        });
        
        // Save token and user data
        TokenManager.set(response.access_token);
        UserManager.set(response.user);
        
        return response;
    },
    
    /**
     * Login user
     * @param {string} username 
     * @param {string} password 
     * @returns {Promise<Object>}
     */
    login: async (username, password) => {
        const response = await apiRequest('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
            skipAuth: true
        });
        
        // Save token and user data
        TokenManager.set(response.access_token);
        UserManager.set(response.user);
        
        return response;
    },
    
    /**
     * Logout user
     */
    logout: async () => {
        try {
            await apiRequest('/api/auth/logout', { method: 'POST' });
        } finally {
            TokenManager.remove();
            UserManager.remove();
        }
    },
    
    /**
     * Get current user profile
     * @returns {Promise<Object>}
     */
    getProfile: async () => {
        return await apiRequest('/api/auth/profile', { method: 'GET' });
    },
    
    /**
     * Update user profile
     * @param {Object} updates
     * @returns {Promise<Object>}
     */
    updateProfile: async (updates) => {
        const response = await apiRequest('/api/auth/profile', {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
        
        // Update stored user data
        UserManager.set(response);
        
        return response;
    }
};

// Session Management API
const SessionAPI = {
    /**
     * Start automated storage session
     * @param {Object} sessionData
     * @returns {Promise<Object>}
     */
    start: async (sessionData) => {
        return await apiRequest('/api/sessions/start', {
            method: 'POST',
            body: JSON.stringify(sessionData)
        });
    },
    
    /**
     * Check if user has active session
     * @returns {Promise<Object>}
     */
    check: async () => {
        return await apiRequest('/api/sessions/check', { method: 'GET' });
    },
    
    /**
     * End active storage session
     * @returns {Promise<Object>} Confirmation message
     */
    end: async () => {
        return await apiRequest('/api/sessions/end', { method: 'POST' });
    },
    
    /**
     * Get upcoming check-in information
     * @returns {Promise<Object>}
     */
    getUpcomingCheckin: async () => {
        return await apiRequest('/api/sessions/upcoming-checkin', { method: 'GET' });
    }
};

// Prediction API
const PredictionAPI = {
    /**
     * Manual prediction
     * @param {Object} predictionData
     * @returns {Promise<Object>}
     */
    manual: async (predictionData) => {
        return await apiRequest('/api/predict/manual', {
            method: 'POST',
            body: JSON.stringify(predictionData)
        });
    }
};

// Notifications API
const NotificationAPI = {
    /**
     * Get all notifications for current user
     * @returns {Promise<Array>}
     */
    getAll: async () => {
        return await apiRequest('/api/notifications', { method: 'GET' });
    }
};

// Health Check API
const HealthAPI = {
    /**
     * Check API health status
     * @returns {Promise<Object>}
     */
    check: async () => {
        return await apiRequest('/health', { 
            method: 'GET',
            skipAuth: true 
        });
    }
};

// redirect to login if not authenticated
function requireAuth() {
    if (!TokenManager.exists()) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Check if user is logged in
function isLoggedIn() {
    return TokenManager.exists();
}

// Get current user from storage
function getCurrentUser() {
    return UserManager.get();
}

// Export all APIs
const CropWatchAPI = {
    Auth: AuthAPI,
    Session: SessionAPI,
    Prediction: PredictionAPI,
    Notification: NotificationAPI,
    Health: HealthAPI,
    Token: TokenManager,
    User: UserManager,
    requireAuth,
    isLoggedIn,
    getCurrentUser
};

// Make available globally
if (typeof window !== 'undefined') {
    window.CropWatchAPI = CropWatchAPI;
}