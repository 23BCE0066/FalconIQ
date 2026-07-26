/* ======================================================
   View 5: Customers — GET /api/v1/customers
   ====================================================== */
const CustomersView = {
  _page: 1,

  async render(root) {
    root.innerHTML = `
      <div class="page-header">
        <div class="page-header-left">
          <div class="page-title">Customers</div>
          <div class="page-subtitle">Browse and monitor customer risk profiles.</div>
        </div>
        <div class="page-header-actions">
          <div id="cu-total-badge" style="font-size:13px;color:#6b7280;display:flex;align-items:center;gap:6px">
            <div class="skeleton" style="width:100px;height:20px"></div>
          </div>
        </div>
      </div>

      <!-- Filter bar -->
      <div class="filter-bar">
        <div class="search-bar" style="flex:1;max-width:340px">
          <svg viewBox="0 0 20 20" fill="none"><circle cx="9" cy="9" r="5.5" stroke="currentColor" stroke-width="1.5"/><path d="M13 13l3.5 3.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          <input id="cu-search" type="text" placeholder="Search name or email…"/>
        </div>
        <select class="input select" style="width:130px" id="cu-risk">
          <option value="">All Risk</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
          <option value="CRITICAL">Critical</option>
        </select>
        <select class="input select" style="width:140px" id="cu-kyc">
          <option value="">All KYC</option>
          <option value="VERIFIED">Verified</option>
          <option value="PENDING">Pending</option>
          <option value="FAILED">Failed</option>
          <option value="EXPIRED">Expired</option>
        </select>
        <button class="btn btn-secondary" id="cu-filter-btn">Filter</button>
      </div>

      <div class="card" style="padding:0">
        <div class="table-wrap">
          <table>
            <thead><tr>
              <th>Customer ID</th><th>Name</th><th>Email</th>
              <th>Country</th><th>Risk Level</th><th>KYC Status</th>
              <th>Annual Income</th><th>Alerts</th><th>Actions</th>
            </tr></thead>
            <tbody id="cu-tbody">${skeleton(10)}</tbody>
          </table>
        </div>
        <div class="pagination" id="cu-pag" style="padding:12px 16px"></div>
      </div>

      <div id="cu-modal" style="display:none"></div>`;

    this._page = 1;
    this._filters = {};
    this._load();

    document.getElementById('cu-filter-btn')?.addEventListener('click', () => this._applyFilters());
    document.getElementById('cu-search')?.addEventListener('keydown', (e) => { if (e.key === 'Enter') this._applyFilters(); });
    document.getElementById('cu-risk')?.addEventListener('change', () => this._applyFilters());
    document.getElementById('cu-kyc')?.addEventListener('change', () => this._applyFilters());
  },

  _applyFilters() {
    this._filters = {
      search: document.getElementById('cu-search')?.value.trim() || undefined,
      risk_level: document.getElementById('cu-risk')?.value || undefined,
      kyc_status: document.getElementById('cu-kyc')?.value || undefined,
    };
    this._page = 1;
    this._load();
  },

  async _load() {
    const tbody = document.getElementById('cu-tbody');
    tbody.innerHTML = skeleton(10);
    try {
      const params = { page: this._page, page_size: 15, ...this._filters };
      const data = await API.get('/customers', params);
      const { items, total } = normalizePage(data);

      const badge = document.getElementById('cu-total-badge');
      if (badge) badge.innerHTML = `<span style="font-weight:600;color:#0f0e2a">${fmt.num(total)}</span> customers on file`;

      if (!items.length) {
        tbody.innerHTML = `<tr><td colspan="9"><div class="empty-state"><p>No customers found</p></div></td></tr>`;
        document.getElementById('cu-pag').innerHTML = '';
        return;
      }

      tbody.innerHTML = items.map(c => `
        <tr data-id="${c.customer_id || c.id}" style="cursor:pointer">
          <td><span style="font-family:monospace;font-size:12px;color:#6366f1">${c.customer_id || c.id}</span></td>
          <td>
            <div style="display:flex;align-items:center;gap:10px">
              <div style="width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#4f46e5,#818cf8);color:white;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0">${(c.name || 'U').charAt(0).toUpperCase()}</div>
              <div>
                <div style="font-weight:600;font-size:13px">${c.name || '—'}</div>
              </div>
            </div>
          </td>
          <td style="color:#6b7280;font-size:12.5px">${c.email || '—'}</td>
          <td style="font-size:12.5px">${c.country || '—'}</td>
          <td>${riskBadge(c.risk_category)}</td>
          <td>${this._kycBadge(c.kyc_status, c.customer_id || c.id)}</td>
          <td style="font-size:13px">${c.annual_income != null ? fmt.money(c.annual_income, c.currency || 'USD') : '—'}</td>
          <td style="text-align:center">
            ${c.alert_count > 0 ? `<span style="background:#fef2f2;color:#ef4444;border-radius:100px;padding:2px 8px;font-size:12px;font-weight:700">${c.alert_count}</span>` : `<span style="color:#9ca3af">0</span>`}
          </td>
          <td>
            <div class="row-actions">
              <button class="btn btn-sm btn-secondary cu-profile" data-id="${c.customer_id || c.id}">Profile</button>
              <button class="btn btn-sm btn-secondary cu-network" data-id="${c.customer_id || c.id}" title="Network">⬡</button>
            </div>
          </td>
        </tr>`).join('');

      renderPagination(document.getElementById('cu-pag'), total, this._page, 15, (p) => { this._page = p; this._load(); });

      document.querySelectorAll('.cu-profile').forEach(btn => {
        btn.addEventListener('click', (e) => { e.stopPropagation(); this._showProfile(btn.dataset.id); });
      });
      document.querySelectorAll('.cu-network').forEach(btn => {
        btn.addEventListener('click', (e) => { e.stopPropagation(); navigateTo('network'); });
      });
      document.querySelectorAll('#cu-tbody tr').forEach(tr => {
        tr.addEventListener('click', () => this._showProfile(tr.dataset.id));
      });
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;color:#ef4444;padding:24px">Failed to load: ${e.message}</td></tr>`;
    }
  },

  _kycBadge(status, customerId) {
    if (customerId) {
      try {
        const frozen = JSON.parse(localStorage.getItem('falconiq_frozen_accounts') || '{}');
        const cid = customerId.toString().trim();
        if (frozen[cid] || frozen[cid.replace('CUST_', '')] || frozen['CUST_' + cid]) {
          return `<span style="background:#fef2f2; color:#dc2626; border:1px solid #f87171; font-weight:800; padding:4px 8px; border-radius:10px; font-size:11px; display:inline-flex; align-items:center; gap:4px; box-shadow:0 1px 3px rgba(220,38,38,0.2);">🔒 FROZEN (STR FILED)</span>`;
        }
        const watchlist = JSON.parse(localStorage.getItem('falconiq_watchlist_accounts') || '{}');
        if (watchlist[cid] || watchlist[cid.replace('CUST_', '')] || watchlist['CUST_' + cid]) {
          return `<span style="background:#eff6ff; color:#2563eb; border:1px solid #93c5fd; font-weight:700; padding:4px 8px; border-radius:10px; font-size:11px; display:inline-flex; align-items:center; gap:4px;">👁️ ON WATCHLIST</span>`;
        }
      } catch (err) {}
    }
    const s = (status || '').toUpperCase();
    const cls = s === 'VERIFIED' ? 'badge-approved' : s === 'FAILED' ? 'badge-high' : s === 'EXPIRED' ? 'badge-dismissed' : 'badge-pending';
    return `<span class="badge ${cls}">${s || '—'}</span>`;
  },

  async _showProfile(customerId) {
    const modalEl = document.getElementById('cu-modal');
    modalEl.style.display = 'flex';
    modalEl.innerHTML = `
      <div class="modal-overlay" id="cu-modal-overlay">
        <div class="modal" style="max-width:680px">
          <div class="modal-header">
            <div class="modal-title">Customer Profile</div>
            <button class="modal-close" id="cu-modal-close">✕</button>
          </div>
          <div class="modal-body"><div class="spinner" style="margin:40px auto"></div></div>
        </div>
      </div>`;
    document.getElementById('cu-modal-close')?.addEventListener('click', () => { modalEl.style.display = 'none'; });
    document.getElementById('cu-modal-overlay')?.addEventListener('click', (e) => { if (e.target === e.currentTarget) modalEl.style.display = 'none'; });

    try {
      const [profile, risk, timeline] = await Promise.all([
        API.get(`/customers/${customerId}`),
        API.get(`/customers/${customerId}/risk`),
        API.get(`/customers/${customerId}/timeline`).catch(() => ({ events: [] })),
      ]);
      const c = profile.customer || profile;
      
      let freezeBanner = '';
      let frozenInfo = null;
      let watchlistInfo = null;
      try {
        const frozen = JSON.parse(localStorage.getItem('falconiq_frozen_accounts') || '{}');
        const cid = (c.customer_id || customerId || '').toString().trim();
        frozenInfo = frozen[cid] || frozen[cid.replace('CUST_', '')] || frozen['CUST_' + cid];
        
        const watchlist = JSON.parse(localStorage.getItem('falconiq_watchlist_accounts') || '{}');
        watchlistInfo = watchlist[cid] || watchlist[cid.replace('CUST_', '')] || watchlist['CUST_' + cid];
      } catch (e) {}

      if (frozenInfo) {
        freezeBanner = `
          <div style="background:#fef2f2; border:2px solid #ef4444; color:#991b1b; border-radius:12px; padding:16px; margin-bottom:18px; box-shadow:0 4px 12px rgba(239,68,68,0.15); animation: fadeIn 0.3s ease-out;">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:10px;">
              <span style="font-size:26px;">🚨</span>
              <div>
                <strong style="display:block; color:#dc2626; font-size:14.5px; text-transform:uppercase; letter-spacing:0.5px;">STATUTORY ACCOUNT FREEZE & STR FILED</strong>
                <span style="font-size:12.5px; color:#7f1d1d;">All debit channels and SWIFT transfer privileges instantly frozen via AI Compliance Agent.</span>
              </div>
            </div>
            <div style="background:#ffffff; padding:10px 12px; border-radius:8px; border:1px solid #fecaca; font-size:12.5px; color:#475569;">
              <strong style="color:#991b1b;">⚖️ STR Audit Evidence:</strong> "${frozenInfo.reason || 'Critical AML financial crime typology detected by autonomous agent.'}"
            </div>
          </div>
        `;
      } else if (watchlistInfo) {
        freezeBanner = `
          <div style="background:#eff6ff; border:2px solid #3b82f6; color:#1e3a8a; border-radius:12px; padding:14px; margin-bottom:18px; display:flex; align-items:center; gap:12px;">
            <span style="font-size:24px;">👁️</span>
            <div>
              <strong style="display:block; color:#1d4ed8; font-size:14px; text-transform:uppercase;">PRIORITY REAL-TIME WATCHLIST ACTIVE</strong>
              <span style="font-size:12.5px;">This entity is actively monitored under 24/7 transaction interception rules by the AI Agent.</span>
            </div>
          </div>
        `;
      }

      let events = [...(timeline.events || [])];
      if (frozenInfo) {
        events.unshift({
          event_type: 'alert',
          description: '🔒 EMERGENCY DEBIT FREEZE & FINCEN STR FILED (Core Banking Gateway ISO-20022)',
          timestamp: frozenInfo.timestamp || new Date().toISOString()
        });
      }
      if (watchlistInfo) {
        events.unshift({
          event_type: 'alert',
          description: '👁️ ENROLLED IN HIGH-RISK REAL-TIME WATCHLIST BY AI COMPLIANCE AGENT',
          timestamp: watchlistInfo.timestamp || new Date().toISOString()
        });
      }

      document.querySelector('.modal-body').innerHTML = `
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px">
          <div style="width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,#4f46e5,#818cf8);color:white;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:700">${(c.name || 'U').charAt(0).toUpperCase()}</div>
          <div>
            <div style="font-size:18px;font-weight:800">${c.name || '—'}</div>
            <div style="font-size:13px;color:#9ca3af">${c.email || ''} · ${c.country || ''}</div>
          </div>
          <div style="margin-left:auto">${riskBadge(c.risk_category)}</div>
        </div>
        ${freezeBanner}
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
          ${[
            ['Customer ID', `<span style="font-family:monospace;color:#6366f1">${c.customer_id || customerId}</span>`],
            ['KYC / Freeze Status', this._kycBadge(c.kyc_status, c.customer_id || customerId)],
            ['Annual Income', fmt.money(c.annual_income, c.currency)],
            ['Occupation', c.occupation || '—'],
            ['Total Alerts', `<strong>${risk.alert_count || 0}</strong>`],
            ['Pending Alerts', `<strong style="color:#ef4444">${risk.pending_alerts || 0}</strong>`],
          ].map(([k, v]) => `<div style="background:#f8f9fe;padding:10px 14px;border-radius:8px"><div style="font-size:11px;color:#9ca3af;text-transform:uppercase;font-weight:600;margin-bottom:4px">${k}</div><div>${v}</div></div>`).join('')}
        </div>
        ${risk.recommendation ? `<div style="background:#ede9fe;border:1px solid #c4b5fd;border-radius:8px;padding:12px 14px;font-size:13px;color:#4c1d95"><strong>Recommendation:</strong> ${risk.recommendation}</div>` : ''}
        <div class="divider"></div>
        <div style="font-weight:700;font-size:13.5px;margin-bottom:10px">Recent Alerts</div>
        ${(profile.triggered_alerts || []).slice(0, 4).map(a => `
          <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f8">
            <span style="font-family:monospace;font-size:12px;color:#6366f1">${a.alert_id || '—'}</span>
            ${riskBadge(a.risk_level)}
            ${statusBadge(a.status)}
            <span style="font-size:11.5px;color:#9ca3af">${fmt.timeAgo(a.created_at)}</span>
          </div>`).join('') || '<div style="color:#9ca3af;font-size:13px;padding:8px 0">No recent alerts</div>'}
        <div class="divider"></div>
        <div style="font-weight:700;font-size:13.5px;margin-bottom:10px">Event Timeline</div>
        <div style="max-height:240px;overflow-y:auto;padding-right:8px">
          ${events.length === 0 ? '<div style="color:#9ca3af;font-size:13px">No events</div>' : 
            events.map(e => `
            <div style="display:flex;gap:12px;margin-bottom:12px">
              <div style="width:24px;height:24px;border-radius:50%;background:${e.event_type === 'alert' ? '#fee2e2' : '#e0e7ff'};color:${e.event_type === 'alert' ? '#ef4444' : '#4f46e5'};display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0">
                ${e.event_type === 'alert' ? '⚠' : '💳'}
              </div>
              <div>
                <div style="font-size:13px;font-weight:600;${e.description.includes('FROZEN') ? 'color:#dc2626;' : ''}">${e.description}</div>
                <div style="font-size:11.5px;color:#9ca3af">${fmt.datetime(e.timestamp)} · ${e.event_type.toUpperCase()}</div>
              </div>
            </div>
            `).join('')}
        </div>`;
    } catch (e) {
      document.querySelector('.modal-body').innerHTML = `<p style="color:#ef4444">Failed to load: ${e.message}</p>`;
    }
  },
};


// Expose for ES Module Router
window.CustomersView = CustomersView;
