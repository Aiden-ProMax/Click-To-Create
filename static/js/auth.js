/**
 * Authentication Helper Library
 * Provides common auth utilities: CSRF token, login/logout, etc.
 */

window.authHelpers = window.authHelpers || {};

/**
 * Fetch and cache CSRF token
 */
window.authHelpers.csrfToken = null;

window.authHelpers.ensureCsrfToken = async function() {
    if (this.csrfToken) {
        return this.csrfToken;
    }
    
    try {
        const res = await fetch('/api/auth/csrf/', { credentials: 'include' });
        const data = await res.json();
        this.csrfToken = data.csrfToken;
        return this.csrfToken;
    } catch (e) {
        console.error('Failed to get CSRF token:', e);
        return '';
    }
};

/**
 * Check authentication status
 * Redirects to login if not authenticated
 */
window.authHelpers.requireAuth = function(options = {}) {
    fetch('/api/auth/me/', { credentials: 'include' })
        .then(res => {
            if (!res.ok) {
                // Not authenticated, redirect to login
                window.location.href = '/login.html';
                return null;
            }
            return res.json();
        })
        .then(user => {
            if (user && options.onUser) {
                options.onUser(user);
            }
        })
        .catch(e => {
            console.error('Auth check failed:', e);
            window.location.href = '/login.html';
        });
};

/**
 * Perform logout
 * Calls logout API and redirects to login page
 */
window.authHelpers.authLogout = async function() {
    try {
        const csrfToken = await this.ensureCsrfToken();
        const res = await fetch('/api/auth/logout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken || ''
            },
            credentials: 'include'
        });
        
        if (res.ok) {
            // Clear cached token
            this.csrfToken = null;
            // Redirect to login
            window.location.href = '/login.html';
        } else {
            console.error('Logout API failed:', res.status);
            // Still redirect even if API fails
            window.location.href = '/login.html';
        }
    } catch (e) {
        console.error('Logout failed:', e);
        // Still redirect even if request fails
        window.location.href = '/login.html';
    }
};
