import { Router } from './router.js';
import { ChartMgr } from './components/chart-manager.js';
import { initLanding } from '../../pages/landing/landing.js';
import { DashboardLogic } from '../../pages/dashboard/dashboard.js';
import { VIEWS } from '../../config/routes.js';
import { API } from '../../api/client.js';
import { fmt } from '../../assets/js/utils/formatters.js';
import { showToast, riskBadge, statusBadge, skeleton, paginate, normalizePage, renderPagination, downloadCSV, escapeHtml, initTheme, toggleTheme, updateThemeIcon } from '../../assets/js/utils/helpers.js';

// Expose legacy globals for views
window.API = API;
window.fmt = fmt;
window.showToast = showToast;
window.riskBadge = riskBadge;
window.statusBadge = statusBadge;
window.skeleton = skeleton;
window.paginate = paginate;
window.normalizePage = normalizePage;
window.renderPagination = renderPagination;
window.downloadCSV = downloadCSV;
window.escapeHtml = escapeHtml;
window.ChartMgr = ChartMgr;
window.initTheme = initTheme;
window.toggleTheme = toggleTheme;

// --- CLERK GOOGLE AUTHENTICATION INTEGRATION ---
function initClerkAuth() {
  const timer = setInterval(async () => {
    if (window.Clerk) {
      clearInterval(timer);
      try {
        await window.Clerk.load();
        console.log('Clerk Auth SDK Loaded successfully');
        renderAuthUI();
        window.Clerk.addListener(() => renderAuthUI());
      } catch (err) {
        console.error('Failed to load Clerk:', err);
      }
    }
  }, 200);
}

function renderAuthUI() {
  const isAuth = window.Clerk && window.Clerk.user;
  
  // 1. Landing Page Sign In button
  const signInBtn = document.getElementById('signin-btn');
  if (signInBtn && window.Clerk) {
    if (isAuth) {
      const name = window.Clerk.user.firstName || window.Clerk.user.primaryEmailAddress?.emailAddress?.split('@')[0] || 'User';
      signInBtn.textContent = `Welcome, ${name}`;
      signInBtn.href = '#/dashboard';
      signInBtn.onclick = null;
    } else {
      signInBtn.textContent = 'Sign in with Google';
      signInBtn.onclick = (e) => {
        e.preventDefault();
        window.Clerk.openSignIn({
          afterSignInUrl: window.location.origin + '/#/dashboard'
        });
      };
    }
  }

  // 2. Dashboard topbar avatar
  const avatarEl = document.getElementById('topbar-avatar');
  if (avatarEl && window.Clerk) {
    if (isAuth) {
      avatarEl.style.width = 'auto';
      avatarEl.style.height = 'auto';
      avatarEl.style.background = 'transparent';
      avatarEl.style.border = 'none';
      avatarEl.innerHTML = '<div id="clerk-user-button-mount"></div>';
      const mountTarget = document.getElementById('clerk-user-button-mount');
      if (mountTarget) {
        window.Clerk.mountUserButton(mountTarget, {
          afterSignOutUrl: window.location.origin + '/'
        });
      }
    } else {
      avatarEl.style.width = 'auto';
      avatarEl.style.height = 'auto';
      avatarEl.style.background = 'none';
      avatarEl.style.border = 'none';
      avatarEl.innerHTML = `
        <button id="clerk-dash-signin" class="btn btn-primary" style="padding: 6px 14px; font-size: 13px; border-radius: 8px; font-weight: 600; display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 4px rgba(79,70,229,0.3); cursor: pointer; border: none; background: #4f46e5; color: white;">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/></svg>
          Sign in
        </button>
      `;
      const signinBtn = document.getElementById('clerk-dash-signin');
      if (signinBtn) {
        signinBtn.addEventListener('click', () => {
          window.Clerk.openSignIn({
            afterSignInUrl: window.location.href
          });
        });
      }
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initClerkAuth();
  
  // Listen for layout rendered events BEFORE initializing router!
  window.addEventListener('landing:rendered', () => {
    initLanding();
    renderAuthUI();
    updateThemeIcon();
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) toggleBtn.addEventListener('click', toggleTheme);
  });
  
  window.addEventListener('dashboard:rendered', () => {
    DashboardLogic.init();
    renderAuthUI();
    updateThemeIcon();
    const dashToggle = document.getElementById('dashboard-theme-toggle');
    if (dashToggle) dashToggle.addEventListener('click', toggleTheme);
    
    // Also attach view objects to global scope for backward compatibility
    window.OverviewView = VIEWS.overview;
    window.AgentView = VIEWS.agent;
    window.InvestigationsView = VIEWS.investigations;
    window.AlertsView = VIEWS.alerts;
    window.CustomersView = VIEWS.customers;
    window.TransactionsView = VIEWS.transactions;
    window.ReportsView = VIEWS.reports;
    window.NetworkView = VIEWS.network;
    window.ModelsView = VIEWS.models;
    window.DatasetsView = VIEWS.datasets;
    window.RulesView = VIEWS.rules;
    window.AuditLogsView = VIEWS.audit_logs;
    window.TeamView = VIEWS.team;
    window.SettingsView = VIEWS.settings;
    window.ChartMgr = ChartMgr;
  });

  window.addEventListener('dashboard:navigate', (e) => {
    const { viewName, queryString } = e.detail;
    const view = VIEWS[viewName];
    if (!view) { console.warn('View not found:', viewName); return; }

    const params = {};
    if (queryString) {
      new URLSearchParams(queryString).forEach((val, key) => params[key] = val);
    }

    // Update nav
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const navEl = document.getElementById(`nav-${viewName}`);
    if (navEl) navEl.classList.add('active');

    // Destroy old charts
    ChartMgr.destroyAll();

    // Render view
    const root = document.getElementById('view-root');
    root.innerHTML = '';
    view.render(root, params);
  });

  // Initialize Router now that listeners are actively watching!
  Router.init();
  
  // Safety fallback: if landing or dashboard was already rendered without event catch
  if (document.getElementById('landing')) {
    initLanding();
    renderAuthUI();
    updateThemeIcon();
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn && !toggleBtn._listenerAttached) {
      toggleBtn._listenerAttached = true;
      toggleBtn.addEventListener('click', toggleTheme);
    }
  }
});
