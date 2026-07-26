export const DashboardLayout = {
  async render(container) {
    container.innerHTML = `<div class="app-shell" id="app-shell">

  <!-- SIDEBAR -->
  <aside class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <div class="brand">
        <div class="brand-icon">
          <svg viewBox="0 0 32 32" fill="none"><path d="M16 2L4 7v9c0 7.18 5.15 13.9 12 15.45C22.85 29.9 28 23.18 28 16V7L16 2z" fill="url(#sg)"/><path d="M12 16l3 3 5-6" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><defs><linearGradient id="sg" x1="4" y1="2" x2="28" y2="32" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#818cf8"/><stop offset="100%" stop-color="#4f46e5"/></linearGradient></defs></svg>
        </div>
        <div class="brand-text">
          <span class="brand-name" style="font-weight: 900; font-size: 20px; letter-spacing: -0.5px;">Falcon<span style="color: #4f46e5;">IQ</span></span>
          <span class="brand-sub" style="font-size: 11px; font-weight: 700; color: #6b7280; letter-spacing: 0.5px;">AI AML PLATFORM</span>
        </div>
      </div>
    </div>

    <nav class="sidebar-nav" id="sidebar-nav">
      <div class="nav-section">
        <a href="#" class="nav-item active" data-view="overview" id="nav-overview">
          <svg viewBox="0 0 20 20" fill="none"><rect x="2" y="2" width="7" height="7" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="11" y="2" width="7" height="7" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="2" y="11" width="7" height="7" rx="1" stroke="currentColor" stroke-width="1.5"/><rect x="11" y="11" width="7" height="7" rx="1" stroke="currentColor" stroke-width="1.5"/></svg>
          <span>Dashboard</span>
        </a>
        <a href="#" class="nav-item" data-view="agent" id="nav-agent">
          <svg viewBox="0 0 20 20" fill="none"><path d="M10 2a8 8 0 100 16A8 8 0 0010 2z" stroke="currentColor" stroke-width="1.5"/><path d="M7 9h6M7 12h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span>Ask the Agent</span>
        </a>
        <a href="#" class="nav-item" data-view="investigations" id="nav-investigations">
          <svg viewBox="0 0 20 20" fill="none"><circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M13 13l4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <span>Investigations</span>
        </a>
        <a href="#" class="nav-item" data-view="alerts" id="nav-alerts">
          <svg viewBox="0 0 20 20" fill="none"><path d="M10 3l7 13H3L10 3z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M10 9v3M10 14h.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span>Alerts &amp; Cases</span>
          <span class="nav-badge" id="nav-alerts-badge">0</span>
        </a>
        <a href="#" class="nav-item" data-view="customers" id="nav-customers">
          <svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="7" r="3" stroke="currentColor" stroke-width="1.5"/><path d="M4 17c0-3.31 2.69-6 6-6s6 2.69 6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span>Customers</span>
        </a>
        <a href="#" class="nav-item" data-view="transactions" id="nav-transactions">
          <svg viewBox="0 0 20 20" fill="none"><path d="M3 10h14M14 7l3 3-3 3M6 7L3 10l3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>Transactions</span>
        </a>
        <a href="#" class="nav-item" data-view="reports" id="nav-reports">
          <svg viewBox="0 0 20 20" fill="none"><rect x="3" y="2" width="14" height="16" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M7 7h6M7 10h6M7 13h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span>Reports</span>
        </a>
        <a href="#" class="nav-item" data-view="network" id="nav-network">
          <svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="4" r="2" stroke="currentColor" stroke-width="1.5"/><circle cx="4" cy="16" r="2" stroke="currentColor" stroke-width="1.5"/><circle cx="16" cy="16" r="2" stroke="currentColor" stroke-width="1.5"/><path d="M10 6v4M8.3 14.5l-2.8 0M11.7 14.5l2.8 0M8.3 14.5l-1.5-4M11.7 14.5l1.5-4" stroke="currentColor" stroke-width="1.3"/></svg>
          <span>Network Analysis</span>
        </a>
        <a href="#" class="nav-item" data-view="models" id="nav-models">
          <svg viewBox="0 0 20 20" fill="none"><path d="M4 6h12M4 10h12M4 14h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span>Models &amp; Rules</span>
        </a>
        <a href="#" class="nav-item" data-view="datasets" id="nav-datasets">
          <svg viewBox="0 0 20 20" fill="none"><ellipse cx="10" cy="6" rx="7" ry="3" stroke="currentColor" stroke-width="1.5"/><path d="M3 6v4c0 1.66 3.13 3 7 3s7-1.34 7-3V6" stroke="currentColor" stroke-width="1.5"/><path d="M3 10v4c0 1.66 3.13 3 7 3s7-1.34 7-3v-4" stroke="currentColor" stroke-width="1.5"/></svg>
          <span>Datasets</span>
        </a>
        <a href="#" class="nav-item" data-view="settings" id="nav-settings">
          <svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="2.5" stroke="currentColor" stroke-width="1.5"/><path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.22 4.22l1.42 1.42M14.36 14.36l1.42 1.42M4.22 15.78l1.42-1.42M14.36 5.64l1.42-1.42" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span>Settings</span>
        </a>
      </div>
    </nav>

    <!-- System Status -->
    <div class="sidebar-footer" id="sidebar-footer">
      <div class="system-status" id="system-status">
        <div class="status-dot" id="status-dot"></div>
        <div class="status-info">
          <span class="status-label" id="status-label">Checking…</span>
          <span class="status-sub">System Status</span>
        </div>
      </div>
      <div class="ai-agent-badge" id="ai-agent-badge">
        <div class="agent-dot"></div>
        <span>AI Agent Online</span>
      </div>
    </div>
  </aside>

  <!-- MAIN AREA -->
  <div class="main-area">

    <!-- TOP BAR -->
    <header class="topbar" id="topbar">
      <div class="topbar-left">
        <button class="sidebar-toggle" id="sidebar-toggle" title="Toggle sidebar">
          <svg viewBox="0 0 20 20" fill="none"><path d="M3 6h14M3 10h14M3 14h14" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
        </button>
        <div class="topbar-search">
          <svg viewBox="0 0 20 20" fill="none"><circle cx="9" cy="9" r="5.5" stroke="currentColor" stroke-width="1.5"/><path d="M13 13l3.5 3.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          <input type="text" placeholder="Ask anything…" id="global-search" autocomplete="off"/>
        </div>
      </div>
      <div class="topbar-right">
        <div class="topbar-date" id="topbar-date"></div>
        <button class="topbar-icon-btn" id="dashboard-theme-toggle" title="Toggle Light/Dark Mode">
          <svg viewBox="0 0 24 24" fill="none" width="18" height="18" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="1.8"/>
            <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
        </button>
        <button class="topbar-icon-btn" id="topbar-notif" title="Notifications">
          <svg viewBox="0 0 20 20" fill="none"><path d="M10 2a6 6 0 016 6c0 3 1.5 4.5 2 5H2c.5-.5 2-2 2-5a6 6 0 016-6z" stroke="currentColor" stroke-width="1.5"/><path d="M8 17a2 2 0 004 0" stroke="currentColor" stroke-width="1.5"/></svg>
          <span class="notif-dot"></span>
        </button>
        <div class="topbar-avatar" id="topbar-avatar">
          <span>CO</span>
        </div>
      </div>
    </header>

    <!-- VIEW CONTENT -->
    <main class="view-root" id="view-root">
      <div class="view-loading" id="initial-loader">
        <div class="spinner"></div>
        <p>Loading FalconIQ…</p>
      </div>
    </main>
  </div>

  <!-- AI ASSISTANT FLOATING BUTTON -->
  <button class="ai-float-btn" id="ai-float-btn" title="AI Agent Assistant">
    <svg viewBox="0 0 24 24" fill="none"><path d="M12 2a10 10 0 100 20A10 10 0 0012 2z" stroke="white" stroke-width="1.6"/><path d="M8 10h8M8 14h5" stroke="white" stroke-width="1.6" stroke-linecap="round"/></svg>
  </button>

  <!-- AI ASSISTANT PANEL -->
  <div class="ai-panel" id="ai-panel">
    <div class="ai-panel-header">
      <div class="ai-panel-title">
        <div class="agent-dot"></div>
        <span>AI Agent Assistant</span>
      </div>
      <button class="ai-panel-close" id="ai-panel-close">✕</button>
    </div>
    <div class="ai-panel-messages" id="ai-panel-messages">
      <div class="ai-msg ai-msg-bot">
        <p>Hello! I'm your AML AI Agent. How can I help you today? Try asking me to <em>analyze suspicious patterns</em> or <em>show high-risk customers</em>.</p>
      </div>
    </div>
    <div class="ai-panel-input">
      <input type="text" id="ai-panel-input" placeholder="Ask the AI agent…" autocomplete="off"/>
      <button id="ai-panel-send">
        <svg viewBox="0 0 20 20" fill="none"><path d="M2 10L18 2 10 18 9 11 2 10z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>
      </button>
    </div>
  </div>

</div><!-- /app-shell -->
`;
    this.initScripts();
  },
  
  initScripts() {
    window.dispatchEvent(new Event("dashboard:rendered"));
  },

  navigateTo(viewName, queryString) {
    window.dispatchEvent(new CustomEvent("dashboard:navigate", { detail: { viewName, queryString } }));
  }
};
