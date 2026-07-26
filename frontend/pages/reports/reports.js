/* ======================================================
   View 7: Reports — POST /api/v1/reports/generate
   ====================================================== */
const ReportsView = {
  _generated: [],

  render(root) {
    root.innerHTML = `
      <div class="page-header">
        <div class="page-header-left">
          <div class="page-title">Reports</div>
          <div class="page-subtitle">Generate and download AML compliance reports.</div>
        </div>
      </div>

      <div class="grid-6-4">
        <!-- Left: Generate panel -->
        <div>
          <!-- Report type cards -->
          <div style="margin-bottom:20px">
            <div style="font-weight:700;font-size:14px;margin-bottom:14px">Select Report Type</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px" id="rp-type-cards">
              ${[
                { id: 'risk_summary', label: 'Risk Summary', desc: 'Customer risk distribution & top AML rules', icon: '🛡', color: '#4f46e5' },
                { id: 'transaction_analysis', label: 'Transaction Analysis', desc: 'Transaction trends & country breakdown', icon: '💳', color: '#10b981' },
                { id: 'alert_report', label: 'Alert Report', desc: 'Alert statistics & recent alerts', icon: '⚠', color: '#ef4444' },
                { id: 'compliance', label: 'Compliance Overview', desc: 'Executive compliance summary', icon: '📋', color: '#7c3aed' },
              ].map(t => `
                <div class="card rp-type-card" data-type="${t.id}" style="cursor:pointer;border:2px solid transparent;transition:all .2s">
                  <div style="font-size:28px;margin-bottom:8px">${t.icon}</div>
                  <div style="font-weight:700;font-size:13.5px;margin-bottom:4px">${t.label}</div>
                  <div style="font-size:12px;color:#9ca3af">${t.desc}</div>
                </div>`).join('')}
            </div>
          </div>

          <!-- Format + Generate -->
          <div class="card">
            <div class="card-title">Report Configuration</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
              <div>
                <label style="font-size:12px;font-weight:600;color:#6b7280;display:block;margin-bottom:6px">SELECTED TYPE</label>
                <div id="rp-selected-type" style="font-size:13.5px;font-weight:600;color:#4f46e5;padding:8px 12px;background:#f0f0ff;border-radius:6px">None selected</div>
              </div>
              <div>
                <label style="font-size:12px;font-weight:600;color:#6b7280;display:block;margin-bottom:6px">FORMAT</label>
                <select class="input select" id="rp-format">
                  <option value="json">JSON</option>
                  <option value="markdown">Markdown</option>
                  <option value="pdf">PDF</option>
                  <option value="doc">DOC (Word)</option>
                </select>
              </div>
            </div>
            <button class="btn btn-primary" id="rp-generate-btn" disabled style="width:100%">
              <svg viewBox="0 0 16 16" fill="none"><path d="M8 2v9M5 8l3 3 3-3M2 13h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
              Generate Report
            </button>
          </div>
        </div>

        <!-- Right: Generated reports list -->
        <div class="card">
          <div class="section-header">
            <span class="card-title">Generated Reports</span>
            <span style="font-size:12px;color:#9ca3af" id="rp-count">0 reports</span>
          </div>
          <div id="rp-list">
            <div class="empty-state">
              <svg viewBox="0 0 24 24" fill="none"><rect x="4" y="2" width="16" height="20" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              <p>No reports yet. Generate your first report.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Report content preview -->
      <div id="rp-preview" style="display:none;margin-top:16px">
        <div class="card">
          <div class="section-header">
            <span class="card-title" id="rp-preview-title">Report Preview</span>
            <div style="display:flex;gap:8px">
              <button class="btn btn-secondary btn-sm" id="rp-copy-btn">Copy</button>
              <button class="btn btn-secondary btn-sm" id="rp-preview-close">✕ Close</button>
            </div>
          </div>
          <div id="rp-preview-content" style="background:#f8f9fe;border:1px solid #e8eaf5;border-radius:8px;padding:16px;font-family:monospace;font-size:12px;max-height:400px;overflow-y:auto;white-space:pre-wrap;line-height:1.6"></div>
        </div>
      </div>`;

    this._selectedType = null;
    this._generated = [];

    // Fetch reports
    API.get('/reports').then(data => {
      this._generated = data.items || data.data || [];
      this._renderList();
    }).catch(e => console.error("Failed to load reports", e));

    // Type card selection
    document.querySelectorAll('.rp-type-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.rp-type-card').forEach(c => { c.style.borderColor = 'transparent'; c.style.background = 'white'; });
        card.style.borderColor = '#6366f1';
        card.style.background = '#f0f0ff';
        this._selectedType = card.dataset.type;
        document.getElementById('rp-selected-type').textContent = card.dataset.type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        document.getElementById('rp-generate-btn').disabled = false;
      });
    });

    document.getElementById('rp-generate-btn')?.addEventListener('click', () => this._generate());
    document.getElementById('rp-preview-close')?.addEventListener('click', () => { document.getElementById('rp-preview').style.display = 'none'; });
  },

  async _generate() {
    if (!this._selectedType) return;
    const btn = document.getElementById('rp-generate-btn');
    const format = document.getElementById('rp-format')?.value || 'json';

    btn.disabled = true;
    btn.innerHTML = `<div class="spinner" style="width:16px;height:16px;border-width:2px"></div> Generating…`;

    try {
      const report = await API.post('/reports/generate', { report_type: this._selectedType, format });
      this._generated.unshift(report);
      this._renderList();
      showToast('Report generated successfully!', 'success');
      this._showPreview(report);
    } catch (e) {
      showToast(`Failed to generate: ${e.message}`, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<svg viewBox="0 0 16 16" fill="none"><path d="M8 2v9M5 8l3 3 3-3M2 13h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg> Generate Report`;
    }
  },

  _renderList() {
    const list = document.getElementById('rp-list');
    const count = document.getElementById('rp-count');
    if (count) count.textContent = `${this._generated.length} report${this._generated.length !== 1 ? 's' : ''}`;

    if (!this._generated.length) {
      list.innerHTML = `<div class="empty-state"><p>No reports yet.</p></div>`;
      return;
    }

    list.innerHTML = this._generated.map(r => `
      <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f0f0f8;gap:8px">
        <div>
          <div style="font-size:13px;font-weight:600">${(r.report_type || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
          <div style="font-size:11.5px;color:#9ca3af">${r.report_id} · ${r.format?.toUpperCase()}</div>
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-sm btn-secondary rp-preview-btn" data-id="${r.report_id}">Preview</button>
          <a class="btn btn-sm btn-primary" href="${(window.location.origin.startsWith('http') && (window.location.port === '8000' || !window.location.port) ? window.location.origin : 'http://localhost:8000')}/api/v1/reports/download/${r.report_id}" target="_blank">↓</a>
        </div>
      </div>`).join('');

    document.querySelectorAll('.rp-preview-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const r = this._generated.find(x => x.report_id === btn.dataset.id);
        if (r) this._showPreview(r);
      });
    });
  },

  _showPreview(report) {
    const preview = document.getElementById('rp-preview');
    const title = document.getElementById('rp-preview-title');
    const content = document.getElementById('rp-preview-content');
    const copyBtn = document.getElementById('rp-copy-btn');

    preview.style.display = 'block';
    title.textContent = `${(report.report_type || '').replace(/_/g, ' ')} — ${report.format?.toUpperCase()}`;

    let text = '';
    if (['markdown', 'pdf', 'doc', 'docx'].includes(report.format)) {
      text = report.markdown || JSON.stringify(report.content, null, 2);
    } else {
      text = JSON.stringify(report.content, null, 2);
    }
    content.textContent = text;
    preview.scrollIntoView({ behavior: 'smooth' });

    copyBtn.onclick = () => {
      navigator.clipboard.writeText(text);
      showToast('Copied to clipboard', 'success');
    };
  },
};


// Expose for ES Module Router
window.ReportsView = ReportsView;
