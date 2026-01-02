/**
 * CodeProof - Navigation Component
 *
 * Reusable header and navigation component for authenticated pages.
 * Automatically adjusts menu items based on user role.
 *
 * Usage:
 *   Navigation.render('dashboard') // Renders navigation with 'dashboard' highlighted
 *   Navigation.init() // Call after DOM loaded to setup event listeners
 */

const Navigation = {
  /**
   * Render the navigation header
   *
   * @param {string} activePage - Current page identifier (e.g., 'dashboard', 'problems')
   * @returns {string} HTML string for navigation
   */
  render(activePage = '') {
    const user = Auth.getCurrentUser();

    if (!user) {
      // If not logged in, redirect to login
      window.location.href = '/auth/login.html';
      return '';
    }

    const lang = (window.i18n && window.i18n.currentLang) ? window.i18n.currentLang : 'en';

    // Helper function to safely get translations
    const t = (key) => {
      if (window.i18n && window.i18n.t) {
        return window.i18n.t(key);
      }
      return key;
    };

    // Navigation items based on role
    const navItems = [
      {
        id: 'dashboard',
        href: '/user/dashboard.html',
        icon: '🏠',
        label: window.i18n.t('nav.dashboard'),
        roles: ['admin', 'problemsetter', 'user']
      },
      {
        id: 'problems',
        href: '/problems/list.html',
        icon: '🎯',
        label: window.i18n.t('nav.problems'),
        roles: ['admin', 'problemsetter', 'user']
      },
      {
        id: 'submissions',
        href: '/submissions/list.html',
        icon: '📝',
        label: window.i18n.t('nav.submissions'),
        roles: ['admin', 'problemsetter', 'user']
      },
      {
        id: 'ranking',
        href: '/ranking/leaderboard.html',
        icon: '🏆',
        label: window.i18n.t('nav.ranking'),
        roles: ['admin', 'problemsetter', 'user']
      },
      {
        id: 'blocks',
        href: '/blocks/explorer.html',
        icon: '🔗',
        label: window.i18n.t('nav.blocks'),
        roles: ['admin', 'problemsetter', 'user']
      },
      {
        id: 'problemsetter',
        href: '/problemsetter/dashboard.html',
        icon: '📋',
        label: window.i18n.t('nav.problemsetter'),
        roles: ['admin', 'problemsetter']
      },
      {
        id: 'admin',
        href: '/admin/panel.html',
        icon: '⚙️',
        label: window.i18n.t('nav.admin'),
        roles: ['admin']
      }
    ];

    // Filter nav items based on user role
    const allowedItems = navItems.filter(item =>
      item.roles.includes(user.role)
    );

    // Build nav links HTML
    const navLinksHTML = allowedItems.map(item => {
      const isActive = item.id === activePage;
      const activeClass = isActive ? 'active' : '';

      return `
        <a href="${item.href}" class="nav-link ${activeClass}">
          <span class="nav-icon">${item.icon}</span>
          <span class="nav-label">${item.label}</span>
        </a>
      `;
    }).join('');

    return `
      <header class="app-header">
        <div class="container">
          <nav class="app-nav">
            <!-- Logo -->
            <a href="/user/dashboard.html" class="app-logo">
              <span class="logo-icon">⚡</span>
              <span class="logo-text">CodeProof</span>
            </a>

            <!-- Navigation Links -->
            <div class="nav-links">
              ${navLinksHTML}
            </div>

            <!-- User Menu -->
            <div class="nav-actions">
              <!-- Language Selector -->
              <select id="language-selector-nav" class="select select-sm">
                <option value="en" ${lang === 'en' ? 'selected' : ''}>🇬🇧 EN</option>
                <option value="es" ${lang === 'es' ? 'selected' : ''}>🇪🇸 ES</option>
              </select>

              <!-- User Dropdown -->
              <div class="user-menu" id="user-menu">
                <button class="user-menu-trigger" id="user-menu-trigger">
                  <span class="user-avatar">${user.username.charAt(0).toUpperCase()}</span>
                  <span class="user-name">${user.username}</span>
                  <span class="user-role-badge badge badge-sm ${this.getRoleBadgeClass(user.role)}">
                    ${this.getRoleLabel(user.role)}
                  </span>
                  <span class="dropdown-arrow">▼</span>
                </button>

                <div class="user-menu-dropdown" id="user-menu-dropdown">
                  <div class="user-menu-header">
                    <div class="user-menu-name">${user.username}</div>
                    <div class="user-menu-email text-muted text-sm">
                      ${window.i18n.t('nav.role')}: ${this.getRoleLabel(user.role)}
                    </div>
                  </div>

                  <div class="user-menu-divider"></div>

                  <div class="user-menu-stats">
                    <div class="user-stat">
                      <span class="user-stat-label">${window.i18n.t('dashboard.totalScore')}</span>
                      <span class="user-stat-value">${user.total_score}</span>
                    </div>
                    <div class="user-stat">
                      <span class="user-stat-label">${window.i18n.t('dashboard.problemsSolved')}</span>
                      <span class="user-stat-value">${user.problems_solved}</span>
                    </div>
                  </div>

                  <div class="user-menu-divider"></div>

                  <a href="/user/profile.html" class="user-menu-item">
                    <span>👤</span>
                    <span data-i18n="nav.profile">${window.i18n.t('nav.profile')}</span>
                  </a>

                  <a href="#" class="user-menu-item" id="logout-btn">
                    <span>🚪</span>
                    <span data-i18n="auth.logout">${window.i18n.t('auth.logout')}</span>
                  </a>
                </div>
              </div>

              <!-- Mobile Menu Toggle -->
              <button class="mobile-menu-toggle" id="mobile-menu-toggle">
                <span class="hamburger-icon">☰</span>
              </button>
            </div>
          </nav>
        </div>
      </header>
    `;
  },

  /**
   * Get CSS class for role badge
   */
  getRoleBadgeClass(role) {
    const classes = {
      'admin': 'badge-error',
      'problemsetter': 'badge-info',
      'user': 'badge-secondary'
    };
    return classes[role] || 'badge-secondary';
  },

  /**
   * Get translated role label
   */
  getRoleLabel(role) {
    const labels = {
      'admin': window.i18n.t('roles.admin') || 'Admin',
      'problemsetter': window.i18n.t('roles.problemsetter') || 'Problemsetter',
      'user': window.i18n.t('roles.user') || 'User'
    };
    return labels[role] || role;
  },

  /**
   * Initialize navigation component
   * Sets up event listeners for user menu, logout, language selector
   */
  init() {
    // Language selector
    const langSelector = document.getElementById('language-selector-nav');
    if (langSelector) {
      langSelector.addEventListener('change', (e) => {
        window.i18n.setLanguage(e.target.value);
        // Reload page to update navigation labels
        window.location.reload();
      });
    }

    // User menu toggle
    const menuTrigger = document.getElementById('user-menu-trigger');
    const menuDropdown = document.getElementById('user-menu-dropdown');

    if (menuTrigger && menuDropdown) {
      menuTrigger.addEventListener('click', (e) => {
        e.stopPropagation();
        menuDropdown.classList.toggle('active');
      });

      // Close dropdown when clicking outside
      document.addEventListener('click', (e) => {
        if (!e.target.closest('#user-menu')) {
          menuDropdown.classList.remove('active');
        }
      });
    }

    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();

        const confirmed = confirm(window.i18n.t('auth.confirmLogout') || 'Are you sure you want to logout?');

        if (confirmed) {
          Auth.logout();
          Notifications.show(
            window.i18n.t('auth.logoutSuccess') || 'Logged out successfully',
            'info'
          );

          // Redirect to login page
          setTimeout(() => {
            window.location.href = '/auth/login.html';
          }, 500);
        }
      });
    }

    // Mobile menu toggle
    const mobileToggle = document.getElementById('mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (mobileToggle && navLinks) {
      mobileToggle.addEventListener('click', () => {
        navLinks.classList.toggle('mobile-active');
      });
    }
  },

  /**
   * Check if user is authenticated, redirect to login if not
   */
  requireAuth() {
    if (!Auth.isLoggedIn()) {
      window.location.href = '/auth/login.html';
      return false;
    }
    return true;
  },

  /**
   * Check if user has required role
   *
   * @param {string|string[]} requiredRoles - Required role(s)
   * @returns {boolean}
   */
  requireRole(requiredRoles) {
    const user = Auth.getCurrentUser();

    if (!user) {
      window.location.href = '/auth/login.html';
      return false;
    }

    const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];

    if (!roles.includes(user.role)) {
      Notifications.show(
        window.i18n.t('errors.unauthorized') || 'You do not have permission to access this page',
        'error'
      );

      setTimeout(() => {
        window.location.href = '/user/dashboard.html';
      }, 1500);

      return false;
    }

    return true;
  }
};

// Make Navigation available globally
window.Navigation = Navigation;
