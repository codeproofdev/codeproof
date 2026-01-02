/**
 * Problemsetter Dashboard - JavaScript Functions
 * Handles problem creation, package upload, and category management
 */

// Global state
let allCategories = [];
let allUsers = []; // For @ autocomplete
window.selectedCategories = window.selectedCategories || [];
window.selectedSubcategories = window.selectedSubcategories || [];
window.authors = window.authors || [];

/**
 * Load users from API (for @ autocomplete)
 */
async function loadUsers() {
  try {
    // Get users from ranking endpoint
    const ranking = await API.request('/ranking?limit=100');
    allUsers = ranking.map(user => user.username).sort();
  } catch (error) {
    console.error('Error loading users:', error);
    allUsers = [];
  }
}

/**
 * Load categories from API
 */
async function loadCategories() {
  try {
    allCategories = await API.getCategories();
    renderCategories();
  } catch (error) {
    console.error('Error loading categories:', error);
    Notifications.show('Failed to load categories', 'error');
  }
}

/**
 * Render category checkboxes
 */
function renderCategories() {
  const container = document.getElementById('categories-container');

  if (allCategories.length === 0) {
    container.innerHTML = '<div class="text-center text-muted py-md">No categories available</div>';
    return;
  }

  container.innerHTML = allCategories.map(cat => `
    <label class="checkbox-label" style="display: flex; align-items: center; padding: var(--spacing-sm); cursor: pointer;">
      <input
        type="checkbox"
        class="category-checkbox"
        value="${cat.code}"
        ${window.selectedCategories.includes(cat.code) ? 'checked' : ''}
        onchange="handleCategoryChange(this)"
        style="margin-right: var(--spacing-sm);">
      <span style="font-size: 0.9rem;">${cat.name_en}</span>
    </label>
  `).join('');
}

/**
 * Handle category checkbox change
 */
function handleCategoryChange(checkbox) {
  const categoryCode = checkbox.value;

  if (checkbox.checked) {
    window.selectedCategories.push(categoryCode);
  } else {
    window.selectedCategories = window.selectedCategories.filter(c => c !== categoryCode);
    // Remove subcategories from this category
    const category = allCategories.find(c => c.code === categoryCode);
    if (category) {
      const subcatCodes = category.subcategories.map(s => s.code);
      window.selectedSubcategories = window.selectedSubcategories.filter(s => !subcatCodes.includes(s));
    }
  }

  renderSubcategories();
}

/**
 * Render subcategories based on selected categories
 */
function renderSubcategories() {
  const container = document.getElementById('subcategories-container');

  if (window.selectedCategories.length === 0) {
    container.innerHTML = '<div class="text-center text-muted py-md">Select categories first</div>';
    return;
  }

  // Get all subcategories from selected categories
  const availableSubcategories = [];
  window.selectedCategories.forEach(catCode => {
    const category = allCategories.find(c => c.code === catCode);
    if (category && category.subcategories) {
      category.subcategories.forEach(subcat => {
        availableSubcategories.push({
          ...subcat,
          categoryName: category.name_en
        });
      });
    }
  });

  if (availableSubcategories.length === 0) {
    container.innerHTML = '<div class="text-center text-muted py-md">No subcategories available</div>';
    return;
  }

  container.innerHTML = availableSubcategories.map(subcat => `
    <label class="checkbox-label" style="display: flex; align-items: start; padding: var(--spacing-xs); cursor: pointer;" title="${subcat.categoryName}">
      <input
        type="checkbox"
        class="subcategory-checkbox"
        value="${subcat.code}"
        ${window.selectedSubcategories.includes(subcat.code) ? 'checked' : ''}
        onchange="handleSubcategoryChange(this)"
        style="margin-right: var(--spacing-xs); margin-top: 2px;">
      <span style="font-size: 0.85rem; line-height: 1.3;">
        ${subcat.name_en}
        <br><small style="color: var(--color-text-muted);">${subcat.categoryName}</small>
      </span>
    </label>
  `).join('');
}

/**
 * Handle subcategory checkbox change
 */
function handleSubcategoryChange(checkbox) {
  const subcategoryCode = checkbox.value;

  if (checkbox.checked) {
    if (!window.selectedSubcategories.includes(subcategoryCode)) {
      window.selectedSubcategories.push(subcategoryCode);
    }
  } else {
    window.selectedSubcategories = window.selectedSubcategories.filter(s => s !== subcategoryCode);
  }
}

/**
 * Add author to the list
 */
