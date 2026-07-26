import { API_BASE } from '../config/constants.js';
import { showToast } from '../assets/js/utils/helpers.js';

const TIMEOUT_MS = 60000;

export const API = {
  async get(path, params = {}) {
    const url = new URL(API_BASE + path);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        url.searchParams.set(k, v);
      }
    });
    
    return this._fetchWithTimeout(url, { headers: { 'Content-Type': 'application/json' } });
  },

  async post(path, body = {}) {
    if (body instanceof FormData) {
      return this._fetchWithTimeout(API_BASE + path, {
        method: 'POST',
        body: body,
      });
    }
    return this._fetchWithTimeout(API_BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  },

  async delete(path) {
    return this._fetchWithTimeout(API_BASE + path, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });
  },
  
  async _fetchWithTimeout(url, options = {}) {
    if (window.Clerk && window.Clerk.session) {
      try {
        const token = await window.Clerk.session.getToken();
        if (token) {
          options.headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
        }
        if (window.Clerk.user && window.Clerk.user.id) {
          options.headers = { ...options.headers, 'X-Clerk-User-ID': window.Clerk.user.id };
        }
      } catch (e) {
        console.warn('Could not retrieve Clerk session token:', e);
      }
    }
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), TIMEOUT_MS);
    
    try {
      const res = await fetch(url, { ...options, signal: controller.signal });
      clearTimeout(id);
      
      if (!res.ok) {
        if (res.status === 401) {
          showToast('Session expired. Please log in again.', 'error');
          // In a real app, redirect to login here
          throw new Error('Unauthorized');
        }
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      
      const json = await res.json();
      return json.data !== undefined ? json.data : json;
      
    } catch (e) {
      clearTimeout(id);
      if (e.name === 'AbortError') {
        showToast('Network timeout. The server took too long to respond.', 'error');
        throw new Error('Network timeout');
      }
      throw e;
    }
  }
};
