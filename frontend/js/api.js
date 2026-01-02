/**
 * CodeProof - API Client
 *
 * Real API client for CodeProof backend (FastAPI).
 * Handles authentication, problems, submissions, ranking, and blocks.
 *
 * Updated in Phase 14 to use real backend endpoints.
 *
 * Usage:
 *   const problems = await API.getProblems();
 *   const problem = await API.getProblem(1);
 *   const submission = await API.submitCode(1, 'print("Hello")');
 */

const API = {
  baseURL: '/api',

  /**
   * Helper: Get authorization header if logged in
   */
  getAuthHeader() {
    const token = localStorage.getItem('token');
    if (token) {
      return { 'Authorization': `Bearer ${token}` };
    }
    return {};
  },

  /**
   * Helper: Make authenticated request
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...this.getAuthHeader(),
      ...options.headers
    };

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);

      // Handle 401 Unauthorized - clear token and redirect to login
      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login.html';
        throw new Error('Unauthorized - please login again');
      }

      // Handle other errors
      if (!response.ok) {
        const error = await response.json().catch(() => ({detail: response.statusText}));
        console.error('API Error Details:', error);
        throw new Error(error.detail || JSON.stringify(error) || `HTTP ${response.status}`);
      }

      // Return JSON response
      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  },

  // ============================================
  // AUTHENTICATION
  // ============================================

  /**
   * Register new user
   */
  async register(username, password, email = null) {
    return await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email })
    });
  },

  /**
   * Login user
   * Returns: { access_token, token_type }
   */
  async login(username, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });

    // Store token
    localStorage.setItem('token', response.access_token);

    // Fetch user info and store it
    const user = await this.getCurrentUser();
    localStorage.setItem('user', JSON.stringify(user));

    return response;
  },

  /**
   * Logout user (client-side)
   */
  async logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/auth/login.html';
  },

  /**
   * Get current user info
   */
  async getCurrentUser() {
    return await this.request('/auth/me', {
      method: 'GET'
    });
  },

  // ============================================
  // PROBLEMS
  // ============================================

  /**
   * Get list of problems
   * @param {Object} filters - Optional filters (tier, status, etc.)
   */
  async getProblems(filters = {}) {
    const params = new URLSearchParams();

    if (filters.tier) params.append('tier', filters.tier);
    if (filters.status) params.append('status', filters.status);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);

    const queryString = params.toString();
    const url = `/problems${queryString ? '?' + queryString : ''}`;

    return await this.request(url, { method: 'GET' });
  },

  /**
   * Get single problem details
   */
  async getProblem(id) {
    return await this.request(`/problems/${id}`, { method: 'GET' });
  },

  /**
   * Get problem editorial
   * @param {number} id - Problem ID
   * @param {string} language - Language code (en or es)
   * @returns {Promise<string>} Editorial markdown content
   */
  async getProblemEditorial(id, language = 'en') {
    const url = `${this.baseURL}/problems/${id}/editorial?language=${language}`;
    const headers = {
      ...this.getAuthHeader()
    };

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers
      });

      // Handle 404 - editorial not available
      if (response.status === 404) {
        return null;
      }

      // Handle 401 Unauthorized
      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login.html';
        throw new Error('Unauthorized - please login again');
      }

      // Handle other errors
      if (!response.ok) {
        const error = await response.json().catch(() => ({detail: response.statusText}));
        console.error('API Error Details:', error);
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      // Return text response (markdown content)
      return await response.text();
    } catch (error) {
      console.error(`API Error [/problems/${id}/editorial]:`, error);
      throw error;
    }
  },

  /**
   * Get problem reference file (test_generator or official_solution)
   * @param {number} id - Problem ID
   * @param {string} fileType - File type (test_generator or official_solution)
   * @returns {Promise<string>} Reference file content
   */
  async getProblemReferenceFile(id, fileType) {
    const url = `${this.baseURL}/problems/${id}/reference/${fileType}`;
    const headers = {
      ...this.getAuthHeader()
    };

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers
      });

      // Handle 404 - file not available
      if (response.status === 404) {
        return null;
      }

      // Handle 401 Unauthorized
      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login.html';
        throw new Error('Unauthorized - please login again');
      }

      // Handle other errors
      if (!response.ok) {
        const error = await response.json().catch(() => ({detail: response.statusText}));
        console.error('API Error Details:', error);
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      // Return text response
      return await response.text();
    } catch (error) {
      console.error(`API Error [/problems/${id}/reference/${fileType}]:`, error);
      throw error;
    }
  },

  /**
   * Create a new problem (problemsetter only)
   * @param {Object} problemData - Problem data including title, description, tests, etc.
   * @returns {Promise<Object>} Created problem object
   */
  async createProblem(problemData) {
    return await this.request('/problems', {
      method: 'POST',
      body: JSON.stringify(problemData)
    });
  },

  /**
   * Update an existing problem (problemsetter/admin only)
   * @param {number} problemId - Problem ID to update
   * @param {Object} problemData - Updated problem data
   * @returns {Promise<Object>} Updated problem object
   */
  async updateProblem(problemId, problemData) {
    return await this.request(`/problems/${problemId}`, {
      method: 'PUT',
      body: JSON.stringify(problemData)
    });
  },

  /**
   * Approve a problem (admin only)
   * @param {number} problemId - Problem ID to approve
   * @returns {Promise<Object>} Updated problem object with status=APPROVED
   */
  async approveProblem(problemId) {
    return await this.request(`/problems/${problemId}/approve`, {
      method: 'PUT'
    });
  },

  /**
   * Reject a problem (admin only)
   * @param {number} problemId - Problem ID to reject
   * @returns {Promise<Object>} Updated problem object with status=REJECTED
   */
  async rejectProblem(problemId) {
    return await this.request(`/problems/${problemId}/reject`, {
      method: 'PUT'
    });
  },

  /**
   * Delete a problem (admin only)
   * @param {number} problemId - Problem ID to delete
   * @param {boolean} force - Force delete even if problem has submissions (default: false)
   * @returns {Promise<Object>} Success message
   */
  async deleteProblem(problemId, force = false) {
    const url = force ? `/problems/${problemId}?force=true` : `/problems/${problemId}`;
    return await this.request(url, {
      method: 'DELETE'
    });
  },

  /**
   * Get pending problems for review (admin only)
   * @returns {Promise<Array>} Array of pending problems
   */
  async getPendingProblems() {
    return await this.request('/admin/problems/pending', { method: 'GET' });
  },

  // ============================================
  // PROBLEM PACKAGES (File-based storage)
  // ============================================

  /**
   * Upload a complete problem package as ZIP
   * @param {File} file - ZIP file containing problem.yml, descriptions, and test cases
   * @returns {Promise<Object>} Created problem object
   */
  async uploadProblemPackage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${this.baseURL}/problems/upload-package`;
    const headers = {
      ...this.getAuthHeader()
      // Don't set Content-Type - browser will set it with boundary for multipart/form-data
    };

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login.html';
        throw new Error('Unauthorized - please login again');
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({detail: response.statusText}));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [upload-package]:`, error);
      throw error;
    }
  },

  /**
   * Upload test cases for an existing problem
   * @param {number} problemId - Problem ID
   * @param {File} file - ZIP file containing test cases
   * @returns {Promise<Object>} Success message
   */
  async uploadTestCases(problemId, file) {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${this.baseURL}/problems/${problemId}/upload-testcases`;
    const headers = {
      ...this.getAuthHeader()
    };

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login.html';
        throw new Error('Unauthorized - please login again');
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({detail: response.statusText}));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [upload-testcases]:`, error);
      throw error;
    }
  },

  /**
   * Export problem package as ZIP
   * @param {number} problemId - Problem ID
   * @returns {Promise<Blob>} ZIP file blob
   */
  async exportProblem(problemId) {
    const url = `${this.baseURL}/problems/${problemId}/export`;
    const headers = {
      ...this.getAuthHeader()
    };

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login.html';
        throw new Error('Unauthorized - please login again');
      }

      if (!response.ok) {
        const error = await response.json().catch(() => ({detail: response.statusText}));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.blob();
    } catch (error) {
      console.error(`API Error [export-problem]:`, error);
      throw error;
    }
  },

  /**
   * Get problem package information
   * @param {number} problemId - Problem ID
   * @returns {Promise<Object>} Package info with size, file count, test cases, etc.
   */
  async getProblemPackageInfo(problemId) {
    return await this.request(`/problems/${problemId}/package`, { method: 'GET' });
  },

  // ============================================
  // CATEGORIES & SUBCATEGORIES
  // ============================================

  /**
   * Get all categories with their subcategories
   * @returns {Promise<Array>} Array of categories with nested subcategories
   */
  async getCategories() {
    return await this.request('/categories', { method: 'GET' });
  },

  // ============================================
  // SUBMISSIONS
  // ============================================

  /**
   * Submit code for a problem
   * @param {number} problemId - Problem ID
   * @param {string} code - Source code
   * @param {string} language - Programming language (default: 'python')
   * @returns {Promise<Object>} Submission object with PENDING status
   */
  async submitCode(problemId, code, language = 'python') {
    return await this.request('/submissions', {
      method: 'POST',
      body: JSON.stringify({
        problem_id: problemId,
        source_code: code,
        language: language
      })
    });
  },

  /**
   * Get user's submissions
   * @param {Object} filters - Optional filters (problem_id, verdict, limit, offset)
   * @returns {Promise<Array>} Array of submissions
   */
  async getSubmissions(filters = {}) {
    const params = new URLSearchParams();

    if (filters.problem_id) params.append('problem_id', filters.problem_id);
    if (filters.verdict) params.append('verdict', filters.verdict);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);
    if (filters.all) params.append('all', 'true'); // Get all users' submissions

    const queryString = params.toString();
    const url = `/submissions${queryString ? '?' + queryString : ''}`;

    return await this.request(url, { method: 'GET' });
  },

  /**
   * Get single submission details (for polling)
   * @param {number} id - Submission ID
   * @returns {Promise<Object>} Submission with full details including test_results
   */
  async getSubmission(id) {
    return await this.request(`/submissions/${id}`, { method: 'GET' });
  },

  /**
   * Get user's submission statistics
   * @returns {Promise<Object>} Stats object with total, by_verdict, acceptance_rate
   */
  async getSubmissionStats() {
    return await this.request('/submissions/stats', { method: 'GET' });
  },

  /**
   * Get best submission for a problem
   * @param {number} problemId - Problem ID
   * @returns {Promise<Object|null>} Best AC submission or latest attempt, null if no submissions
   */
  async getBestSubmission(problemId) {
    return await this.request(`/submissions/problem/${problemId}/best`, { method: 'GET' });
  },

  // ============================================
  // RANKING
  // ============================================

  /**
   * Get leaderboard/ranking
   * @param {number} limit - Number of entries to return (default: 100, max: 500)
   * @param {number} offset - Number of entries to skip for pagination (default: 0)
   * @returns {Promise<Array>} Array of ranking entries with rank, username, scores, etc.
   */
  async getRanking(limit = 100, offset = 0) {
    const params = new URLSearchParams();

    if (limit) params.append('limit', limit);
    if (offset) params.append('offset', offset);

    const queryString = params.toString();
    const url = `/ranking${queryString ? '?' + queryString : ''}`;

    return await this.request(url, { method: 'GET' });
  },

  /**
   * Get ranking statistics
   * @returns {Promise<Object>} Stats object with total users, score, problems solved, blocks mined
   */
  async getRankingStats() {
    return await this.request('/ranking/stats', { method: 'GET' });
  },

  /**
   * Get global platform statistics (admin only)
   * @returns {Promise<Object>} Stats object with users, problems, submissions, blocks, etc.
   */
  async getStatistics() {
    return await this.request('/admin/statistics', { method: 'GET' });
  },

  // ============================================
  // BLOCKS (Blockchain)
  // ============================================

  /**
   * Get recent blocks
   * @param {number} limit - Number of blocks to return (default: 30, max: 100)
   * @param {number} offset - Number of blocks to skip for pagination (default: 0)
   * @returns {Promise<Array>} Array of blocks with summary information
   */
  async getBlocks(limit = 30, offset = 0) {
    const params = new URLSearchParams();

    if (limit) params.append('limit', limit);
    if (offset) params.append('offset', offset);

    const queryString = params.toString();
    const url = `/blocks${queryString ? '?' + queryString : ''}`;

    return await this.request(url, { method: 'GET' });
  },

  /**
   * Get single block details with all transactions
   * @param {number} id - Block ID
   * @returns {Promise<Object>} Block detail with full information including transactions
   */
  async getBlock(id) {
    return await this.request(`/blocks/id/${id}`, { method: 'GET' });
  },

  /**
   * Get block by height
   * @param {number} height - Block height (e.g., 0 for genesis, 1 for first block)
   * @returns {Promise<Object>} Block detail with full information
   */
  async getBlockByHeight(height) {
    return await this.request(`/blocks/height/${height}`, { method: 'GET' });
  },

  /**
   * Get mempool (unconfirmed transactions)
   * @returns {Promise<Object>} Mempool with pending and unconfirmed submissions
   */
  async getMempool() {
    return await this.request('/blocks/mempool', { method: 'GET' });
  },

  // ============================================
  // ADMIN - USER MANAGEMENT
  // ============================================

  /**
   * Get all users (admin only)
   * @param {Object} filters - Optional filters (limit, offset, role)
   * @returns {Promise<Array>} Array of users
   */
  async getUsers(filters = {}) {
    const params = new URLSearchParams();

    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);
    if (filters.role) params.append('role', filters.role);

    const queryString = params.toString();
    const url = `/users${queryString ? '?' + queryString : ''}`;

    return await this.request(url, { method: 'GET' });
  },

  /**
   * Get user statistics (admin only)
   * @returns {Promise<Object>} User stats with total_users, by_role, total_score, etc.
   */
  async getUserStats() {
    return await this.request('/users/stats', { method: 'GET' });
  },

  /**
   * Get user profile
   * @param {number} userId - User ID
   * @returns {Promise<Object>} User profile
   */
  async getUser(userId) {
    return await this.request(`/users/${userId}`, { method: 'GET' });
  },

  /**
   * Update user role (admin only)
   * @param {number} userId - User ID
   * @param {string} newRole - New role (admin, problemsetter, user)
   * @returns {Promise<Object>} Updated user
   */
  async updateUserRole(userId, newRole) {
    return await this.request(`/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role: newRole })
    });
  },

  /**
   * Reset user password (admin only)
   * @param {number} userId - User ID
   * @param {string} newPassword - New password to set
   * @returns {Promise<Object>} Success message
   */
  async resetUserPassword(userId, newPassword) {
    const payload = { new_password: newPassword };
    console.log('Sending password reset:', { userId, payload });
    return await this.request(`/users/${userId}/reset-password`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
  },

  /**
   * Delete user (admin only)
   * @param {number} userId - User ID
   * @returns {Promise<Object>} Success message
   */
  async deleteUser(userId) {
    return await this.request(`/users/${userId}`, {
      method: 'DELETE'
    });
  },

  /**
   * Update current user's profile
   * @param {Object} profileData - Profile data to update
   * @returns {Promise<Object>} Updated user object
   */
  async updateProfile(profileData) {
    return await this.request('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
  },

  /**
   * Change current user's password
   * @param {string} currentPassword - Current password
   * @param {string} newPassword - New password
   * @returns {Promise<Object>} Success message
   */
  async changePassword(currentPassword, newPassword) {
    return await this.request('/auth/me/password', {
      method: 'PUT',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword
      })
    });
  }
};

// Export for use in other files
window.API = API;
