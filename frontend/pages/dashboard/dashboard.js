
import { API } from '../../api/client.js';
import { fmt } from '../../assets/js/utils/formatters.js';

export const DashboardLogic = {
  init() {
    this.initSidebar();
    this.initTopbar();
    this.initLayoutInteractions();
    this.checkSystemStatus();
    this.updateAlertBadge();
    
    // Refresh interval
    setInterval(() => {
      this.checkSystemStatus();
      this.updateAlertBadge();
    }, 60000);
  },

  initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebar-toggle');
    if (toggle) {
      toggle.addEventListener('click', () => sidebar.classList.toggle('collapsed'));
    }

    // Nav clicks are handled via hash changes now
    document.querySelectorAll('.nav-item[data-view]').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        window.location.hash = 'dashboard/' + el.dataset.view;
      });
    });
  },

  initTopbar() {
    const el = document.getElementById('topbar-date');
    if (el) {
      const now = new Date();
      el.textContent = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
    }
  },

  initLayoutInteractions() {
    // 1. AI Panel toggling
    const aiBtn = document.getElementById('ai-float-btn');
    const aiPanel = document.getElementById('ai-panel');
    const aiClose = document.getElementById('ai-panel-close');
    
    if (aiBtn && aiPanel) {
      aiBtn.addEventListener('click', () => {
        aiPanel.classList.add('active');
        aiBtn.style.display = 'none';
      });
    }
    if (aiClose && aiPanel && aiBtn) {
      aiClose.addEventListener('click', () => {
        aiPanel.classList.remove('active');
        aiBtn.style.display = 'flex';
      });
    }

    // 2. Global Search
    const searchInput = document.getElementById('global-search');
    if (searchInput) {
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && searchInput.value.trim()) {
          window.location.hash = `dashboard/investigations?q=${encodeURIComponent(searchInput.value.trim())}`;
          searchInput.value = '';
        }
      });
    }

    // 3. Notifications Bell & Interactive Popup Panel
    const notifBtn = document.getElementById('topbar-notif');
    if (notifBtn) {
      notifBtn.style.position = 'relative';
      notifBtn.style.cursor = 'pointer';
      // Add red dot badge if not exists
      if (!notifBtn.querySelector('.notif-badge-dot')) {
        const dot = document.createElement('span');
        dot.className = 'notif-badge-dot';
        dot.style.cssText = 'position:absolute;top:6px;right:6px;width:8px;height:8px;background:#ef4444;border-radius:50%;border:1px solid #fff;box-shadow:0 0 6px #ef4444;';
        notifBtn.appendChild(dot);
      }

      notifBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        let panel = document.getElementById('notif-popup-panel');
        if (panel) {
          panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
          return;
        }

        panel = document.createElement('div');
        panel.id = 'notif-popup-panel';
        panel.style.cssText = 'position:absolute;top:60px;right:24px;width:380px;background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;box-shadow:0 20px 35px -5px rgba(0,0,0,0.15),0 10px 15px -5px rgba(0,0,0,0.05);z-index:99999;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;animation:fadeIn 0.15s ease-out;';
        
        panel.innerHTML = `
          <div style="padding:16px;background:#1e293b;color:#fff;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #334155">
            <div style="font-weight:700;font-size:14px;display:flex;align-items:center;gap:8px">
              <span style="font-size:18px">🔔</span> Live AML Alerts & Telemetry
            </div>
            <button id="notif-clear-btn" style="background:transparent;border:1px solid #475569;color:#cbd5e1;padding:4px 8px;border-radius:6px;font-size:11px;cursor:pointer;transition:all 0.2s">Clear All</button>
          </div>
          <div id="notif-list-body" style="max-height:360px;overflow-y:auto;divide-y:1px solid #f1f5f9;background:#fff">
            ${[
              { id: 'N1', type: 'HIGH RISK', title: '🚨 ₹ 45,20,000 Structuring Flag', desc: 'Customer CUST_920 exceeded velocity rules in Mumbai hub.', time: '2 mins ago', color: '#ef4444', link: '#dashboard/alerts' },
              { id: 'N2', type: 'MEETING', title: '📅 Demo Confirm Automation', desc: 'Microsoft Teams scheduled link dispatched to client.', time: '14 mins ago', color: '#6366f1', link: '#dashboard/agent' },
              { id: 'N3', type: 'MODEL', title: '🤖 AI AML Model v4.2 Active', desc: 'Anomaly detection weights re-calibrated successfully.', time: '1 hour ago', color: '#10b981', link: '#dashboard/models' },
              { id: 'N4', type: 'VELOCITY', title: '⚠️ Cross-Border Flow Alert', desc: '₹ 89,50,000 transfer from Kolkata to Singapore flagged.', time: '3 hours ago', color: '#f59e0b', link: '#dashboard/transactions' },
            ].map(n => `
              <div class="notif-item-row" data-link="${n.link}" style="padding:14px 16px;border-bottom:1px solid #f1f5f9;cursor:pointer;transition:background 0.15s;display:flex;flex-direction:column;gap:4px;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='#fff'">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <span style="font-size:11px;font-weight:800;color:${n.color};text-transform:uppercase;letter-spacing:0.5px">${n.type}</span>
                  <span style="font-size:11px;color:#94a3b8">${n.time}</span>
                </div>
                <div style="font-size:13px;font-weight:700;color:#0f172a">${n.title}</div>
                <div style="font-size:12px;color:#64748b;line-height:1.4">${n.desc}</div>
              </div>
            `).join('')}
          </div>
          <div style="padding:12px 16px;background:#f8f9fe;text-align:center;border-top:1px solid #e2e8f0">
            <a href="#dashboard/alerts" id="notif-view-all" style="font-size:12px;font-weight:700;color:#4f46e5;text-decoration:none">View All Compliance Alerts →</a>
          </div>
        `;
        
        document.body.appendChild(panel);

        // Bind clicks on items to navigate
        panel.querySelectorAll('.notif-item-row').forEach(row => {
          row.addEventListener('click', () => {
            panel.style.display = 'none';
            window.location.hash = row.dataset.link;
          });
        });

        // Clear all button
        document.getElementById('notif-clear-btn')?.addEventListener('click', (ev) => {
          ev.stopPropagation();
          const body = document.getElementById('notif-list-body');
          if (body) body.innerHTML = `<div style="padding:40px 20px;text-align:center;color:#94a3b8;font-size:13px">✨ No pending alerts or notifications.</div>`;
          const badge = notifBtn.querySelector('.notif-badge-dot');
          if (badge) badge.style.display = 'none';
        });

        // Close when clicking outside
        document.addEventListener('click', function onOutClick(ev) {
          if (!panel.contains(ev.target) && ev.target !== notifBtn && !notifBtn.contains(ev.target)) {
            panel.style.display = 'none';
          }
        });
      });
    }
  },


  async checkSystemStatus() {
    const dot = document.getElementById('status-dot');
    const lbl = document.getElementById('status-label');
    if (!dot || !lbl) return;
    try {
      const { status } = await API.get('/health');
      if (status === 'ok') {
        dot.className = 'status-dot online';
        lbl.textContent = 'System Online';
      } else {
        dot.className = 'status-dot offline';
        lbl.textContent = 'System Error';
      }
    } catch (e) {
      dot.className = 'status-dot offline';
      lbl.textContent = 'Disconnected';
    }
  },

  async updateAlertBadge() {
    const badge = document.getElementById('nav-alerts-badge');
    if (!badge) return;
    try {
      const res = await API.get('/alerts', { status: 'PENDING', page_size: 1 });
      const pending = res.total_items ?? res.total ?? 0;
      if (pending > 0) {
        badge.textContent = pending > 99 ? '99+' : pending;
        badge.style.display = 'flex';
      } else {
        badge.style.display = 'none';
      }
    } catch (e) {
      console.error('Failed to load pending alerts count', e);
    }
  }
};
