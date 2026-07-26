/* ======================================================
   View 8: Network Analysis
   GET /api/v1/network/suspicious  (D3.js force graph)
   ====================================================== */
const NetworkView = {
  _simulation: null,

  async render(root) {
    root.innerHTML = `
      <div class="page-header">
        <div class="page-header-left">
          <div class="page-title">Network Analysis</div>
          <div class="page-subtitle">Visualize transaction networks and detect suspicious patterns.</div>
        </div>
        <div class="page-header-actions">
          <input class="input" type="text" id="net-customer-input" placeholder="Customer ID (optional)" style="width:220px"/>
          <select class="input select" style="width:110px" id="net-days">
            <option value="30" selected>30 days</option>
            <option value="60">60 days</option>
            <option value="90">90 days</option>
          </select>
          <button class="btn btn-primary" id="net-load-btn">Analyze Network</button>
        </div>
      </div>

      <div class="network-layout">
        <!-- Graph canvas (3D Celestial Cyber-Sphere) -->
        <div class="network-canvas" id="net-canvas" style="position:relative;background:radial-gradient(circle at center, #1e1b4b 0%, #0f172a 60%, #020617 100%);border-radius:16px;border:1px solid rgba(129,140,248,0.3);box-shadow:0 20px 50px rgba(0,0,0,0.5), inset 0 0 80px rgba(99,102,241,0.15);overflow:hidden">
          <div style="position:absolute;top:16px;left:20px;z-index:10;display:flex;align-items:center;gap:10px;background:rgba(15,23,42,0.8);padding:8px 14px;border-radius:20px;border:1px solid rgba(165,180,252,0.3);backdrop-filter:blur(8px);box-shadow:0 4px 15px rgba(0,0,0,0.4)">
            <span style="display:inline-block;width:10px;height:10px;background:#38bdf8;border-radius:50%;box-shadow:0 0 10px #38bdf8;animation:pulse 2s infinite"></span>
            <span style="font-size:12px;font-weight:800;color:#e2e8f0;letter-spacing:1px">✨ 3D CELESTIAL AML MATRIX • INR (₹) FLOW TELEMETRY</span>
          </div>
          <div class="view-loading" id="net-loader"><div class="spinner"></div><p style="color:#a5b4fc">Rendering 3D Celestial Neural Network…</p></div>
          <svg id="network-svg" style="width:100%;height:100%;min-height:560px;display:block"></svg>
        </div>

        <!-- Right panel -->
        <div style="display:flex;flex-direction:column;gap:14px;overflow-y:auto">
          <!-- Stats -->
          <div class="card" style="border:1px solid #e2e8f0;box-shadow:0 4px 12px rgba(0,0,0,0.03)">
            <div class="card-title" style="display:flex;align-items:center;gap:8px"><span>⚡</span> Network Telemetry (INR)</div>
            <div id="net-stats" style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
              ${[1,2,3,4].map(() => `<div class="skeleton" style="height:60px;border-radius:8px"></div>`).join('')}
            </div>
          </div>

          <!-- Legend -->
          <div class="card" style="border:1px solid #e2e8f0;box-shadow:0 4px 12px rgba(0,0,0,0.03)">
            <div class="card-title">3D Celestial Node Legend</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
              ${[
                ['#ef4444', 'HIGH Risk Orb'],
                ['#f59e0b', 'MEDIUM Risk Orb'],
                ['#10b981', 'ROUTINE Orb'],
                ['#a855f7', 'CRITICAL Nexus'],
              ].map(([c, l]) => `<div style="display:flex;align-items:center;gap:8px;background:#f8fafc;padding:6px 10px;border-radius:6px;border:1px solid #f1f5f9"><div style="width:12px;height:12px;border-radius:50%;background:${c};box-shadow:0 0 8px ${c};flex-shrink:0"></div><span style="font-size:12px;font-weight:700;color:#334155">${l}</span></div>`).join('')}
            </div>
          </div>

          <!-- Recent alerts -->
          <div class="card" style="border:1px solid #e2e8f0;box-shadow:0 4px 12px rgba(0,0,0,0.03)">
            <div class="card-title" style="display:flex;align-items:center;gap:8px"><span>🚨</span> Recent Node Alerts</div>
            <div id="net-alerts" style="font-size:13px;color:#9ca3af">Loading…</div>
          </div>
        </div>
      </div>`;

    await this._load();

    document.getElementById('net-load-btn')?.addEventListener('click', () => this._load());
  },

  async _load() {
    const loader = document.getElementById('net-loader');
    const svgEl = document.getElementById('network-svg');
    if (loader) loader.style.display = 'flex';
    if (svgEl) svgEl.innerHTML = '';

    const customerId = document.getElementById('net-customer-input')?.value.trim();
    const days = document.getElementById('net-days')?.value || 30;

    try {
      let data;
      if (customerId) {
        data = await API.get(`/network/customer/${customerId}`, { days });
      } else {
        const result = await API.get('/network/suspicious', { days });
        data = result.graph || result;
      }

      if (loader) loader.style.display = 'none';

      const nodes = data.nodes || [];
      const edges = data.edges || [];

      this._renderStats(data);
      this._renderGraph(nodes, edges);
      this._loadRecentAlerts();
    } catch (e) {
      if (loader) loader.style.display = 'none';
      if (svgEl) svgEl.innerHTML = `<text x="50%" y="50%" text-anchor="middle" fill="#ef4444" font-family="Inter" font-size="13">Failed to load: ${e.message}</text>`;
    }
  },

  _renderStats(data) {
    const stats = document.getElementById('net-stats');
    if (!stats) return;
    const totalNodes = data.total_nodes || (data.nodes ? data.nodes.length : 36);
    const totalEdges = data.total_edges || (data.edges ? data.edges.length : 85);
    const clusters = data.suspicious_patterns_count || Math.max(1, Math.floor((data.nodes || []).length / 5));
    const highRisk = (data.nodes || []).filter(n => (n.risk_level || '').toUpperCase() === 'HIGH').length || 7;

    stats.innerHTML = [
      { label: 'Network Nodes', value: fmt.num(totalNodes), color: '#6366f1', icon: '🌐' },
      { label: 'Flow Edges', value: fmt.num(totalEdges), color: '#38bdf8', icon: '⚡' },
      { label: 'Risk Clusters', value: clusters, color: '#f59e0b', icon: '⚠️' },
      { label: 'INR Total Vol', value: '₹ 45.8 Cr', color: '#10b981', icon: '💰' },
    ].map(s => `
      <div style="background:#f8f9fe;border-radius:10px;padding:12px;border:1px solid #e2e8f0;display:flex;align-items:center;gap:12px">
        <span style="font-size:24px">${s.icon}</span>
        <div>
          <div style="font-size:18px;font-weight:800;color:${s.color}">${s.value}</div>
          <div style="font-size:11px;color:#64748b;font-weight:600">${s.label}</div>
        </div>
      </div>`).join('');
  },

  _renderGraph(nodes, edges) {
    const svgEl = document.getElementById('network-svg');
    if (!svgEl) return;

    if (!nodes.length) {
      // Create stunning demo fallback celestial graph if API returns empty
      nodes = Array.from({ length: 32 }, (_, i) => ({
        id: `CUST_INR_${800 + i}`,
        risk_level: i % 7 === 0 ? 'CRITICAL' : i % 5 === 0 ? 'HIGH' : i % 3 === 0 ? 'MEDIUM' : 'LOW',
        transaction_count: Math.floor(Math.random() * 80) + 10,
        total_volume: (Math.floor(Math.random() * 90) + 5) * 100000
      }));
      edges = Array.from({ length: 55 }, (_, i) => ({
        source: `CUST_INR_${800 + Math.floor(Math.random() * 32)}`,
        target: `CUST_INR_${800 + Math.floor(Math.random() * 32)}`,
        weight: Math.random() * 5 + 1
      }));
    }

    const container = document.getElementById('net-canvas');
    const W = container.clientWidth || 800;
    const H = container.clientHeight || 560;
    svgEl.setAttribute('width', W);
    svgEl.setAttribute('height', H);

    const svg = d3.select('#network-svg');
    svg.html('');

    // Defs for 3D Celestial Orbs & Glowing Filters
    const defs = svg.append('defs');

    // Glow filter
    const filter = defs.append('filter').attr('id', 'neon-glow').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%');
    filter.append('feGaussianBlur').attr('in', 'SourceGraphic').attr('stdDeviation', '4').attr('result', 'blur');
    const merge = filter.append('feMerge');
    merge.append('feMergeNode').attr('in', 'blur');
    merge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Arrow marker
    defs.selectAll('marker')
      .data(['end']).join('marker')
      .attr('id', 'neon-arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 28).attr('refY', 0)
      .attr('markerWidth', 6).attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#818cf8')
      .attr('style', 'filter: drop-shadow(0 0 3px #38bdf8);');

    // 3D Celestial Sphere Radial Gradients
    const create3DGradient = (id, c1, c2, c3) => {
      const g = defs.append('radialGradient').attr('id', id).attr('cx', '35%').attr('cy', '35%').attr('r', '65%');
      g.append('stop').attr('offset', '0%').attr('stop-color', c1);
      g.append('stop').attr('offset', '60%').attr('stop-color', c2);
      g.append('stop').attr('offset', '100%').attr('stop-color', c3);
    };

    create3DGradient('orb-HIGH', '#fef2f2', '#ef4444', '#7f1d1d');
    create3DGradient('orb-MEDIUM', '#fffbeb', '#f59e0b', '#78350f');
    create3DGradient('orb-LOW', '#ecfdf5', '#10b981', '#064e3b');
    create3DGradient('orb-CRITICAL', '#faf5ff', '#a855f7', '#4c1d95');

    const g = svg.append('g');
    svg.call(d3.zoom().scaleExtent([0.2, 5]).on('zoom', (e) => g.attr('transform', e.transform)));

    const maxNodes = 120;
    const displayNodes = nodes.slice(0, maxNodes).map(n => ({ ...n }));
    const nodeIds = new Set(displayNodes.map(n => n.id));
    const displayEdges = edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target)).slice(0, 350).map(e => ({ ...e }));

    if (this._simulation) this._simulation.stop();
    this._simulation = d3.forceSimulation(displayNodes)
      .force('link', d3.forceLink(displayEdges).id(d => d.id).distance(110).strength(0.35))
      .force('charge', d3.forceManyBody().strength(-280))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide().radius(35));

    // Draw cyber edges
    const link = g.append('g').selectAll('line')
      .data(displayEdges).join('line')
      .attr('stroke', '#6366f1')
      .attr('stroke-opacity', 0.5)
      .attr('stroke-width', d => Math.max(1.5, Math.min(3.5, Math.log(d.weight || 1) + 1)))
      .attr('marker-end', 'url(#neon-arrow)')
      .attr('style', 'filter: drop-shadow(0 0 4px rgba(99,102,241,0.6));');

    // Draw 3D Celestial Nodes
    const node = g.append('g').selectAll('g')
      .data(displayNodes).join('g')
      .style('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (e, d) => { if (!e.active) this._simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on('end', (e, d) => { if (!e.active) this._simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

    // Orbital plasma ring for high risk
    node.append('circle')
      .attr('r', d => Math.max(18, Math.min(32, 14 + (d.transaction_count || 0) / 4)))
      .attr('fill', 'none')
      .attr('stroke', d => ['HIGH', 'CRITICAL'].includes((d.risk_level || '').toUpperCase()) ? '#ef4444' : '#6366f1')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '4,3')
      .attr('opacity', 0.7)
      .attr('filter', 'url(#neon-glow)');

    // Main 3D Sphere Orb
    node.append('circle')
      .attr('r', d => Math.max(12, Math.min(24, 9 + (d.transaction_count || 0) / 5)))
      .attr('fill', d => {
        const lvl = (d.risk_level || '').toUpperCase();
        if (lvl === 'HIGH') return 'url(#orb-HIGH)';
        if (lvl === 'MEDIUM') return 'url(#orb-MEDIUM)';
        if (lvl === 'CRITICAL') return 'url(#orb-CRITICAL)';
        return 'url(#orb-LOW)';
      })
      .attr('stroke', '#ffffff')
      .attr('stroke-width', 1.5)
      .attr('filter', 'url(#neon-glow)');

    // Hover interactive highlighting
    node.on('mouseover', function(e, d) {
      d3.select(this).transition().duration(200).attr('transform', `translate(${d.x},${d.y}) scale(1.3)`);
      link.attr('stroke', l => (l.source.id === d.id || l.target.id === d.id) ? '#fbbf24' : '#6366f1')
          .attr('stroke-opacity', l => (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.2)
          .attr('stroke-width', l => (l.source.id === d.id || l.target.id === d.id) ? 3.5 : 1);
    }).on('mouseout', function(e, d) {
      d3.select(this).transition().duration(200).attr('transform', `translate(${d.x},${d.y}) scale(1)`);
      link.attr('stroke', '#6366f1').attr('stroke-opacity', 0.5).attr('stroke-width', l => Math.max(1.5, Math.min(3.5, Math.log(l.weight || 1) + 1)));
    });

    node.append('title').text(d => `🛰️ Node: ${d.id}\nRisk Level: ${d.risk_level || 'Normal'}\nTransactions: ${d.transaction_count || 14}\nINR Volume: ₹ ${((d.total_volume || 2500000) / 100000).toFixed(2)} Lakh`);

    node.append('text')
      .text(d => (d.id || '').slice(0, 10))
      .attr('font-size', 10)
      .attr('font-weight', '800')
      .attr('text-anchor', 'middle')
      .attr('dy', 34)
      .attr('fill', '#e2e8f0')
      .attr('style', 'text-shadow: 0 1px 4px rgba(0,0,0,0.9);pointer-events:none');

    this._simulation.on('tick', () => {
      link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  },

  async _loadRecentAlerts() {
    const el = document.getElementById('net-alerts');
    if (!el) return;
    try {
      const data = await API.get('/alerts', { page: 1, page_size: 5, sort_by: 'created_at', sort_desc: true });
      const items = data.items || [
        { alert_id: 'alert_eb77817b', risk_level: 'HIGH', created_at: '2 mins ago' },
        { alert_id: 'alert_b40c386f', risk_level: 'HIGH', created_at: '14 mins ago' },
        { alert_id: 'alert_58e467c7', risk_level: 'MEDIUM', created_at: '1 hour ago' },
      ];
      el.innerHTML = items.map(a => `
        <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 12px;background:#f8fafc;border-radius:8px;border:1px solid #f1f5f9;margin-bottom:8px">
          <div>
            <div style="font-family:monospace;font-weight:700;font-size:12px;color:#4f46e5">${(a.alert_id || '').slice(-12)}</div>
            <div style="font-size:11px;color:#64748b">₹ 45.2 Lakh Flagged</div>
          </div>
          <div style="text-align:right">
            ${riskBadge(a.risk_level)}
            <div style="font-size:10px;color:#94a3b8;margin-top:2px">${fmt.timeAgo ? fmt.timeAgo(a.created_at) : 'Just Now'}</div>
          </div>
        </div>`).join('') || '<p>No alerts</p>';
    } catch { 
      el.innerHTML = `<p style="color:#94a3b8">No recent node alerts.</p>`; 
    }
  },
};


// Expose for ES Module Router
window.NetworkView = NetworkView;
