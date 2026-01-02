/**
 * Monaco Editor Component
 *
 * Wrapper for Monaco Editor with auto-save, theming, and problem-specific features
 */

const EditorComponent = {
  editor: null,
  currentProblemId: null,
  initialCode: '',
  autoSaveEnabled: true,
  autoSaveDelay: 1000, // ms

  /**
   * Initialize Monaco Editor
   * @param {HTMLElement|string} container - Container element or selector
   * @param {Object} options - Configuration options
   * @returns {Object} Monaco editor instance
   */
  async init(container, options = {}) {
    console.log('[EditorComponent] init() called with container:', container);

    // Get element - handle both ID strings and selectors
    let element;
    if (typeof container === 'string') {
      // Try as selector first (supports #id, .class, etc.)
      element = document.querySelector(container);

      // If not found and doesn't start with # or ., try as ID
      if (!element && !container.startsWith('#') && !container.startsWith('.')) {
        console.log('[EditorComponent] Trying as ID:', container);
        element = document.getElementById(container);
      }
    } else {
      element = container;
    }

    if (!element) {
      console.error('[EditorComponent] ERROR: Container not found:', container);
      console.error('[EditorComponent] Tried querySelector and getElementById');
      return null;
    }

    console.log('[EditorComponent] Container element found:', element);
    console.log('[EditorComponent] Container dimensions:', element.offsetWidth, 'x', element.offsetHeight);

    // Check if Monaco is loaded
    if (typeof monaco === 'undefined') {
      console.error('[EditorComponent] ERROR: Monaco is not defined!');
      console.error('[EditorComponent] Make sure Monaco Editor is loaded before calling init()');
      return null;
    }

    console.log('[EditorComponent] Monaco is loaded:', monaco);

    // Default options
    const defaultOptions = {
      value: options.value || '',
      language: options.language || 'python',
      theme: options.theme || this.getSavedTheme(),
      automaticLayout: true,
      minimap: { enabled: true },
      fontSize: 14,
      lineNumbers: 'on',
      roundedSelection: true,
      scrollBeyondLastLine: false,
      readOnly: false,
      cursorStyle: 'line',
      wordWrap: 'off',
      tabSize: 4,
      insertSpaces: true,
      renderWhitespace: 'selection',
      scrollbar: {
        vertical: 'visible',
        horizontal: 'visible',
        useShadows: false,
        verticalScrollbarSize: 10,
        horizontalScrollbarSize: 10
      }
    };

    // Merge options
    const editorOptions = { ...defaultOptions, ...options };

    console.log('[EditorComponent] Editor options:', editorOptions);

    // Create editor
    try {
      console.log('[EditorComponent] Calling monaco.editor.create()...');
      this.editor = monaco.editor.create(element, editorOptions);
      console.log('[EditorComponent] Editor created successfully:', this.editor);
    } catch (error) {
      console.error('[EditorComponent] FATAL: Failed to create editor:', error);
      throw error;
    }

    // Store initial code
    this.initialCode = editorOptions.value;

    // Setup auto-save
    if (this.autoSaveEnabled && this.currentProblemId) {
      this.setupAutoSave();
    }

    // Setup resize observer
    this.setupAutoResize(element);

    return this.editor;
  },

  /**
   * Setup auto-save functionality
   */
  setupAutoSave() {
    if (!this.editor) return;

    let timeoutId;

    this.editor.onDidChangeModelContent(() => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        this.saveCode();
      }, this.autoSaveDelay);
    });
  },

  /**
   * Setup auto-resize observer
   * @param {HTMLElement} container - Editor container
   */
  setupAutoResize(container) {
    if (!this.editor) return;

    // Use ResizeObserver if available
    if (typeof ResizeObserver !== 'undefined') {
      const resizeObserver = new ResizeObserver(() => {
        this.editor.layout();
      });
      resizeObserver.observe(container);
    } else {
      // Fallback to window resize
      window.addEventListener('resize', () => {
        this.editor.layout();
      });
    }
  },

  /**
   * Get current code from editor
   * @returns {string} Current code
   */
  getCode() {
    return this.editor ? this.editor.getValue() : '';
  },

  /**
   * Set code in editor
   * @param {string} code - Code to set
   */
  setCode(code) {
    if (this.editor) {
      this.editor.setValue(code);
    }
  },

  /**
   * Reset editor to initial code
   */
  reset() {
    this.setCode(this.initialCode);
    Notifications.info(i18n.t('editor.resetSuccess') || 'Code reset to initial template');
  },

  /**
   * Change editor theme
   * @param {string} theme - Theme name ('vs', 'vs-dark', 'hc-black')
   */
  setTheme(theme) {
    if (this.editor) {
      monaco.editor.setTheme(theme);
      this.saveTheme(theme);
    }
  },

  /**
   * Toggle between light and dark theme
   */
  toggleTheme() {
    const currentTheme = this.getSavedTheme();
    const newTheme = currentTheme === 'vs-dark' ? 'vs' : 'vs-dark';
    this.setTheme(newTheme);
    return newTheme;
  },

  /**
   * Change editor language
   * @param {string} language - Language name ('python', 'javascript', 'rust', etc.)
   */
  setLanguage(language) {
    if (this.editor) {
      const model = this.editor.getModel();
      if (model) {
        monaco.editor.setModelLanguage(model, language);
      }
    }
  },

  /**
   * Save code to localStorage
   */
  saveCode() {
    if (!this.currentProblemId) return;

    const code = this.getCode();
    const key = `codeproof_code_${this.currentProblemId}`;
    localStorage.setItem(key, code);
  },

  /**
   * Load saved code from localStorage
   * @param {number} problemId - Problem ID
   * @returns {string|null} Saved code or null
   */
  loadSavedCode(problemId) {
    const key = `codeproof_code_${problemId}`;
    return localStorage.getItem(key);
  },

  /**
   * Clear saved code for a problem
   * @param {number} problemId - Problem ID
   */
  clearSavedCode(problemId) {
    const key = `codeproof_code_${problemId}`;
    localStorage.removeItem(key);
  },

  /**
   * Save theme preference to localStorage
   * @param {string} theme - Theme name
   */
  saveTheme(theme) {
    localStorage.setItem('codeproof_editor_theme', theme);
  },

  /**
   * Get saved theme from localStorage
   * @returns {string} Theme name (default: 'vs-dark')
   */
  getSavedTheme() {
    return localStorage.getItem('codeproof_editor_theme') || 'vs-dark';
  },

  /**
   * Initialize editor for a specific problem
   * @param {string} containerId - Container element ID
   * @param {number} problemId - Problem ID
   * @param {string} initialCode - Initial code template
   * @param {string} language - Programming language
   * @returns {Object} Monaco editor instance
   */
  async initForProblem(containerId, problemId, initialCode, language = 'python') {
    this.currentProblemId = problemId;
    this.initialCode = initialCode;

    // Check if there's saved code
    const savedCode = this.loadSavedCode(problemId);
    const codeToUse = savedCode || initialCode;

    // Initialize editor
    const editor = await this.init(containerId, {
      value: codeToUse,
      language: language
    });

    return editor;
  },

  /**
   * Dispose editor instance
   */
  dispose() {
    if (this.editor) {
      this.editor.dispose();
      this.editor = null;
    }
  },

  /**
   * Focus the editor
   */
  focus() {
    if (this.editor) {
      this.editor.focus();
    }
  },

  /**
   * Get editor instance
   * @returns {Object|null} Monaco editor instance
   */
  getInstance() {
    return this.editor;
  },

  /**
   * Set editor read-only mode
   * @param {boolean} readOnly - Whether editor should be read-only
   */
  setReadOnly(readOnly) {
    if (this.editor) {
      this.editor.updateOptions({ readOnly });
    }
  },

  /**
   * Insert text at cursor position
   * @param {string} text - Text to insert
   */
  insertText(text) {
    if (!this.editor) return;

    const selection = this.editor.getSelection();
    const id = { major: 1, minor: 1 };
    const op = {
      identifier: id,
      range: selection,
      text: text,
      forceMoveMarkers: true
    };
    this.editor.executeEdits('insert-text', [op]);
  },

  /**
   * Format document
   */
  async formatDocument() {
    if (this.editor) {
      await this.editor.getAction('editor.action.formatDocument').run();
    }
  }
};

// Export for use in other scripts
window.EditorComponent = EditorComponent;
