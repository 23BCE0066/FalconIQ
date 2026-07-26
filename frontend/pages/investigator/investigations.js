/* ======================================================
   View 3: Investigations — GET /api/v1/dashboard (sessions)
   ====================================================== */
const InvestigationsView = {
  _page: 1,
  _status: '',
  _query: '',

  async render(root) {
    root.innerHTML = `
      <div class="page-header">
        <div class="page-header-left">
          <div class="page-title">Investigations</div>
          <div class="page-subtitle">Track and manage AML investigations.</div>
        </div>
        <div class="page-header-actions">
          <button class="btn btn-primary" id="inv-new-btn">
            <svg viewBox="0 0 16 16" fill="none"><path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
            New Investigation
          </button>
        </div>
      </div>

      <!-- Stats row -->
      <div class="stat-row" id="inv-stats">
        ${[1,2,3,4,5].map(() => `<div class="skeleton" style="height:80px;border-radius:10px"></div>`).join('')}
      </div>

      <!-- Filter bar -->
      <div class="filter-bar">
        <div class="search-bar" style="flex:1;max-width:320px">
          <svg viewBox="0 0 20 20" fill="none"><circle cx="9" cy="9" r="5.5" stroke="currentColor" stroke-width="1.5"/><path d="M13 13l3.5 3.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          <input id="inv-search" type="text" placeholder="Search investigations…"/>
        </div>
        <select class="input select" style="width:150px" id="inv-status-filter">
          <option value="">All Status</option>
          <option value="COMPLETED">Completed</option>
          <option value="FAILED">Failed</option>
          <option value="RUNNING">Running</option>
        </select>
        <button class="btn btn-secondary" id="inv-filter-btn">Filter</button>
      </div>

      <!-- Table -->
      <div class="card" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>Investigation ID</th>
              <th>Query</th>
              <th>Intent</th>
              <th>Status</th>
              <th>Tools</th>
              <th>Date</th>
              <th>Actions</th>
            </tr></thead>
            <tbody id="inv-tbody">
              ${skeleton(8)}
            </tbody>
          </table>
        </div>
        <div class="pagination" id="inv-pag" style="padding:12px 16px"></div>
      </div>`;

    document.getElementById('inv-new-btn')?.addEventListener('click', () => navigateTo('agent'));

    this._page = 1;
    this._status = '';
    this._query = '';

    await this._loadStats();
    await this._loadTable();

    document.getElementById('inv-filter-btn')?.addEventListener('click', () => this._applyFilters());
    document.getElementById('inv-search')?.addEventListener('keydown', (e) => { if (e.key === 'Enter') this._applyFilters(); });
    document.getElementById('inv-status-filter')?.addEventListener('change', () => this._applyFilters());
  },

  _applyFilters() {
    this._query = document.getElementById('inv-search')?.value.trim() || '';
    this._status = document.getElementById('inv-status-filter')?.value || '';
    this._page = 1;
    this._loadTable();
  },

  async _loadStats() {
    try {
      const stats = await API.get('/investigations/stats');
      document.getElementById('inv-stats').innerHTML = [
        { label: 'Total', value: stats.total, color: '#4f46e5' },
        { label: 'Completed', value: stats.completed, color: '#10b981' },
        { label: 'Failed', value: stats.failed, color: '#ef4444' },
        { label: 'Running', value: stats.running, color: '#f59e0b' },
        { label: 'Avg Time', value: stats.avg_time_ms ? `${stats.avg_time_ms}ms` : '—', color: '#6b7280' },
      ].map(s => `
        <div class="stat-mini">
          <div class="stat-mini-value" style="color:${s.color}">${s.value}</div>
          <div class="stat-mini-label">${s.label}</div>
        </div>`).join('');
    } catch(e) {
      console.error('Failed to load stats', e);
    }
  },

  async _loadTable() {
    const tbody = document.getElementById('inv-tbody');
    tbody.innerHTML = skeleton(8);
    try {
      const params = { page: this._page, page_size: 10 };
      if (this._status) params.status = this._status;
      if (this._query) params.q = this._query;
      
      const data = await API.get('/investigations', params);
      const { items, total } = normalizePage(data);
      
      if (!items.length) {
        tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state"><svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/></svg><p>No investigations found</p></div></td></tr>`;
        document.getElementById('inv-pag').innerHTML = '';
        return;
      }
      tbody.innerHTML = items.map(s => `
        <tr>
          <td><span style="font-family:monospace;font-size:12px;color:#6366f1">${(s.session_id || s.id || '—').slice(0, 20)}</span></td>
          <td style="max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${s.query || ''}">${s.query || '—'}</td>
          <td><span class="tag">${s.intent || '—'}</span></td>
          <td>${statusBadge(s.status)}</td>
          <td>${s.tool_count || '—'}</td>
          <td>${fmt.datetime(s.created_at)}</td>
          <td>
            <button class="btn btn-sm btn-secondary" onclick="window.location.hash='dashboard/agent?session_id=${s.session_id}'">Re-run</button>
          </td>
        </tr>`).join('');
  
      renderPagination(document.getElementById('inv-pag'), total, this._page, 10, (p) => { this._page = p; this._loadTable(); });
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#ef4444;padding:32px">Failed to load: ${e.message}</td></tr>`;
    }
  },
};


// Expose for ES Module Router
window.InvestigationsView = InvestigationsView;
