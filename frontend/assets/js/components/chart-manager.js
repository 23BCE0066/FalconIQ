export const ChartMgr = {
  _charts: {},
  
  destroy(id) { 
    if (this._charts[id]) { 
      this._charts[id].destroy(); 
      delete this._charts[id]; 
    } 
  },
  
  destroyAll() { 
    Object.keys(this._charts).forEach(id => this.destroy(id)); 
  },
  
  register(id, instance) { 
    this.destroy(id); 
    this._charts[id] = instance; 
    return instance; 
  },
  
  create(id, ctx, config) {
    this.destroy(id);
    const chart = new Chart(ctx, config);
    this._charts[id] = chart;
    return chart;
  }
};

// Apply defaults when this module is imported, assuming Chart.js is available globally
if (typeof Chart !== 'undefined') {
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.color = '#6b7280';
}
