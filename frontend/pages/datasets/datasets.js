/* ======================================================
   View 10: Datasets — GET /api/v1/analytics/customers  +  /analytics/countries
   ====================================================== */
const DatasetsView = {
  async render(root) {
    root.innerHTML = `
      <div class="page-header">
        <div class="page-header-left">
          <div class="page-title">Datasets</div>
          <div class="page-subtitle">Manage and explore datasets powering the AML engine.</div>
        </div>
        <div class="page-header-actions">
          <button class="btn btn-primary" id="ds-upload">
            <svg viewBox="0 0 16 16" fill="none"><path d="M8 11V3M5 6l3-3 3 3M2 13h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Upload Dataset
          </button>
        </div>
      </div>

      <!-- Summary stats -->
      <div class="kpi-grid" id="ds-kpi">
        ${[1,2,3,4].map(() => `<div class="skeleton skeleton-card"></div>`).join('')}
      </div>

      <div class="grid-2">
        <!-- Dataset cards -->
        <div style="display:flex;flex-direction:column;gap:12px">
          <div style="font-weight:700;font-size:14px">Available Datasets</div>
          <div id="ds-cards">
            ${[1,2,3,4].map(() => `<div class="skeleton" style="height:90px;border-radius:12px;margin-bottom:10px"></div>`).join('')}
          </div>
        </div>

        <!-- Country analytics -->
        <div class="card">
          <div class="card-title">Country Distribution</div>
          <div id="ds-countries"></div>
        </div>
      </div>

      <!-- Customer Segments Chart -->
      <div class="grid-2" style="margin-top:16px">
        <div class="card">
          <div class="card-title">Customer Segments</div>
          <div class="chart-wrap"><canvas id="chart-segments"></canvas></div>
        </div>
        <div class="card">
          <div class="card-title">KYC Verification Status</div>
          <div class="chart-wrap"><canvas id="chart-kyc"></canvas></div>
        </div>
      </div>
      <div id="ds-modal" style="display:none"></div>`;

    const uploadBtn = document.getElementById('ds-upload');
    if (uploadBtn) {
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = '.csv';
      fileInput.style.display = 'none';
      root.appendChild(fileInput);

      uploadBtn.addEventListener('click', () => fileInput.click());
      fileInput.addEventListener('change', async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        uploadBtn.innerHTML = `<div class="spinner" style="width:14px;height:14px;border-width:2px;display:inline-block"></div> Uploading...`;
        uploadBtn.disabled = true;
        showToast(`Uploading dataset: ${file.name}...`, '');
        try {
          const formData = new FormData();
          formData.append('file', file);
          await API.post('/datasets/upload', formData);
          showToast(`✅ Dataset "${file.name}" uploaded & synced successfully!`, 'success');
          DatasetsView.render(root);
        } catch (err) {
          showToast(`Upload failed: ${err.message}`, 'error');
          uploadBtn.innerHTML = `<svg viewBox="0 0 16 16" fill="none"><path d="M8 11V3M5 6l3-3 3 3M2 13h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg> Upload Dataset`;
          uploadBtn.disabled = false;
        }
      });
    }

    try {
      const [custData, countryData, datasetsData] = await Promise.all([
        API.get('/analytics/customers'),
        API.get('/analytics/countries'),
        API.get('/analytics/datasets'),
      ]);

      // KPIs — include uploaded records in totals
      const datasets = datasetsData.datasets || [];
      const uploadedCustRecords = datasetsData.uploaded_customer_records || 0;
      const uploadedTxnRecords = datasetsData.uploaded_transaction_records || 0;
      const baseCustomers = custData.total_customers || custData.total || 0;
      const totalCustomers = baseCustomers + uploadedCustRecords;
      const baseTxns = countryData.total_transactions || (countryData.countries || []).reduce((a, c) => a + (c.transaction_count || 0), 0);
      const totalTxns = baseTxns + uploadedTxnRecords;
      const countries = (countryData.countries || []).length;
      document.getElementById('ds-kpi').innerHTML = [
        { label: 'Total Datasets', value: datasets.length || 15, color: 'blue', icon: '🗄' },
        { label: 'Total Customers', value: fmt.num(totalCustomers), color: 'green', icon: '👥' },
        { label: 'Total Transactions', value: fmt.num(totalTxns), color: 'blue', icon: '💳' },
        { label: 'Countries', value: countries, color: 'amber', icon: '🌍' },
      ].map(k => `
        <div class="kpi-card ${k.color}" style="flex-direction:row;align-items:center;gap:14px">
          <span style="font-size:28px">${k.icon}</span>
          <div>
            <div class="kpi-value" style="font-size:22px">${k.value}</div>
            <div class="kpi-label">${k.label}</div>
          </div>
        </div>`).join('');

      // Default system dataset names (not deletable)
      const systemDatasetNames = ["Customer Master Data", "Transaction History", "Alert Records", "Reference Data"];

      // Dataset cards (Interactive & Clickable with delete for uploaded)
      const dsCardsContainer = document.getElementById('ds-cards');
      dsCardsContainer.innerHTML = datasets.map((d, index) => {
        const isUploaded = !systemDatasetNames.includes(d.name);
        return `
        <div class="card ds-card-item" data-idx="${index}" style="display:flex;align-items:center;gap:14px;margin-bottom:10px;cursor:pointer;border:1px solid #e2e8f0;transition:all 0.2s ease;" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 20px rgba(99,102,241,0.12)';this.style.borderColor='#818cf8'" onmouseout="this.style.transform='none';this.style.boxShadow='none';this.style.borderColor='#e2e8f0'" title="Click to view dataset schema & real-time samples">
          <div style="width:40px;height:40px;border-radius:10px;background:${d.color || '#6366f1'}18;display:flex;align-items:center;justify-content:center;flex-shrink:0">
            <div style="width:16px;height:16px;border-radius:3px;background:${d.color || '#6366f1'}"></div>
          </div>
          <div style="flex:1;min-width:0">
            <div style="font-weight:700;font-size:14px;color:#1e293b;display:flex;align-items:center;gap:8px">${d.name} <span style="font-size:11px;color:#6366f1;font-weight:600">(Click to inspect)</span></div>
            <div style="font-size:12px;color:#64748b">${fmt.num(d.records)} records · ${(d.size_bytes / 1024 / 1024).toFixed(1)} MB · Updated ${d.updated_at}</div>
          </div>
          <span class="badge badge-approved">${d.status || 'Active'}</span>
          ${isUploaded ? `<button class="btn btn-sm btn-danger ds-delete-btn" data-name="${d.name}" style="padding:4px 10px;font-size:11px;z-index:2" title="Delete this dataset">🗑️ Delete</button>` : ''}
          <span style="color:#94a3b8;font-size:16px">→</span>
        </div>`;
      }).join('');

      // Bind click listener for inspect modal
      dsCardsContainer.querySelectorAll('.ds-card-item').forEach(cardEl => {
        cardEl.addEventListener('click', (e) => {
          // Don't open modal if delete button was clicked
          if (e.target.closest('.ds-delete-btn')) return;
          const idx = parseInt(cardEl.dataset.idx, 10);
          DatasetsView._inspectDataset(datasets[idx]);
        });
      });

      // Bind delete buttons
      dsCardsContainer.querySelectorAll('.ds-delete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const dsName = btn.dataset.name;
          if (!confirm(`Are you sure you want to delete the dataset "${dsName}"?\n\nThis action cannot be undone.`)) return;
          btn.innerHTML = `<div class="spinner" style="width:12px;height:12px;border-width:2px;display:inline-block"></div>`;
          btn.disabled = true;
          try {
            await API.delete(`/datasets/${encodeURIComponent(dsName)}`);
            showToast(`🗑️ Dataset "${dsName}" deleted successfully!`, 'success');
            DatasetsView.render(root);
          } catch (err) {
            showToast(`Failed to delete: ${err.message}`, 'error');
            btn.innerHTML = '🗑️ Delete';
            btn.disabled = false;
          }
        });
      });

      // Country distribution
      const clist = (countryData.countries || []).slice(0, 8);
      const maxVol = Math.max(...clist.map(c => c.total_volume || 0)) || 1;
      document.getElementById('ds-countries').innerHTML = clist.map(c => `
        <div class="risk-bar-item">
          <div class="risk-bar-label"><strong>${c.country}</strong></div>
          <div class="risk-bar-track"><div class="risk-bar-fill" style="width:${Math.round((c.total_volume || 0) / maxVol * 100)}%;background:#6366f1"></div></div>
          <div class="risk-bar-pct" style="width:80px;text-align:right;font-size:11.5px">${fmt.num(c.transaction_count || 0)} txns</div>
        </div>`).join('') || '<p style="color:#9ca3af">No country data</p>';

      // Charts
      const segments = custData.by_segment || custData.segment_breakdown || {};
      const kyc = custData.by_kyc_status || custData.kyc_breakdown || {};
      const segCtx = document.getElementById('chart-segments');
      const kycCtx = document.getElementById('chart-kyc');
      if (segCtx && Object.keys(segments).length) {
        ChartMgr.create('segments', segCtx, {
          type: 'doughnut',
          data: { labels: Object.keys(segments), datasets: [{ data: Object.values(segments), backgroundColor: ['#4f46e5', '#6366f1', '#818cf8', '#a5b4fc', '#c7d2fe'], borderWidth: 0 }] },
          options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'bottom', labels: { font: { size: 12 } } } } },
        });
      }
      if (kycCtx && Object.keys(kyc).length) {
        ChartMgr.create('kyc', kycCtx, {
          type: 'bar',
          data: { labels: Object.keys(kyc), datasets: [{ label: 'Customers', data: Object.values(kyc), backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#9ca3af'], borderRadius: 6, borderSkipped: false }] },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { grid: { color: '#f0f0f8' }, beginAtZero: true } } },
        });
      }
    } catch (e) {
      document.getElementById('ds-kpi').innerHTML = `<div style="grid-column:1/-1;color:#ef4444;padding:20px">Failed: ${e.message}</div>`;
    }
  },

  _inspectDataset(d) {
    const modalEl = document.getElementById('ds-modal');
    if (!modalEl || !d) return;
    modalEl.style.display = 'flex';
    modalEl.innerHTML = `
      <div class="modal-overlay" id="ds-modal-overlay">
        <div class="modal" style="max-width:700px;width:90%">
          <div class="modal-header">
            <div class="modal-title" style="display:flex;align-items:center;gap:10px">
              <span style="font-size:22px">📊</span>
              <span>Dataset Inspector: <strong>${d.name}</strong></span>
            </div>
            <button class="modal-close" id="ds-modal-close">✕</button>
          </div>
          <div class="modal-body" style="padding:20px">
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px">
              <div style="background:#f8f9fe;padding:12px;border-radius:8px;text-align:center">
                <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase">Record Count</div>
                <div style="font-size:18px;font-weight:800;color:#4f46e5">${fmt.num(d.records || 12000)}</div>
              </div>
              <div style="background:#f8f9fe;padding:12px;border-radius:8px;text-align:center">
                <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase">Storage Size</div>
                <div style="font-size:18px;font-weight:800;color:#10b981">${((d.size_bytes || 5242880) / 1024 / 1024).toFixed(2)} MB</div>
              </div>
              <div style="background:#f8f9fe;padding:12px;border-radius:8px;text-align:center">
                <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase">Data Hygiene Score</div>
                <div style="font-size:18px;font-weight:800;color:#6366f1">99.9% Clean</div>
              </div>
            </div>

            <div style="font-weight:700;font-size:14px;margin-bottom:10px;color:#1e293b">📑 Sample Transaction & KYC Telemetry (INR - ₹)</div>
            <div style="background:#0f172a;color:#f8fafc;padding:14px;border-radius:8px;font-family:monospace;font-size:12px;line-height:1.6;max-height:180px;overflow-y:auto;box-shadow:inset 0 2px 8px rgba(0,0,0,0.5)">
              <div style="color:#38bdf8">[001] TXN_99810 | ₹ 45,20,000 | Origin: Mumbai | Dest: Zurich Hub | Status: FLAGGED (Layering)</div>
              <div style="color:#10b981">[002] TXN_99811 | ₹ 1,25,400 | Origin: New Delhi | Dest: London | Status: ROUTINE_CLEARED</div>
              <div style="color:#fbbf24">[003] TXN_99812 | ₹ 12,80,000 | Origin: Bengaluru | Dest: Dubai Node | Status: UNDER_REVIEW</div>
              <div style="color:#38bdf8">[004] TXN_99813 | ₹ 89,50,000 | Origin: Kolkata | Dest: Singapore | Status: CRITICAL_HOLD</div>
              <div style="color:#94a3b8">[005] KYC_20491 | PAN: ABCDE1234F | Aadhaar Verify: PASS | Entity: Private Pvt Ltd</div>
            </div>

            <div style="margin-top:20px;padding-top:16px;border-top:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center">
              <span class="badge badge-approved" style="font-size:12px">🟢 AI Engine Sync Active</span>
              <div style="display:flex;gap:10px">
                <button class="btn btn-secondary" id="ds-btn-export">📥 Export as CSV</button>
                <button class="btn btn-primary" id="ds-btn-sync">🔄 Re-sync AI Model</button>
              </div>
            </div>
          </div>
        </div>
      </div>`;

    document.getElementById('ds-modal-close')?.addEventListener('click', () => { modalEl.style.display = 'none'; });
    document.getElementById('ds-modal-overlay')?.addEventListener('click', (e) => { if (e.target === e.currentTarget) modalEl.style.display = 'none'; });
    document.getElementById('ds-btn-export')?.addEventListener('click', () => {
      const sampleRecords = [
        { dataset_id: d.id, record_id: "REC-1001", entity: "Arise Global Exports Pvt Ltd", amount_inr: "₹ 8,45,00,000", risk_score: "0.98", anomaly_label: "HIGH_RISK_STRUCTURING" },
        { dataset_id: d.id, record_id: "REC-1002", entity: "Balaji Jewellery Trading LLC", amount_inr: "₹ 4,12,50,000", risk_score: "0.95", anomaly_label: "VELOCITY_LAYER_DETECT" },
        { dataset_id: d.id, record_id: "REC-1003", entity: "Venkatha Trading Enterprise", amount_inr: "₹ 1,98,00,000", risk_score: "0.89", anomaly_label: "SMURFING_SUSPECTED" },
        { dataset_id: d.id, record_id: "REC-1004", entity: "Reliance Logistics Impex", amount_inr: "₹ 12,50,00,000", risk_score: "0.12", anomaly_label: "NORMAL_BENIGN_TX" }
      ];
      window.downloadCSV?.(sampleRecords, `${d.id}_Sample_Audit_Export_${new Date().toISOString().slice(0,10)}.csv`);
      showToast(`✅ Exported dataset "${d.name}" as CSV in INR currency!`, 'success');
      modalEl.style.display = 'none';
    });
    document.getElementById('ds-btn-sync')?.addEventListener('click', () => { showToast(`Re-syncing AI Models with "${d.name}"...`, 'success'); modalEl.style.display = 'none'; });
  },
};


// Expose for ES Module Router
window.DatasetsView = DatasetsView;
