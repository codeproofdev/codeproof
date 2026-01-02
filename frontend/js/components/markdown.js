/**
 * Markdown Component
 *
 * Renders markdown content to HTML using marked.js
 * Includes syntax highlighting for code blocks using highlight.js
 */

const MarkdownComponent = {
  /**
   * Initialize marked.js configuration
   */
  init() {
    // Check if marked is loaded
    if (typeof marked === 'undefined') {
      console.error('marked.js is not loaded. Include it via CDN in your HTML.');
      return false;
    }

    // Configure marked options
    marked.setOptions({
      breaks: true, // Convert \n to <br>
      gfm: true, // GitHub Flavored Markdown
      headerIds: true,
      mangle: false,
      sanitize: false, // We'll sanitize manually if needed
    });

    // Custom renderer for code blocks with syntax highlighting
    const renderer = new marked.Renderer();

    // Override code block rendering
    renderer.code = (code, language) => {
      // If highlight.js is available, use it
      if (typeof hljs !== 'undefined' && language) {
        try {
          const highlighted = hljs.highlight(code, { language }).value;
          return `<pre><code class="hljs language-${language}">${highlighted}</code></pre>`;
        } catch (e) {
          console.warn('Highlight.js error:', e);
        }
      }

      // Fallback to plain code block
      return `<pre><code class="language-${language || 'plaintext'}">${this.escapeHtml(code)}</code></pre>`;
    };

    // Override inline code rendering
    renderer.codespan = (code) => {
      return `<code class="inline-code">${this.escapeHtml(code)}</code>`;
    };

    marked.setOptions({ renderer });

    return true;
  },

  /**
   * Render markdown string to HTML
   * @param {string} markdownText - The markdown text to render
   * @returns {string} HTML string
   */
  render(markdownText) {
    if (!markdownText) {
      return '';
    }

    try {
      return marked.parse(markdownText);
    } catch (error) {
      console.error('Markdown rendering error:', error);
      return `<p class="error">Error rendering markdown content.</p>`;
    }
  },

  /**
   * Render markdown and insert into a DOM element
   * @param {string} markdownText - The markdown text to render
   * @param {HTMLElement|string} targetElement - Target element or selector
   */
  renderTo(markdownText, targetElement) {
    const element = typeof targetElement === 'string'
      ? document.querySelector(targetElement)
      : targetElement;

    if (!element) {
      console.error('Target element not found:', targetElement);
      return;
    }

    element.innerHTML = this.render(markdownText);

    // Apply syntax highlighting to any code blocks that weren't highlighted during render
    if (typeof hljs !== 'undefined') {
      element.querySelectorAll('pre code:not(.hljs)').forEach((block) => {
        hljs.highlightElement(block);
      });
    }
  },

  /**
   * Escape HTML to prevent XSS
   * @param {string} html - HTML string to escape
   * @returns {string} Escaped HTML
   */
  escapeHtml(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
  },

  /**
   * Create a live preview setup for markdown editing
   * @param {HTMLElement|string} sourceElement - Input element (textarea)
   * @param {HTMLElement|string} previewElement - Preview element
   * @param {number} debounceMs - Debounce delay in milliseconds
   */
  livePreview(sourceElement, previewElement, debounceMs = 300) {
    const source = typeof sourceElement === 'string'
      ? document.querySelector(sourceElement)
      : sourceElement;

    const preview = typeof previewElement === 'string'
      ? document.querySelector(previewElement)
      : previewElement;

    if (!source || !preview) {
      console.error('Source or preview element not found');
      return;
    }

    let timeoutId;

    const updatePreview = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        this.renderTo(source.value, preview);
      }, debounceMs);
    };

    // Initial render
    this.renderTo(source.value, preview);

    // Update on input
    source.addEventListener('input', updatePreview);
  },

  /**
   * Parse problem description with special formatting
   * Handles special blocks like Input/Output format, Examples, etc.
   * @param {string} markdown - Markdown text
   * @returns {string} Rendered HTML
   */
  renderProblemDescription(markdown) {
    if (!markdown) return '';

    // Replace special problem formatting patterns
    let processed = markdown;

    // Highlight input/output format sections
    processed = processed.replace(
      /### Input Format\n([\s\S]*?)(?=###|$)/g,
      '<div class="format-section input-format"><h3>📥 Input Format</h3>$1</div>'
    );

    processed = processed.replace(
      /### Output Format\n([\s\S]*?)(?=###|$)/g,
      '<div class="format-section output-format"><h3>📤 Output Format</h3>$1</div>'
    );

    // Highlight constraints
    processed = processed.replace(
      /### Constraints\n([\s\S]*?)(?=###|$)/g,
      '<div class="format-section constraints"><h3>⚙️ Constraints</h3>$1</div>'
    );

    return this.render(processed);
  }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    MarkdownComponent.init();
  });
} else {
  MarkdownComponent.init();
}

// Export for use in other scripts
window.MarkdownComponent = MarkdownComponent;
