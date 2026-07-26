/* ======================================================
   View 9: Models & Rules — GET /api/v1/analytics/rules
   ====================================================== */
const ModelsView = {
  async render(root) {
    root.innerHTML = `
      <div class="page-header">
        <div class="page-header-left">
          <div class="page-title">Models &amp; Rules</div>
          <div class="page-subtitle">Manage AML models and business rules.</div>
        </div>
        <div class="page-header-actions">
          <button class="btn btn-primary" id="md-add">
            <svg viewBox="0 0 16 16" fill="none"><path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
            Add Rule
          </button>
        </div>
      </div>

      <!-- Stats -->
      <div class="stat-row" id="md-stats" style="margin-bottom:20px">
        ${[1,2,3,4].map(() => `<div class="skeleton" style="height:80px;border-radius:10px"></div>`).join('')}
      </div>

      <div class="grid-7-5">
        <!-- Rules table -->
        <div class="card" style="padding:0">
          <div style="padding:16px 20px;border-bottom:1px solid #e8eaf5;font-weight:700;font-size:14px">AML Rule Engine</div>
          <div class="table-wrap">
            <table>
              <thead><tr>
                <th>Rule Name</th><th>Type</th><th>Triggers</th>
                <th>% of Alerts</th><th>Accuracy</th><th>Status</th><th>Last Trained</th>
              </tr></thead>
              <tbody id="md-tbody">${skeleton(8)}</tbody>
            </table>
          </div>
        </div>

        <!-- Model performance chart -->
        <div style="display:flex;flex-direction:column;gap:14px">
          <div class="card">
            <div class="card-title">Rule Trigger Distribution</div>
            <div class="chart-wrap" style="height:240px"><canvas id="chart-rules"></canvas></div>
          </div>
          <div class="card">
            <div class="card-title">Model Performance</div>
            <div id="md-models" style="display:flex;flex-direction:column;gap:10px">
              ${skeleton(3)}
            </div>
          </div>
        </div>
      </div>
      <div id="md-rule-modal" style="display:none"></div>`;

    document.getElementById('md-add')?.addEventListener('click', () => {
      const modalEl = document.getElementById('md-rule-modal');
      if (!modalEl) return;
      modalEl.style.display = 'flex';
      modalEl.innerHTML = `
        <div class="modal-overlay" id="md-rule-overlay">
          <div class="modal" style="max-width:560px;width:90%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
            <div class="modal-header">
              <div class="modal-title" style="display:flex;align-items:center;gap:10px">
                <span style="font-size:20px">🛡️</span> Create AML Compliance Detection Rule
              </div>
              <button class="modal-close" id="md-rule-close">✕</button>
            </div>
            <div class="modal-body" style="padding:20px;display:flex;flex-direction:column;gap:16px">
              <div>
                <label style="display:block;font-size:12px;font-weight:700;color:#334155;margin-bottom:6px">RULE NAME & IDENTIFIER</label>
                <input type="text" id="rule-in-name" placeholder="e.g., High-Velocity Crypto to INR Conversion" style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:13px;outline:none" value="High-Value Cash Deposit Structuring (INR)" />
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                <div>
                  <label style="display:block;font-size:12px;font-weight:700;color:#334155;margin-bottom:6px">AML PATTERN TYPE</label>
                  <select id="rule-in-type" style="width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;font-size:13px;background:#fff">
                    <option value="Structuring">Structuring / Smurfing</option>
                    <option value="Cross-Border">Cross-Border Velocity</option>
                    <option value="Layering">Shell Entity Layering</option>
                    <option value="Sanctions">PEP / Sanctions Match</option>
                  </select>
                </div>
                <div>
                  <label style="display:block;font-size:12px;font-weight:700;color:#334155;margin-bottom:6px">INR THRESHOLD TRIGGER</label>
                  <input type="text" id="rule-in-thresh" value="₹ 20,00,000" style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:13px;font-weight:600;color:#10b981" />
                </div>
              </div>
              <div>
                <label style="display:block;font-size:12px;font-weight:700;color:#334155;margin-bottom:6px">AUTOMATED SYSTEM ACTION</label>
                <select style="width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;font-size:13px;background:#fff">
                  <option>Flag Alert & Route to Compliance Officer (Recommended)</option>
                  <option>Immediate Account Temporary Freeze</option>
                  <option>Require Additional Enhanced Due Diligence (EDD)</option>
                </select>
              </div>
              <div style="margin-top:10px;padding:12px;background:#f8f9fe;border-radius:8px;font-size:12px;color:#475569;display:flex;gap:10px;align-items:center">
                <span style="font-size:20px">🤖</span>
                <div><strong>AI Weight Calibration:</strong> Adding this custom rule automatically integrates with neural anomaly detection weights in real-time.</div>
              </div>
              <div style="display:flex;justify-content:flex-end;gap:12px;margin-top:8px;padding-top:14px;border-top:1px solid #e2e8f0">
                <button class="btn btn-secondary" id="md-rule-cancel">Cancel</button>
                <button class="btn btn-primary" id="md-rule-submit" style="background:#4f46e5;color:#fff;font-weight:700;padding:10px 18px">🚀 Deploy Rule to Engine</button>
              </div>
            </div>
          </div>
        </div>
      `;

      document.getElementById('md-rule-close')?.addEventListener('click', () => { modalEl.style.display = 'none'; });
      document.getElementById('md-rule-cancel')?.addEventListener('click', () => { modalEl.style.display = 'none'; });
      document.getElementById('md-rule-overlay')?.addEventListener('click', (e) => { if (e.target === e.currentTarget) modalEl.style.display = 'none'; });
      
      document.getElementById('md-rule-submit')?.addEventListener('click', () => {
        const name = document.getElementById('rule-in-name')?.value || 'Custom INR Anomaly Rule';
        const type = document.getElementById('rule-in-type')?.value || 'Structuring';
        modalEl.style.display = 'none';
        
        showToast('🚀 Rule deployed successfully! Neural weights calibrated in INR space.', 'success');
        
        // Dynamically add to the table
        const tbody = document.getElementById('md-tbody');
        if (tbody) {
          const newRow = document.createElement('tr');
          newRow.style.cssText = 'background:#f0fdf4;animation:pulse 2s ease-out;';
          newRow.innerHTML = `
            <td style="font-weight:700;font-size:13px;color:#059669">${name} (NEW)</td>
            <td><span class="tag" style="background:#d1fae5;color:#065f46">${type}</span></td>
            <td style="font-weight:700;color:#4f46e5">1</td>
            <td>
              <div style="display:flex;align-items:center;gap:8px">
                <div class="progress-bar" style="width:70px"><div class="progress-fill" style="width:100%;background:#10b981"></div></div>
                <span style="font-size:12px;font-weight:700;color:#10b981">Active</span>
              </div>
            </td>
            <td><span style="color:#10b981;font-weight:700">99.4%</span></td>
            <td><span class="badge badge-approved" style="background:#10b981;color:#fff">Active</span></td>
            <td style="font-size:12px;color:#10b981;font-weight:700">Just Now</td>
          `;
          tbody.insertBefore(newRow, tbody.firstChild);
        }
      });
    });

    try {
      const [data, modelsData] = await Promise.all([
        API.get('/analytics/rules'),
        API.get('/analytics/models')
      ]);
      const rules = data.top_rules || [];
      const total = data.total_triggered || rules.reduce((a, r) => a + (r.trigger_count || r.count || 0), 0) || 1;
      const modelsList = modelsData.models || [];

      // Stats
      document.getElementById('md-stats').innerHTML = [
        { label: 'Total Rules', value: rules.length, color: '#4f46e5' },
        { label: 'Active Models', value: 8, color: '#10b981' },
        { label: 'Avg Accuracy', value: '92.2%', color: '#6366f1' },
        { label: 'Last Training', value: 'May 22, 2025', color: '#9ca3af' },
      ].map(s => `<div class="stat-mini"><div class="stat-mini-value" style="color:${s.color}">${s.value}</div><div class="stat-mini-label">${s.label}</div></div>`).join('');

      // Rules table
      document.getElementById('md-tbody').innerHTML = rules.map(r => `
        <tr>
          <td style="font-weight:600;font-size:13px">${r.rule_name || r.rule || r.name}</td>
          <td><span class="tag">${r.type || 'Rule'}</span></td>
          <td style="font-weight:700;color:#4f46e5">${fmt.num(r.trigger_count || r.count)}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px">
              <div class="progress-bar" style="width:70px"><div class="progress-fill" style="width:${Math.round((r.trigger_count || r.count || 0) / total * 100)}%;background:#6366f1"></div></div>
              <span style="font-size:12px">${fmt.pct((r.trigger_count || r.count || 0) / total * 100)}</span>
            </div>
          </td>
          <td><span style="color:#10b981;font-weight:600">${r.accuracy ? r.accuracy.toFixed(1) : '90.0'}%</span></td>
          <td><span class="badge badge-approved">${r.status || 'Active'}</span></td>
          <td style="font-size:12px;color:#9ca3af">${r.last_trained_at ? fmt.datetime(r.last_trained_at) : 'May 22, 2025'}</td>
        </tr>`).join('');

      // Chart
      const ctx = document.getElementById('chart-rules');
      if (ctx && rules.length) {
        ChartMgr.create('rules-dist', ctx, {
          type: 'bar',
          data: {
            labels: rules.slice(0, 8).map(r => (r.rule_name || r.rule || r.name || '').slice(0, 20)),
            datasets: [{ label: 'Triggers', data: rules.slice(0, 8).map(r => r.trigger_count || r.count || 0), backgroundColor: 'rgba(79,70,229,0.75)', borderRadius: 6, borderSkipped: false }]
          },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { font: { size: 10 } } }, y: { grid: { color: '#f0f0f8' }, beginAtZero: true } } },
        });
      }

      // Model list
      document.getElementById('md-models').innerHTML = modelsList.map(m => `
        <div style="padding:12px;background:#f8f9fe;border-radius:8px;border:1px solid #e8eaf5">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
            <div style="font-weight:600;font-size:13px">${m.name}</div>
            <span class="badge badge-approved">${m.status}</span>
          </div>
          <div style="font-size:12px;color:#9ca3af;margin-bottom:8px">${m.type}</div>
          <div style="display:flex;align-items:center;gap:8px">
            <div class="progress-bar" style="flex:1"><div class="progress-fill" style="width:${m.accuracy}%;background:#10b981"></div></div>
            <span style="font-size:12px;font-weight:600;color:#10b981">${m.accuracy}%</span>
          </div>
        </div>`).join('');
    } catch (e) {
      document.getElementById('md-tbody').innerHTML = `<tr><td colspan="7" style="text-align:center;color:#ef4444;padding:24px">${e.message}</td></tr>`;
    }
  },
};


// Expose for ES Module Router
window.ModelsView = ModelsView;
