import { DashboardLayout } from '../../layouts/dashboard-layout.js';
import { LandingLayout } from '../../layouts/landing-layout.js';

export const Router = {
  currentLayout: null,
  
  init() {
    window.addEventListener('hashchange', () => this.handleRoute());
    this.handleRoute();
  },

  async handleRoute() {
    const hash = window.location.hash.slice(1) || 'landing';
    const appRoot = document.getElementById('app');

    if (hash === 'landing') {
      if (this.currentLayout !== 'landing') {
        appRoot.innerHTML = '';
        await LandingLayout.render(appRoot);
        this.currentLayout = 'landing';
      }
    } else if (hash.startsWith('dashboard')) {
      if (this.currentLayout !== 'dashboard') {
        appRoot.innerHTML = '';
        await DashboardLayout.render(appRoot);
        this.currentLayout = 'dashboard';
      }
      
      // Extract specific view from hash like #dashboard/overview?session=123
      const viewPath = hash.split('/')[1] || 'overview';
      const [viewName, queryString] = viewPath.split('?');
      DashboardLayout.navigateTo(viewName, queryString);
    } else {
      // Default fallback
      window.location.hash = 'landing';
    }
  }
};