function addAuthor() {
  const input = document.getElementById('author-input');
  const name = input.value.trim();

  if (!name) {
    return;
  }

  if (window.authors.includes(name)) {
    Notifications.show('Author already added', 'warning');
    return;
  }

  window.authors.push(name);
  renderAuthors();
  input.value = '';
}

/**
 * Remove author from the list
 */
function removeAuthor(name) {
  window.authors = window.authors.filter(a => a !== name);
  renderAuthors();
}

/**
 * Render author tags
 */
function renderAuthors() {
  const container = document.getElementById('authors-container');

  if (window.authors.length === 0) {
    container.innerHTML = '<div class="text-sm text-muted">No authors added yet</div>';
    return;
  }

  container.innerHTML = window.authors.map(author => `
    <span class="tag" style="display: inline-flex; align-items: center; gap: var(--spacing-xs); padding: var(--spacing-xs) var(--spacing-sm); background: var(--color-bg-secondary); border-radius: var(--radius-sm); margin-right: var(--spacing-xs); margin-bottom: var(--spacing-xs);">
      ${author}
      <button type="button" onclick="removeAuthor('${author.replace(/'/g, "\\'")})')" class="tag-remove" style="background: none; border: none; color: var(--color-text-muted); cursor: pointer; padding: 0; font-size: 1.2rem; line-height: 1;">&times;</button>
    </span>
  `).join('');
}

/**
 * Setup autocomplete for @ mentions in author input
 */
function setupAuthorAutocomplete() {
  const input = document.getElementById('author-input');
  let autocompleteDiv = null;
  let selectedIndex = -1;

  // Create autocomplete dropdown
  function createAutocompleteDropdown() {
    if (autocompleteDiv) return autocompleteDiv;

    autocompleteDiv = document.createElement('div');
    autocompleteDiv.id = 'author-autocomplete';
    autocompleteDiv.style.cssText = `
      position: absolute;
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-sm);
      max-height: 200px;
      overflow-y: auto;
      z-index: 1000;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
      display: none;
    `;
    input.parentElement.style.position = 'relative';
    input.parentElement.appendChild(autocompleteDiv);
    return autocompleteDiv;
  }

  // Show suggestions
  function showSuggestions(query) {
    const dropdown = createAutocompleteDropdown();

    // Filter users based on query (after @)
    const filtered = allUsers.filter(username =>
      username.toLowerCase().startsWith(query.toLowerCase())
    ).slice(0, 10); // Limit to 10 suggestions

    if (filtered.length === 0) {
      dropdown.style.display = 'none';
      return;
    }

    selectedIndex = -1;
    dropdown.innerHTML = filtered.map((username, index) => `
      <div class="autocomplete-item" data-index="${index}" data-username="${username}" style="
        padding: 8px 12px;
        cursor: pointer;
        color: var(--text-primary);
        font-size: 0.9rem;
        border-bottom: 1px solid var(--border-color);
        transition: background 0.2s;
      ">
        <span style="color: var(--accent-orange);">@</span>${username}
      </div>
    `).join('');

    // Position dropdown
    const rect = input.getBoundingClientRect();
    dropdown.style.width = `${input.offsetWidth}px`;
    dropdown.style.top = `${input.offsetHeight}px`;
    dropdown.style.left = '0';
    dropdown.style.display = 'block';

    // Add click handlers
    dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
      item.addEventListener('click', () => {
        selectUser(item.dataset.username);
      });
      item.addEventListener('mouseenter', () => {
        dropdown.querySelectorAll('.autocomplete-item').forEach(i => i.style.background = '');
        item.style.background = 'var(--bg-tertiary)';
      });
    });
  }

  // Hide suggestions
  function hideSuggestions() {
    if (autocompleteDiv) {
      autocompleteDiv.style.display = 'none';
    }
    selectedIndex = -1;
  }

  // Select a user from dropdown
  function selectUser(username) {
    input.value = '@' + username;
    hideSuggestions();
    input.focus();
  }

  // Handle keyboard navigation
  function navigateDropdown(direction) {
    if (!autocompleteDiv || autocompleteDiv.style.display === 'none') return;

    const items = autocompleteDiv.querySelectorAll('.autocomplete-item');
    if (items.length === 0) return;

    // Clear previous selection
    items.forEach(item => item.style.background = '');

    // Update index
    if (direction === 'down') {
      selectedIndex = (selectedIndex + 1) % items.length;
    } else if (direction === 'up') {
      selectedIndex = selectedIndex <= 0 ? items.length - 1 : selectedIndex - 1;
    }

    // Highlight selected
    items[selectedIndex].style.background = 'var(--bg-tertiary)';
    items[selectedIndex].scrollIntoView({ block: 'nearest' });
  }

  // Select highlighted item
  function selectHighlighted() {
    if (!autocompleteDiv || autocompleteDiv.style.display === 'none') return false;

    const items = autocompleteDiv.querySelectorAll('.autocomplete-item');
    if (selectedIndex >= 0 && selectedIndex < items.length) {
      selectUser(items[selectedIndex].dataset.username);
      return true;
    }
    return false;
  }

  // Input event listener
  input.addEventListener('input', (e) => {
    const value = input.value;

    if (value.startsWith('@') && value.length > 1) {
      const query = value.substring(1); // Remove @
      showSuggestions(query);
    } else {
      hideSuggestions();
    }
  });

  // Keyboard navigation
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      navigateDropdown('down');
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      navigateDropdown('up');
    } else if (e.key === 'Enter') {
      if (autocompleteDiv && autocompleteDiv.style.display !== 'none') {
        if (selectHighlighted()) {
          e.preventDefault();
        }
      }
    } else if (e.key === 'Escape') {
      hideSuggestions();
    }
  });

  // Hide on blur (with delay to allow clicks)
  input.addEventListener('blur', () => {
    setTimeout(() => hideSuggestions(), 200);
  });
}

