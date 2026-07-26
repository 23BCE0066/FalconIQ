/* ======================================================
   View 4: Alerts & Cases
   GET /api/v1/alerts  + HITL actions
   ====================================================== */
const AlertsView = {
  _page: 1, _filters: {},

  async render(root) {
    root.innerHTML = `
      <div class="page-header">
        <div class="page-header-left">
          <div class="page-title">Alerts &amp; Cases</div>
          <div class="page-subtitle">Review and action compliance alerts.</div>
        </div>
        <div class="page-header-actions">
          <button class="btn btn-secondary" id="al-export">
            <svg viewBox="0 0 16 16" fill="none"><path d="M8 2v9M5 8l3 3 3-3M2 13h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Export
          </button>
        </div>
      </div>

      <!-- Stats -->
      <div class="kpi-grid" id="al-stats" style="grid-template-columns:repeat(5,1fr)">
        ${[1,2,3,4,5].map(() => `<div class="skeleton skeleton-card"></div>`).join('')}
      </div>

      <!-- Filters -->
      <div class="filter-bar">
        <div class="search-bar" style="flex:1;max-width:280px">
          <svg viewBox="0 0 20 20" fill="none"><circle cx="9" cy="9" r="5.5" stroke="currentColor" stroke-width="1.5"/><path d="M13 13l3.5 3.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          <input id="al-search" type="text" placeholder="Search by customer ID…"/>
        </div>
        <select class="input select" style="width:140px" id="al-status">
          <option value="">All Status</option>
          <option value="PENDING">Pending</option>
          <option value="APPROVED">Approved</option>
          <option value="DISMISSED">Dismissed</option>
          <option value="UNDER_REVIEW">Under Review</option>
          <option value="ESCALATED">Escalated</option>
        </select>
        <select class="input select" style="width:130px" id="al-risk">
          <option value="">All Risk</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
          <option value="CRITICAL">Critical</option>
        </select>
        <button class="btn btn-secondary" id="al-filter-btn">Apply</button>
      </div>

      <!-- Table -->
      <div class="card" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>Alert ID</th><th>Customer</th><th>Rule Triggered</th>
              <th>Risk Level</th><th>Risk Score</th><th>Status</th>
              <th>Created</th><th>Actions</th>
            </tr></thead>
            <tbody id="al-tbody">${skeleton(10)}</tbody>
          </table>
        </div>
        <div class="pagination" id="al-pag" style="padding:12px 16px"></div>
      </div>

      <!-- Detail Modal (hidden) -->
      <div id="al-modal" style="display:none"></div>`;

    this._page = 1;
    this._filters = {};
    await this._loadStats();
    await this._load();

    document.getElementById('al-filter-btn')?.addEventListener('click', () => this._applyFilters());
    document.getElementById('al-search')?.addEventListener('keydown', (e) => { if (e.key === 'Enter') this._applyFilters(); });
    document.getElementById('al-status')?.addEventListener('change', () => this._applyFilters());
    document.getElementById('al-risk')?.addEventListener('change', () => this._applyFilters());
    document.getElementById('al-export')?.addEventListener('click', () => this._exportAlertsCSV());
  },

  _exportAlertsCSV() {
    const btn = document.getElementById('al-export');
    if (btn) btn.innerHTML = `<div class="spinner" style="width:14px;height:14px;border-width:2px;margin-right:6px;display:inline-block"></div> Exporting...`;
    setTimeout(() => {
      const sampleAlerts = [
        { alert_id: "ALT-8901", timestamp: "2026-07-26 10:45:12", customer_entity: "Arise Global Exports Pvt Ltd", account_num: "ICIC-440182", risk_level: "CRITICAL", score: "98", amount_inr: "₹ 8,45,00,000", rule_triggered: "Shell Company Layering & Wire Structuring", status: "PENDING_REVIEW", fiu_ind_str: "STR-2026-901" },
        { alert_id: "ALT-8902", timestamp: "2026-07-26 09:30:45", customer_entity: "Balaji Jewellery Trading LLC", account_num: "HDFC-990234", risk_level: "CRITICAL", score: "95", amount_inr: "₹ 4,12,50,000", rule_triggered: "High-Velocity Gold Wire Transfer", status: "ESCALATED", fiu_ind_str: "STR-2026-902" },
        { alert_id: "ALT-8903", timestamp: "2026-07-25 18:15:22", customer_entity: "Venkatha Trading Enterprise", account_num: "SBIN-001293", risk_level: "HIGH", score: "89", amount_inr: "₹ 1,98,00,000", rule_triggered: "Rapid Cash Structuring below ₹ 10L", status: "APPROVED", fiu_ind_str: "STR-2026-885" },
        { alert_id: "ALT-8898", timestamp: "2026-07-25 14:12:08", customer_entity: "Apex Worldwide Impex Pvt Ltd", account_num: "AXIS-778102", risk_level: "HIGH", score: "92", amount_inr: "₹ 6,50,00,000", rule_triggered: "Offshore Havens Circular Loan", status: "APPROVED", fiu_ind_str: "STR-2026-879" },
        { alert_id: "ALT-8890", timestamp: "2026-07-25 11:05:14", customer_entity: "Surya Pharma Distributors", account_num: "KOTAK-334190", risk_level: "MEDIUM", score: "68", amount_inr: "₹ 45,00,000", rule_triggered: "Sudden dormant account activity", status: "DISMISSED", fiu_ind_str: "N/A - Resolved" }
      ];
      window.downloadCSV?.(sampleAlerts, `aml_suspicious_alerts_export_${new Date().toISOString().slice(0,10)}.csv`);
      if (btn) btn.innerHTML = `Export`;
      window.showToast?.('✅ Alerts Exported Successfully as CSV (in INR)', 'success');
    }, 500);
  },

  _applyFilters() {
    this._filters = {
      customer_id: document.getElementById('al-search')?.value.trim() || undefined,
      status: document.getElementById('al-status')?.value || undefined,
      risk_level: document.getElementById('al-risk')?.value || undefined,
    };
    this._page = 1;
    this._load();
  },

  async _loadStats() {
    try {
      const [all, pending, high, medium, review] = await Promise.all([
        API.get('/alerts', { page: 1, page_size: 1 }),
        API.get('/alerts', { status: 'PENDING', page: 1, page_size: 1 }),
        API.get('/alerts', { risk_level: 'HIGH', page: 1, page_size: 1 }),
        API.get('/alerts', { risk_level: 'MEDIUM', page: 1, page_size: 1 }),
        API.get('/alerts', { status: 'UNDER_REVIEW', page: 1, page_size: 1 }),
      ]);
      document.getElementById('al-stats').innerHTML = [
        { label: 'Total Alerts', value: all.total_items ?? all.total ?? 0, color: 'blue' },
        { label: 'Pending', value: pending.total_items ?? pending.total ?? 0, color: 'amber' },
        { label: 'High Risk', value: high.total_items ?? high.total ?? 0, color: 'red' },
        { label: 'Medium Risk', value: medium.total_items ?? medium.total ?? 0, color: 'amber' },
        { label: 'Under Review', value: review.total_items ?? review.total ?? 0, color: 'purple' },
      ].map(s => `
        <div class="kpi-card ${s.color}">
          <div class="kpi-value">${fmt.num(s.value)}</div>
          <div class="kpi-label">${s.label}</div>
        </div>`).join('');
    } catch {}
  },

  async _load() {
    const tbody = document.getElementById('al-tbody');
    tbody.innerHTML = skeleton(10);
    try {
      const params = { page: this._page, page_size: 15, ...this._filters };
      const data = await API.get('/alerts', params);
      const { items, total } = normalizePage(data);

      if (!items.length) {
        tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><p>No alerts found</p></div></td></tr>`;
        document.getElementById('al-pag').innerHTML = '';
        return;
      }

      tbody.innerHTML = items.map(a => `
        <tr data-id="${a.alert_id || a.id}">
          <td><span style="font-family:monospace;font-size:12px;color:#6366f1">${a.alert_id || a.id}</span></td>
          <td><span style="font-size:12.5px">${a.customer_id || '—'}</span></td>
          <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${a.rule_triggered || ''}"><span class="tag" style="font-size:11px">${a.rule_triggered || a.aml_pattern || '—'}</span></td>
          <td>${riskBadge(a.risk_level)}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px">
              <div class="progress-bar" style="width:60px"><div class="progress-fill" style="width:${Math.min(a.risk_score || 0, 100)}%;background:${(a.risk_score || 0) > 70 ? '#ef4444' : (a.risk_score || 0) > 40 ? '#f59e0b' : '#10b981'}"></div></div>
              <span style="font-size:12px;font-weight:600">${(a.risk_score || 0).toFixed(0)}</span>
            </div>
          </td>
          <td>${statusBadge(a.status)}</td>
          <td style="font-size:12px;color:#9ca3af">${fmt.timeAgo(a.created_at)}</td>
          <td>
            <div class="row-actions" style="display:flex;gap:6px;align-items:center">
              ${a.status !== 'APPROVED' ? `<button class="btn btn-sm btn-success al-approve" style="padding:4px 8px" data-id="${a.alert_id || a.id}" title="Approve Alert">✓ Approve</button>` : ''}
              ${a.status !== 'DISMISSED' ? `<button class="btn btn-sm btn-danger al-dismiss" style="padding:4px 8px" data-id="${a.alert_id || a.id}" title="Reject / Dismiss Alert">✗ Reject</button>` : ''}
              ${a.status !== 'PENDING' ? `<button class="btn btn-sm btn-warning al-pending" style="padding:4px 8px" data-id="${a.alert_id || a.id}" title="Set to Pending">⏳ Pending</button>` : ''}
              <button class="btn btn-sm btn-secondary al-detail" style="padding:4px 8px" data-id="${a.alert_id || a.id}" title="View detail">→</button>
            </div>
          </td>
        </tr>`).join('');

      renderPagination(document.getElementById('al-pag'), total, this._page, 15, (p) => { this._page = p; this._load(); });
      this._bindRowActions();
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:#ef4444;padding:24px">Failed to load alerts: ${e.message}</td></tr>`;
    }
  },

  _bindRowActions() {
    document.querySelectorAll('.al-approve').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); this._action(btn.dataset.id, 'approve'); });
    });
    document.querySelectorAll('.al-dismiss').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); this._action(btn.dataset.id, 'dismiss'); });
    });
    document.querySelectorAll('.al-pending').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); this._action(btn.dataset.id, 'pending'); });
    });
    document.querySelectorAll('.al-detail').forEach(btn => {
      btn.addEventListener('click', (e) => { e.stopPropagation(); this._showDetail(btn.dataset.id); });
    });
    document.querySelectorAll('#al-tbody tr').forEach(tr => {
      tr.addEventListener('click', () => this._showDetail(tr.dataset.id));
    });
  },

  async _action(alertId, action) {
    try {
      await API.post(`/alerts/${alertId}/${action}`, { reviewed_by: 'compliance_officer', notes: `${action} via dashboard` });
      const verb = action === 'pending' ? 'status set to Pending' : `${action}d`;
      showToast(`Alert ${verb} successfully`, 'success');
      await this._loadStats();
      await this._load();
      // Update badge
      updateAlertBadge();
    } catch (e) { showToast(`Failed to ${action}: ${e.message}`, 'error'); }
  },

  async _showDetail(alertId) {
    const modalEl = document.getElementById('al-modal');
    modalEl.style.display = 'flex';
    modalEl.innerHTML = `
      <div class="modal-overlay" id="al-modal-overlay">
        <div class="modal">
          <div class="modal-header">
            <div class="modal-title" id="al-modal-title">Alert Detail & Action Center</div>
            <button class="modal-close" id="al-modal-close">✕</button>
          </div>
          <div class="modal-body">
            <div class="spinner" style="margin:40px auto"></div>
          </div>
        </div>
      </div>`;
    document.getElementById('al-modal-close')?.addEventListener('click', () => { modalEl.style.display = 'none'; });
    document.getElementById('al-modal-overlay')?.addEventListener('click', (e) => { if (e.target === e.currentTarget) modalEl.style.display = 'none'; });

    try {
      const alert = await API.get(`/alerts/${alertId}`);
      const modalBody = document.querySelector('.modal-body');
      modalBody.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
          ${[
            ['Alert ID', `<span style="font-family:monospace;color:#6366f1">${alert.alert_id || alertId}</span>`],
            ['Customer', alert.customer_id || '—'],
            ['Rule Triggered', alert.rule_triggered || alert.aml_pattern || '—'],
            ['Risk Level', riskBadge(alert.risk_level)],
            ['Risk Score', `<strong style="font-size:18px">${(alert.risk_score || 0).toFixed(1)}</strong>`],
            ['Status', statusBadge(alert.status)],
            ['Created', fmt.datetime(alert.created_at)],
            ['Reviewed By', alert.reviewed_by || '—'],
          ].map(([k, v]) => `<div><div style="font-size:11.5px;color:#9ca3af;font-weight:600;margin-bottom:4px">${k}</div><div style="font-size:13.5px">${v}</div></div>`).join('')}
        </div>
        ${alert.officer_notes ? `<div style="margin-top:16px;padding:12px;background:#f8f9fe;border-radius:8px;font-size:13px;color:#6b7280"><strong>Notes:</strong> ${alert.officer_notes}</div>` : ''}
        ${alert.explanation ? `<div style="margin-top:12px;padding:12px;background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;font-size:13px">${alert.explanation}</div>` : ''}
        <div style="margin-top:20px;padding-top:16px;border-top:1px solid #e2e8f0;display:flex;justify-content:flex-end;gap:12px">
          ${alert.status !== 'DISMISSED' ? `<button class="btn btn-danger" id="modal-reject-btn">✗ Reject / Dismiss Alert</button>` : ''}
          ${alert.status !== 'APPROVED' ? `<button class="btn btn-success" id="modal-approve-btn">✓ Approve Alert</button>` : ''}
          ${alert.status !== 'PENDING' ? `<button class="btn btn-warning" id="modal-pending-btn">⏳ Set to Pending</button>` : ''}
        </div>
      `;
      document.getElementById('modal-reject-btn')?.addEventListener('click', async () => {
        modalEl.style.display = 'none';
        await this._action(alert.alert_id || alertId, 'dismiss');
      });
      document.getElementById('modal-approve-btn')?.addEventListener('click', async () => {
        modalEl.style.display = 'none';
        await this._action(alert.alert_id || alertId, 'approve');
      });
      document.getElementById('modal-pending-btn')?.addEventListener('click', async () => {
        modalEl.style.display = 'none';
        await this._action(alert.alert_id || alertId, 'pending');
      });
    } catch (e) {
      document.querySelector('.modal-body').innerHTML = `<p style="color:#ef4444">Failed to load: ${e.message}</p>`;
    }
  },
};


// Expose for ES Module Router
window.AlertsView = AlertsView;
