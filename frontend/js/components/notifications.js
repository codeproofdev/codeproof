/**
 * CodeProof - Toast Notification System
 *
 * Simple toast notification system for showing temporary messages to users.
 * Supports success, error, warning, and info types.
 *
 * Usage:
 *   showNotification('Success!', 'Your code was accepted', 'success');
 *   showNotification('Error', 'Invalid credentials', 'error');
 *   showNotification('Info', 'Judging in progress...', 'info');
 */

// Initialize notification container
let notificationContainer = null;

/**
 * Initialize the notification system
 * Creates the container element if it doesn't exist
 */
function initNotifications() {
  if (!notificationContainer) {
    notificationContainer = document.createElement('div');
    notificationContainer.className = 'notification-container';
    document.body.appendChild(notificationContainer);
  }
}

/**
 * Show a toast notification
 *
 * @param {string} title - Notification title
 * @param {string} message - Notification message
 * @param {string} type - Notification type: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds (default: 3000)
 * @returns {HTMLElement} The notification element
 */
function showNotification(title, message, type = 'info', duration = 3000) {
  // Initialize container if not exists
  initNotifications();

  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;

  // Icon based on type
  const icons = {
    success: '✓',
    error: '✗',
    warning: '⚠',
    info: 'ℹ'
  };

  const icon = icons[type] || icons.info;

  // Build notification HTML
  notification.innerHTML = `
    <div class="notification-icon">${icon}</div>
    <div class="notification-content">
      <div class="notification-title">${escapeHtml(title)}</div>
      ${message ? `<div class="notification-message">${escapeHtml(message)}</div>` : ''}
    </div>
    <button class="notification-close" aria-label="Close">&times;</button>
  `;

  // Add to container
  notificationContainer.appendChild(notification);

  // Setup close button
  const closeBtn = notification.querySelector('.notification-close');
  closeBtn.addEventListener('click', () => {
    removeNotification(notification);
  });

  // Auto-remove after duration
  if (duration > 0) {
    setTimeout(() => {
      removeNotification(notification);
    }, duration);
  }

  return notification;
}

/**
 * Remove a notification with animation
 *
 * @param {HTMLElement} notification - The notification element to remove
 */
function removeNotification(notification) {
  if (!notification || !notification.parentElement) return;

  // Add exit animation class
  notification.classList.add('notification-exit');

  // Remove from DOM after animation
  setTimeout(() => {
    if (notification.parentElement) {
      notification.parentElement.removeChild(notification);
    }
  }, 300);
}

/**
 * Clear all notifications
 */
function clearAllNotifications() {
  if (notificationContainer) {
    notificationContainer.innerHTML = '';
  }
}

/**
 * Escape HTML to prevent XSS
 *
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Convenience functions for specific types
function showSuccess(title, message, duration) {
  return showNotification(title, message, 'success', duration);
}

function showError(title, message, duration) {
  return showNotification(title, message, 'error', duration);
}

function showWarning(title, message, duration) {
  return showNotification(title, message, 'warning', duration);
}

function showInfo(title, message, duration) {
  return showNotification(title, message, 'info', duration);
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initNotifications);
} else {
  initNotifications();
}

// Export Notifications API
const Notifications = {
  show: showNotification,
  success: showSuccess,
  error: showError,
  warning: showWarning,
  info: showInfo,
  clear: clearAllNotifications
};

// Make available globally
if (typeof window !== 'undefined') {
  window.Notifications = Notifications;
}
