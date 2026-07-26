// Using global variables for now to maintain compatibility with the existing view logic
// which relies on ChartMgr, API, fmt etc being globally available, 
// OR we would need to refactor every single view file to use imports.
// For the scope of this refactor (structural only, no functionality change),
// we will load the views via script tags in the new index.html and they will
// register themselves to the global window object.

export const VIEWS = {
  get overview() { return window.OverviewView; },
  get agent() { return window.AgentView; },
  get investigations() { return window.InvestigationsView; },
  get alerts() { return window.AlertsView; },
  get customers() { return window.CustomersView; },
  get transactions() { return window.TransactionsView; },
  get reports() { return window.ReportsView; },
  get network() { return window.NetworkView; },
  get models() { return window.ModelsView; },
  get datasets() { return window.DatasetsView; },
  get settings() { return window.SettingsView; }
};
