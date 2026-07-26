/* ======================================================
   View 11: Settings — GET /api/v1/health + /system/info
   ====================================================== */
const SettingsView = {
  async render(root) {
    root.innerHTML = `
      <div class="page-header">
        <div class="page-header-left">
          <div class="page-title">Settings</div>
          <div class="page-subtitle">Configure system settings and preferences.</div>
        </div>
        <div class="page-header-actions">
          <button class="btn btn-primary" id="st-save">Save Settings</button>
        </div>
      </div>

      <div class="grid-6-4">
        <!-- Left: Settings forms -->
        <div style="display:flex;flex-direction:column;gap:16px">

          <!-- General Settings -->
          <div class="card">
            <div class="card-title">General Settings</div>
            <div style="display:flex;flex-direction:column;gap:14px">
              ${[
                { label: 'Platform Name', id: 'st-name', type: 'text', ph: 'Platform name' },
                { label: 'System Timezone', id: 'st-tz', type: 'text', ph: 'Timezone' },
                { label: 'Session Timeout (min)', id: 'st-timeout', type: 'number', ph: '30' },
              ].map(f => `
                <div>
                  <label style="font-size:12px;font-weight:600;color:#6b7280;display:block;margin-bottom:6px">${f.label.toUpperCase()}</label>
                  <input class="input" id="${f.id}" type="${f.type}" placeholder="${f.ph}"/>
                </div>`).join('')}
            </div>
          </div>

          <!-- Alert Settings -->
          <div class="card">
            <div class="card-title">Alert Settings</div>
            <div style="display:flex;flex-direction:column;gap:14px">
              <div>
                <label style="font-size:12px;font-weight:600;color:#6b7280;display:block;margin-bottom:6px">HIGH RISK THRESHOLD</label>
                <div style="display:flex;align-items:center;gap:12px">
                  <input type="range" id="st-high-thresh" min="50" max="95" value="75" style="flex:1" oninput="document.getElementById('st-high-val').textContent=this.value+'%'"/>
                  <span id="st-high-val" style="font-weight:700;color:#ef4444;width:40px">75%</span>
                </div>
              </div>
              <div>
                <label style="font-size:12px;font-weight:600;color:#6b7280;display:block;margin-bottom:6px">MEDIUM RISK THRESHOLD</label>
                <div style="display:flex;align-items:center;gap:12px">
                  <input type="range" id="st-med-thresh" min="20" max="70" value="40" style="flex:1" oninput="document.getElementById('st-med-val').textContent=this.value+'%'"/>
                  <span id="st-med-val" style="font-weight:700;color:#f59e0b;width:40px">40%</span>
                </div>
              </div>
              <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-top:1px solid #f0f0f8">
                <div>
                  <div style="font-weight:600;font-size:13.5px">Auto-escalate Critical Alerts</div>
                  <div style="font-size:12px;color:#9ca3af">Automatically escalate alerts above critical threshold</div>
                </div>
                <label style="position:relative;cursor:pointer;display:flex;align-items:center">
                  <input type="checkbox" checked id="st-escalate" style="opacity:0;position:absolute">
                  <div id="st-escalate-toggle" style="width:42px;height:24px;background:#4f46e5;border-radius:100px;transition:all .2s;position:relative">
                    <div style="position:absolute;top:3px;right:3px;width:18px;height:18px;background:white;border-radius:50%;transition:all .2s"></div>
                  </div>
                </label>
              </div>
            </div>
          </div>

          <!-- Security -->
          <div class="card">
            <div class="card-title">Security</div>
            <div style="display:flex;flex-direction:column;gap:12px">
              ${[
                ['Two-factor Authentication', true],
                ['Session Logging', true],
                ['IP Allowlist', false],
                ['Audit Trail', true],
              ].map(([label, enabled]) => `
                <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f8">
                  <span style="font-size:13.5px;font-weight:500">${label}</span>
                  <span class="badge ${enabled ? 'badge-approved' : 'badge-dismissed'}">${enabled ? 'Enabled' : 'Disabled'}</span>
                </div>`).join('')}
            </div>
          </div>
        </div>

        <!-- Right: System info + API Key status -->
        <div style="display:flex;flex-direction:column;gap:14px">

          <!-- System info -->
          <div class="card">
            <div class="card-title">System Information</div>
            <div id="st-sysinfo">
              ${skeleton(5)}
            </div>
          </div>

          <!-- Integrations -->
          <div class="card">
            <div class="card-title">Integrations</div>
            <div style="display:flex;flex-direction:column;gap:10px">
              ${[
                { name: 'Gemini AI', status: true, icon: '🧠' },
                { name: 'SQLite DB', status: true, icon: '🗄' },
                { name: 'Rule Engine', status: true, icon: '⚙' },
                { name: 'ML Pipeline', status: true, icon: '🤖' },
                { name: 'SMTP Alerts', status: false, icon: '📧' },
              ].map(s => `
                <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f0f0f8">
                  <span style="font-size:18px">${s.icon}</span>
                  <span style="flex:1;font-size:13.5px;font-weight:500">${s.name}</span>
                  <div style="display:flex;align-items:center;gap:6px">
                    <div style="width:8px;height:8px;border-radius:50%;background:${s.status ? '#10b981' : '#9ca3af'}"></div>
                    <span style="font-size:12px;color:${s.status ? '#10b981' : '#9ca3af'};font-weight:600">${s.status ? 'Connected' : 'Not set'}</span>
                  </div>
                </div>`).join('')}
            </div>
          </div>

          <!-- AI Log configuration -->
          <div class="card">
            <div class="card-title">AI Log Level</div>
            <select class="input select" id="st-log-level">
              <option value="INFO" selected>INFO</option>
              <option value="DEBUG">DEBUG</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </div>
        </div>
      </div>`;

    document.getElementById('st-save')?.addEventListener('click', async () => {
      try {
        await API.post('/system/settings', {
          platform_name: document.getElementById('st-name').value,
          timezone: document.getElementById('st-tz').value,
          session_timeout: parseInt(document.getElementById('st-timeout').value) || 30,
          high_risk_threshold: parseInt(document.getElementById('st-high-thresh').value) || 75,
          medium_risk_threshold: parseInt(document.getElementById('st-med-thresh').value) || 40,
          auto_escalate: document.getElementById('st-escalate').checked,
          log_level: document.getElementById('st-log-level').value,
        });
        showToast('Settings saved successfully', 'success');
      } catch (e) {
        showToast('Failed to save settings', 'error');
      }
    });

    // Load settings
    API.get('/system/settings').then(s => {
      document.getElementById('st-name').value = s.platform_name || '';
      document.getElementById('st-tz').value = s.timezone || '';
      document.getElementById('st-timeout').value = s.session_timeout || 30;
      
      const hr = document.getElementById('st-high-thresh');
      if (hr) { hr.value = s.high_risk_threshold || 75; document.getElementById('st-high-val').textContent = hr.value + '%'; }
      const mr = document.getElementById('st-med-thresh');
      if (mr) { mr.value = s.medium_risk_threshold || 40; document.getElementById('st-med-val').textContent = mr.value + '%'; }
      
      const ae = document.getElementById('st-escalate');
      if (ae) ae.checked = s.auto_escalate;
      
      const ll = document.getElementById('st-log-level');
      if (ll) ll.value = s.log_level || 'INFO';
    }).catch(e => console.error("Failed to load settings", e));

    // Load system info
    try {
      const health = await API.get('/system/info');
      const sysinfo = document.getElementById('st-sysinfo');
      if (sysinfo) {
        sysinfo.innerHTML = [
          ['Version', health.version || '2.1.0'],
          ['Environment', health.environment || 'Production'],
          ['Database', health.database || 'SQLite'],
          ['Database Status', health.db_status === 'healthy' ? '<span class="badge badge-approved">Healthy</span>' : health.db_status || '<span class="badge badge-pending">Unknown</span>'],
          ['Uptime', health.uptime || '21d 3h 12m'],
          ['Memory', health.memory || '512 MB'],
          ['CPU', health.cpu || '12%'],
          ['AI Key', health.api_key_configured ? '<span class="badge badge-approved">Configured</span>' : '<span class="badge badge-dismissed">Not configured</span>'],
        ].map(([k, v]) => `
          <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f8;font-size:13px">
            <span style="color:#9ca3af;font-weight:500">${k}</span>
            <span style="font-weight:600">${v}</span>
          </div>`).join('');
      }
    } catch { 
      const el = document.getElementById('st-sysinfo');
      if (el) el.innerHTML = '<p style="color:#ef4444;font-size:13px">Backend not reachable</p>';
    }
  },
};


// Expose for ES Module Router
window.SettingsView = SettingsView;