/**
 * Handle upload package form submission
 */
async function handlePackageUpload(e) {
  e.preventDefault();

  const fileInput = document.getElementById('package-file');
  const file = fileInput.files[0];

  if (!file) {
    Notifications.show('Please select a file', 'error');
    return;
  }

  // Show progress
  const progressDiv = document.getElementById('upload-progress');
  const resultDiv = document.getElementById('upload-result');
  progressDiv.style.display = 'block';
  resultDiv.style.display = 'none';

  try {
    const result = await API.uploadProblemPackage(file);

    // Hide progress
    progressDiv.style.display = 'none';

    // Show success message
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = `
      <div class="alert alert-success">
        <h3 class="font-semibold mb-sm">Package uploaded successfully!</h3>
        <p><strong>Problem:</strong> ${result.title_en} (ID: ${result.id})</p>
        <p><strong>Status:</strong> ${result.status}</p>
        <p class="text-sm mt-sm">The problem has been submitted for review.</p>
      </div>
    `;

    Notifications.show('Problem package uploaded successfully!', 'success');

    // Reset form
    fileInput.value = '';

    // Reload my problems
    await loadMyProblems();

  } catch (error) {
    // Hide progress
    progressDiv.style.display = 'none';

    // Show error
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = `
      <div class="alert alert-error">
        <h3 class="font-semibold mb-sm">Upload failed</h3>
        <p>${error.message}</p>
      </div>
    `;

    Notifications.show(error.message, 'error');
  }
}

/**
 * Export problem as ZIP
 */
async function exportProblem(problemId, problemTitle) {
  try {
    Notifications.show('Preparing download...', 'info');

    const blob = await API.exportProblem(problemId);

    // Create download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${problemTitle.replace(/[^a-z0-9]/gi, '-').toLowerCase()}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    Notifications.show('Download started', 'success');

  } catch (error) {
    Notifications.show('Export failed: ' + error.message, 'error');
  }
}

/**
 * View problem package info
 */
async function viewPackageInfo(problemId) {
  try {
    const info = await API.getProblemPackageInfo(problemId);

    // Show modal or alert with package info
    const sizeInMB = (info.size_bytes / (1024 * 1024)).toFixed(2);

    alert(`Package Information:

Code: ${info.code}
Size: ${sizeInMB} MB (${info.size_bytes} bytes)
Files: ${info.file_count}
Test Cases: ${info.test_case_count} (${info.sample_count} samples, ${info.hidden_count} hidden)
Has Descriptions: ${info.has_descriptions ? 'Yes' : 'No'}
Created: ${new Date(info.created_at).toLocaleDateString()}
Updated: ${new Date(info.updated_at).toLocaleDateString()}`);

  } catch (error) {
    Notifications.show('Failed to load package info: ' + error.message, 'error');
  }
}

// Make functions globally available
window.loadUsers = loadUsers;
window.loadCategories = loadCategories;
window.setupAuthorAutocomplete = setupAuthorAutocomplete;
window.handleCategoryChange = handleCategoryChange;
window.handleSubcategoryChange = handleSubcategoryChange;
window.addAuthor = addAuthor;
window.removeAuthor = removeAuthor;
window.handlePackageUpload = handlePackageUpload;
window.exportProblem = exportProblem;
window.viewPackageInfo = viewPackageInfo;
window.selectedCategories = selectedCategories;
window.selectedSubcategories = selectedSubcategories;
window.authors = authors;
