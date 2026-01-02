/**
 * CodeProof - Authentication Module
 *
 * Handles user authentication with real backend API.
 * Updated in Phase 14 to use real JWT authentication.
 *
 * Usage:
 *   await Auth.login('admin', 'admin') // Returns user object or throws error
 *   Auth.logout()
 *   Auth.getCurrentUser() // Returns current user or null
 *   Auth.hasRole('admin') // Returns true/false
 */

// LocalStorage keys (updated to remove prefix)
const STORAGE_KEY_USER = 'user';
const STORAGE_KEY_TOKEN = 'token';

/**
 * Authenticate user with username and password
 *
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Promise<object>} User object if successful
 * @throws {Error} If authentication fails
 */
async function login(username, password) {
  try {
    // Call backend API
    const response = await API.login(username, password);

    // API.login() already stores token and user in localStorage
    const user = getCurrentUser();

    // Dispatch login event
    document.dispatchEvent(new CustomEvent('userLoggedIn', {
      detail: { user }
    }));

    return user;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

/**
 * Register a new user
 *
 * @param {string} username - Username
 * @param {string} password - Password
 * @param {string} email - Optional email address
 * @returns {Promise<object>} Result object with success status
 * @throws {Error} If registration fails
 */
async function register(username, password, email = null) {
  try {
    // Call backend API
    const user = await API.register(username, password, email);

    // Auto-login after successful registration
    return await login(username, password);
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
}

/**
 * Logout current user
 */
function logout() {
  // Clear localStorage
  localStorage.removeItem(STORAGE_KEY_USER);
  localStorage.removeItem(STORAGE_KEY_TOKEN);

  // Dispatch logout event
  document.dispatchEvent(new CustomEvent('userLoggedOut'));

  // Redirect to login page
  window.location.href = '/auth/login.html';
}

/**
 * Get currently logged in user
 *
 * @returns {object|null} User object or null if not logged in
 */
function getCurrentUser() {
  const userStr = localStorage.getItem(STORAGE_KEY_USER);
  if (!userStr) return null;

  try {
    return JSON.parse(userStr);
  } catch (e) {
    console.error('Error parsing user data:', e);
    return null;
  }
}

/**
 * Check if user is logged in
 *
 * @returns {boolean} True if logged in, false otherwise
 */
function isLoggedIn() {
  const token = localStorage.getItem(STORAGE_KEY_TOKEN);
  const user = getCurrentUser();
  return token !== null && user !== null;
}

/**
 * Check if current user has a specific role
 *
 * @param {string} role - Role to check ('admin', 'problemsetter', 'user')
 * @returns {boolean} True if user has the role, false otherwise
 */
function hasRole(role) {
  const user = getCurrentUser();
  if (!user) return false;
  return user.role === role;
}

/**
 * Check if current user has at least a specific role level
 * Role hierarchy: admin > problemsetter > user
 *
 * @param {string} minRole - Minimum required role
 * @returns {boolean} True if user has at least this role level
 */
function hasMinRole(minRole) {
  const user = getCurrentUser();
  if (!user) return false;

  const roleHierarchy = {
    'user': 1,
    'problemsetter': 2,
    'admin': 3
  };

  const userLevel = roleHierarchy[user.role] || 0;
  const requiredLevel = roleHierarchy[minRole] || 0;

  return userLevel >= requiredLevel;
}

/**
 * Require authentication - redirect to login if not logged in
 *
 * @param {string} redirectUrl - URL to redirect to after login (default: current page)
 */
function requireAuth(redirectUrl = null) {
  if (!isLoggedIn()) {
    const returnUrl = redirectUrl || window.location.pathname;
    window.location.href = `/auth/login.html?redirect=${encodeURIComponent(returnUrl)}`;
    return false;
  }
  return true;
}

/**
 * Require specific role - redirect to dashboard if not authorized
 *
 * @param {string} role - Required role
 */
function requireRole(role) {
  if (!requireAuth()) return false;

  if (!hasRole(role)) {
    window.location.href = '/user/dashboard.html';
    return false;
  }
  return true;
}

/**
 * Update current user data in localStorage
 * (Called after user info changes on backend)
 *
 * @param {object} updates - Object with fields to update
 */
function updateCurrentUser(updates) {
  const user = getCurrentUser();
  if (!user) return null;

  const updatedUser = { ...user, ...updates };
  localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(updatedUser));

  // Dispatch update event
  document.dispatchEvent(new CustomEvent('userUpdated', {
    detail: { user: updatedUser }
  }));

  return updatedUser;
}

/**
 * Get JWT token
 *
 * @returns {string|null} Token or null
 */
function getToken() {
  return localStorage.getItem(STORAGE_KEY_TOKEN);
}

/**
 * Check if token exists
 *
 * @returns {boolean} True if token exists
 */
function isTokenValid() {
  const token = getToken();
  return token !== null && token.length > 0;
}

/**
 * Refresh user data from backend
 *
 * @returns {Promise<object>} Updated user object
 */
async function refreshUserData() {
  try {
    const user = await API.getCurrentUser();
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user));

    // Dispatch update event
    document.dispatchEvent(new CustomEvent('userUpdated', {
      detail: { user }
    }));

    return user;
  } catch (error) {
    console.error('Error refreshing user data:', error);
    // If token is invalid, logout
    if (error.message.includes('Unauthorized')) {
      logout();
    }
    throw error;
  }
}

// Initialize auth system on load
(function initAuth() {
  // Check if user is logged in
  if (isLoggedIn()) {
    // Note: refreshUserData() commented out for mock mode
    // Will be re-enabled when backend API is ready
    // refreshUserData().catch(err => {
    //   console.warn('Could not refresh user data:', err);
    // });
  }
})();

// Export as Auth object
const Auth = {
  login,
  register,
  logout,
  getCurrentUser,
  isLoggedIn,
  isAuthenticated: isLoggedIn, // Alias
  hasRole,
  hasMinRole,
  requireAuth,
  requireRole,
  updateCurrentUser,
  refreshUserData,
  getToken,
  isTokenValid
};

// Make Auth available globally
if (typeof window !== 'undefined') {
  window.Auth = Auth;
}
