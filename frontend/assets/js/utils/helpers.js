import { fmt } from './formatters.js';

export function showToast(msg, type = '') {
  let toast = document.getElementById('global-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'global-toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.className = `toast ${type}`;
  requestAnimationFrame(() => { toast.classList.add('show'); });
  setTimeout(() => { toast.classList.remove('show'); }, 3000);
}

export function escapeHtml(unsafe) {
  if (!unsafe) return '';
  return String(unsafe)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export function riskBadge(level) {
  if (!level) return '<span class="badge badge-low">—</span>';
  const l = level.toUpperCase();
  const cls = l === 'HIGH' ? 'badge-high' : l === 'CRITICAL' ? 'badge-critical' : l === 'MEDIUM' ? 'badge-medium' : 'badge-low';
  return `<span class="badge ${cls}">${l}</span>`;
}

export function statusBadge(status) {
  if (!status) return '';
  const s = status.toLowerCase().replace(/ /g, '_');
  const cls = { 
    pending: 'badge-pending', 
    approved: 'badge-approved', 
    dismissed: 'badge-dismissed', 
    under_review: 'badge-review', 
    escalated: 'badge-escalated', 
    completed: 'badge-completed', 
    failed: 'badge-failed' 
  };
  return `<span class="badge ${cls[s] || 'badge-pending'}">${status}</span>`;
}

export function skeleton(rows = 5, isTable = (rows > 5)) {
  if (isTable) {
    return Array.from({ length: rows }, () => `<tr><td colspan="12" style="border:none;padding:8px 16px;"><div class="skeleton skeleton-row"></div></td></tr>`).join('');
  }
  return Array.from({ length: rows }, () => `<div class="skeleton skeleton-row"></div>`).join('');
}

export function paginate(items, page, size) {
  const start = (page - 1) * size;
  return items.slice(start, start + size);
}

export function normalizePage(data) {
  const items = data.items || data.results || [];
  const total = data.total_items ?? data.total ?? 0;
  return { items, total };
}

export function renderPagination(container, total, page, size, onChange) {
  const totalPages = Math.max(1, Math.ceil(total / size));
  const start = Math.min((page - 1) * size + 1, total);
  const end = Math.min(page * size, total);
  const pages = [];
  for (let i = Math.max(1, page - 2); i <= Math.min(totalPages, page + 2); i++) pages.push(i);
  
  container.innerHTML = `
    <span>${fmt.num(start)}–${fmt.num(end)} of ${fmt.num(total)}</span>
    <div class="pagination-btns">
      <button class="page-btn" data-p="${page - 1}" ${page === 1 ? 'disabled' : ''}>‹</button>
      ${pages.map(p => `<button class="page-btn ${p === page ? 'active' : ''}" data-p="${p}">${p}</button>`).join('')}
      <button class="page-btn" data-p="${page + 1}" ${page >= totalPages ? 'disabled' : ''}>›</button>
    </div>`;
    
  container.querySelectorAll('.page-btn:not([disabled])').forEach(btn => {
    btn.addEventListener('click', () => onChange(+btn.dataset.p));
  });
}

export function downloadCSV(items, filename) {
  if (!items || !items.length) {
    showToast('No data to export', 'error');
    return;
  }
  const headers = Object.keys(items[0]);
  const csvRows = [
    headers.join(','),
    ...items.map(row => 
      headers.map(field => {
        let val = row[field];
        if (val === null || val === undefined) val = '';
        val = String(val).replace(/"/g, '""');
        return `"${val}"`;
      }).join(',')
    )
  ];
  const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.setAttribute('hidden', '');
  a.setAttribute('href', url);
  a.setAttribute('download', filename);
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

export function initTheme() {
  const saved = localStorage.getItem('falconiq-theme') || 'light';
  if (saved === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    document.body.classList.add('dark-mode');
  } else {
    document.documentElement.removeAttribute('data-theme');
    document.body.classList.remove('dark-mode');
  }
  updateThemeIcon();
}

export function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem('falconiq-theme', next);
  initTheme();
  showToast(`Switched to ${next} theme`, 'success');
}

export function updateThemeIcon() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const iconHtml = isDark 
    ? '<svg viewBox="0 0 24 24" fill="none" width="18" height="18" xmlns="http://www.w3.org/2000/svg"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" fill="#f59e0b" stroke="#f59e0b" stroke-width="1.5"/></svg>'
    : '<svg viewBox="0 0 24 24" fill="none" width="18" height="18" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="1.8"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
  
  document.querySelectorAll('#theme-toggle, #dashboard-theme-toggle').forEach(btn => {
    btn.innerHTML = iconHtml;
  });
}
