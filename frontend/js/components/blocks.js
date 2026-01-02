/**
 * CodeProof - Blocks Component
 * Blockchain Explorer UI (Mempool.space style)
 */

const BlocksComponent = {
  /**
   * Determine block activity class based on TX count
   * 🟢 Green: 10+ AC (high-activity)
   * 🟣 Purple: 5-9 AC (medium-activity)
   * 🔵 Blue: 1-4 AC (low-activity)
   * ⚫ Black: 0 AC (empty)
   */
  getActivityClass(txCount) {
    if (txCount >= 10) return 'block-high-activity';
    if (txCount >= 5) return 'block-medium-activity';
    if (txCount >= 1) return 'block-low-activity';
    return 'block-empty';
  },

  /**
   * Format time ago (relative time)
   * e.g., "10 minutos atrás", "2 horas atrás"
   */
  formatTimeAgo(timestamp) {
    const now = new Date();
    const blockTime = new Date(timestamp);
    const diffMs = now - blockTime;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    const lang = window.i18n?.currentLang || 'en';

    if (diffMins < 1) {
      return lang === 'es' ? 'Ahora mismo' : 'Just now';
    } else if (diffMins < 60) {
      return lang === 'es'
        ? `${diffMins} minuto${diffMins > 1 ? 's' : ''} atrás`
        : `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return lang === 'es'
        ? `${diffHours} hora${diffHours > 1 ? 's' : ''} atrás`
        : `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else {
      return lang === 'es'
        ? `${diffDays} día${diffDays > 1 ? 's' : ''} atrás`
        : `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    }
  },

  /**
   * Format points with decimals
   */
  formatPoints(points) {
    return points ? points.toFixed(2) : '0.00';
  },

  /**
   * Get miner icon based on miner name or empty state
   */
  getMinerIcon(isEmpty, minerName) {
    if (isEmpty) return '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline; vertical-align: middle;"><circle cx="12" cy="12" r="10"/><path d="m4.9 4.9 14.2 14.2"/></svg>';

    // Use different icons for variety
    const icons = [
      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline; vertical-align: middle;"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline; vertical-align: middle;"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline; vertical-align: middle;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline; vertical-align: middle;"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>',
      '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline; vertical-align: middle;"><path d="M2.7 10.3a2.41 2.41 0 0 0 0 3.41l7.59 7.59a2.41 2.41 0 0 0 3.41 0l7.59-7.59a2.41 2.41 0 0 0 0-3.41l-7.59-7.59a2.41 2.41 0 0 0-3.41 0Z"/></svg>'
    ];
    const hash = minerName ? minerName.split('').reduce((a, b) => a + b.charCodeAt(0), 0) : 0;
    return icons[hash % icons.length];
  },

  /**
   * Render a single block card
   */
  renderBlock(block, isNextBlock = false) {
    const lang = window.i18n?.currentLang || 'en';
    const activityClass = isNextBlock ? 'block-next' : this.getActivityClass(block.tx_count);
    const timeAgo = isNextBlock ? (lang === 'es' ? 'Próximo' : 'Next') : this.formatTimeAgo(block.timestamp);
    const points = this.formatPoints(block.total_points);
    const minerIcon = this.getMinerIcon(block.is_empty, block.miner_username);

    // Use miner_username or default to "CodeProof"
    const minerName = block.miner_username || 'CodeProof';

    const blockContainer = document.createElement('div');
    blockContainer.className = 'block-container';

    const blockEl = document.createElement('div');
    blockEl.className = `bitcoin-block ${activityClass}`;
    blockEl.dataset.blockId = block.id;
    if (!isNextBlock) {
      blockEl.dataset.blockHeight = block.block_height;
    }

    blockEl.innerHTML = `
      <div class="block-header">
        <div class="block-height">${isNextBlock ? '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline; vertical-align: middle;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' : '#' + block.block_height}</div>
        <div class="block-time">${timeAgo}</div>
      </div>

      <div class="block-body">
        <div class="block-stat-row">
          <span class="block-stat-label">${lang === 'es' ? 'tx' : 'tx'}</span>
          <span class="block-stat-value highlight">${block.tx_count}</span>
        </div>
        <div class="block-stat-row">
          <span class="block-stat-label">${lang === 'es' ? 'puntos' : 'points'}</span>
          <span class="block-stat-value">${points}</span>
        </div>
      </div>
    `;

    blockContainer.appendChild(blockEl);

    // Add miner name below block (not for next block)
    if (!isNextBlock && !block.is_empty) {
      const minerLabel = document.createElement('div');
      minerLabel.className = 'block-miner-label';
      minerLabel.innerHTML = `
        <span class="miner-name" title="${minerName}">${minerName}</span>
      `;
      blockContainer.appendChild(minerLabel);
    } else if (!isNextBlock && block.is_empty) {
      const emptyLabel = document.createElement('div');
      emptyLabel.className = 'block-miner-label empty';
      emptyLabel.textContent = lang === 'es' ? 'Vacío' : 'Empty';
      blockContainer.appendChild(emptyLabel);
    } else if (isNextBlock) {
      // Add placeholder spacer for Next Block to maintain alignment
      const spacer = document.createElement('div');
      spacer.className = 'block-miner-spacer';
      spacer.style.height = '32px'; // Same as miner label height
      spacer.style.visibility = 'hidden';
      blockContainer.appendChild(spacer);
    }

    // Click handler to show block detail (not for next block)
    if (!isNextBlock) {
      blockEl.addEventListener('click', () => {
        this.showBlockDetail(block.id);
      });
    }

    return blockContainer;
  },

  /**
   * Render blocks timeline with Next Block
   */
  async renderTimeline(blocks, containerId, showNextBlock = true) {
    const container = document.getElementById(containerId);
    if (!container) {
      console.error(`Container ${containerId} not found`);
      return;
    }

    // Clear existing blocks
    container.innerHTML = '';

    // Add "Next Block" if enabled
    if (showNextBlock) {
      try {
        // Fetch mempool to get pending submissions
        let allSubmissions = [];
        let mempool = [];

        try {
          // Only fetch submissions if user is authenticated
          const token = localStorage.getItem('token');
          if (typeof API !== 'undefined' && token) {
            allSubmissions = await API.getSubmissions();
            // Filter only AC submissions without block
            mempool = allSubmissions.filter(s => s.verdict === 'AC' && !s.block_id);
          }
        } catch (e) {
          // User may not be authenticated, show empty Next Block
        }

        // Count submissions since last block (< 10 minutes)
        let txCount = 0;
        let totalPoints = 0;

        if (blocks.length > 0) {
          const lastBlockTime = new Date(blocks[0].timestamp);
          const now = new Date();
          const tenMinutesAgo = new Date(now.getTime() - 10 * 60000);

          // Filter submissions after last block
          const recentSubmissions = mempool.filter(sub => {
            const subTime = new Date(sub.submitted_at);
            return subTime > lastBlockTime && subTime > tenMinutesAgo;
          });

          txCount = recentSubmissions.length;
          totalPoints = recentSubmissions.reduce((sum, sub) => sum + (sub.points_earned || 0), 0);
        } else {
          txCount = mempool.length;
          totalPoints = mempool.reduce((sum, sub) => sum + (sub.points_earned || 0), 0);
        }

        const nextBlock = {
          id: 'next',
          block_height: 0,
          timestamp: new Date().toISOString(),
          tx_count: txCount,
          total_points: totalPoints,
          is_empty: txCount === 0
        };

        const nextBlockEl = this.renderBlock(nextBlock, true);
        container.appendChild(nextBlockEl);

        // Add separator line (mempool.space style)
        const separator = document.createElement('div');
        separator.className = 'blocks-separator';
        separator.innerHTML = `
          <div class="separator-line">
            <div class="separator-arrow-up">↑</div>
            <div class="separator-dash"></div>
            <div class="separator-arrow-down">↓</div>
          </div>
        `;
        container.appendChild(separator);
      } catch (error) {
        console.error('Error rendering next block:', error);
      }
    }

    // Render each mined block
    blocks.forEach(block => {
      const blockEl = this.renderBlock(block, false);
      container.appendChild(blockEl);
    });
  },

  /**
   * Show block detail modal
   */
  async showBlockDetail(blockId) {
    try {
      // Fetch block details from API
      const response = await fetch(`/api/blocks/${blockId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch block details');
      }

      const block = await response.json();
      this.renderBlockDetailModal(block);
    } catch (error) {
      console.error('Error fetching block details:', error);
      // Show error notification
      if (window.notifications) {
        window.notifications.show('Error loading block details', 'error');
      }
    }
  },

  /**
   * Render block detail modal
   */
  renderBlockDetailModal(block) {
    const lang = window.i18n?.currentLang || 'en';

    // Create modal if it doesn't exist
    let modal = document.getElementById('block-detail-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'block-detail-modal';
      modal.className = 'modal';
      document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <div class="modal-content">
        <div class="modal-header">
          <h2 class="modal-title">${lang === 'es' ? 'Bloque' : 'Block'} #${block.block_height}</h2>
          <button class="modal-close" id="close-block-modal">&times;</button>
        </div>
        <div class="modal-body">
          <!-- Block Stats Grid -->
          <div class="block-detail-grid">
            <div class="block-detail-stat">
              <div class="block-detail-stat-label">${lang === 'es' ? 'Altura' : 'Height'}</div>
              <div class="block-detail-stat-value">${block.block_height}</div>
            </div>
            <div class="block-detail-stat">
              <div class="block-detail-stat-label">${lang === 'es' ? 'Transacciones' : 'Transactions'}</div>
              <div class="block-detail-stat-value">${block.tx_count}</div>
            </div>
            <div class="block-detail-stat">
              <div class="block-detail-stat-label">${lang === 'es' ? 'Puntos Totales' : 'Total Points'}</div>
              <div class="block-detail-stat-value">${this.formatPoints(block.total_points)}</div>
            </div>
            <div class="block-detail-stat">
              <div class="block-detail-stat-label">${lang === 'es' ? 'Minero' : 'Miner'}</div>
              <div class="block-detail-stat-value">${block.miner_username || (lang === 'es' ? 'Ninguno' : 'None')}</div>
            </div>
            <div class="block-detail-stat">
              <div class="block-detail-stat-label">${lang === 'es' ? 'Tamaño' : 'Size'}</div>
              <div class="block-detail-stat-value">${block.block_size} KB</div>
            </div>
            <div class="block-detail-stat">
              <div class="block-detail-stat-label">${lang === 'es' ? 'Timestamp' : 'Timestamp'}</div>
              <div class="block-detail-stat-value">${new Date(block.timestamp).toLocaleString()}</div>
            </div>
          </div>

          <!-- Block Hashes -->
          <div>
            <h4>${lang === 'es' ? 'Hash del Bloque' : 'Block Hash'}</h4>
            <div class="block-hash-full">
              ${block.block_hash}
              <button class="btn btn-sm copy-hash-btn" data-hash="${block.block_hash}">
                ${lang === 'es' ? 'Copiar' : 'Copy'}
              </button>
            </div>
          </div>

          ${block.prev_block_hash ? `
            <div>
              <h4>${lang === 'es' ? 'Hash Anterior' : 'Previous Hash'}</h4>
              <div class="block-hash-full">${block.prev_block_hash}</div>
            </div>
          ` : ''}

          <!-- Transactions Table -->
          ${block.transactions && block.transactions.length > 0 ? `
            <div class="transactions-section">
              <h3 class="transactions-title">
                ${lang === 'es' ? 'Transacciones' : 'Transactions'} (${block.transactions.length})
              </h3>
              <table class="tx-table">
                <thead>
                  <tr>
                    <th>${lang === 'es' ? 'Hash TX' : 'TX Hash'}</th>
                    <th>${lang === 'es' ? 'Usuario' : 'User'}</th>
                    <th>${lang === 'es' ? 'Problema' : 'Problem'}</th>
                    <th>${lang === 'es' ? 'Puntos' : 'Points'}</th>
                    <th>${lang === 'es' ? 'Tiempo' : 'Time'}</th>
                    <th>${lang === 'es' ? 'Memoria' : 'Memory'}</th>
                  </tr>
                </thead>
                <tbody>
                  ${block.transactions.map(tx => `
                    <tr>
                      <td><span class="tx-hash-short" title="${tx.tx_hash}">${tx.tx_hash.substring(0, 12)}...</span></td>
                      <td>${tx.username}</td>
                      <td><a href="/problems/detail.html?id=${tx.problem_id}">${tx.problem_id} - ${tx.problem_title}</a></td>
                      <td>${this.formatPoints(tx.points_earned)}</td>
                      <td>${tx.execution_time}ms</td>
                      <td>${tx.memory_used}KB</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          ` : `
            <div class="transactions-section">
              <p class="text-muted">${lang === 'es' ? 'No hay transacciones en este bloque' : 'No transactions in this block'}</p>
            </div>
          `}

          <!-- Bitcoin Anchor Info -->
          ${block.btc_block_height ? `
            <div class="btc-anchor">
              <div class="btc-anchor-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline; vertical-align: middle; margin-right: 6px;"><circle cx="12" cy="5" r="3"/><path d="M12 22V8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/></svg>
                ${lang === 'es' ? 'Anclado a Bitcoin Block' : 'Anchored to Bitcoin Block'}
              </div>
              <div class="btc-anchor-info">${lang === 'es' ? 'Altura' : 'Height'}: ${block.btc_block_height}</div>
              <div class="btc-anchor-info">${lang === 'es' ? 'Hash' : 'Hash'}: ${block.btc_block_hash}</div>
              ${block.btc_miner ? `<div class="btc-anchor-info">${lang === 'es' ? 'Minero BTC' : 'BTC Miner'}: ${block.btc_miner}</div>` : ''}
              <a href="https://mempool.space/block/${block.btc_block_hash}" target="_blank" class="btc-anchor-link">
                ${lang === 'es' ? 'Ver en Mempool.space →' : 'View on Mempool.space →'}
              </a>
            </div>
          ` : ''}
        </div>
      </div>
    `;

    // Show modal
    modal.classList.add('active');

    // Close button handler
    document.getElementById('close-block-modal').addEventListener('click', () => {
      modal.classList.remove('active');
    });

    // Copy hash buttons
    modal.querySelectorAll('.copy-hash-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const hash = btn.dataset.hash;
        navigator.clipboard.writeText(hash).then(() => {
          if (window.notifications) {
            window.notifications.show(
              lang === 'es' ? 'Hash copiado' : 'Hash copied',
              'success'
            );
          }
        });
      });
    });

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  },

  /**
   * Load and render recent blocks
   */
  async loadRecentBlocks(limit = 30, containerId = 'blocks-timeline') {
    try {
      const response = await fetch(`/api/blocks?limit=${limit}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch blocks');
      }

      const data = await response.json();
      this.renderTimeline(data.blocks, containerId);
    } catch (error) {
      console.error('Error loading blocks:', error);
      // Show error notification
      if (window.notifications) {
        window.notifications.show('Error loading blocks', 'error');
      }
    }
  },

  /**
   * Initialize blocks component
   */
  init(containerId = 'blocks-timeline', limit = 30) {
    this.loadRecentBlocks(limit, containerId);

    // Auto-refresh every 60 seconds
    setInterval(() => {
      this.loadRecentBlocks(limit, containerId);
    }, 60000);
  }
};

// Export for use in other modules
if (typeof window !== 'undefined') {
  window.BlocksComponent = BlocksComponent;
}
