/**
 * ACAD=GIS Enhanced API Helpers
 * Wraps fetch with common patterns and adds query builder and upload progress.
 */

var API = window.API || (() => {
  const BASE = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://localhost:8000/api';

  const toQuery = (obj = {}) => {
    const params = new URLSearchParams();
    Object.entries(obj).forEach(([k, v]) => {
      if (v === undefined || v === null || v === '') return;
      if (Array.isArray(v)) v.forEach(val => params.append(k, val));
      else params.append(k, v);
    });
    const s = params.toString();
    return s ? `?${s}` : '';
  };

  async function request(method, endpoint, { data, headers, signal } = {}) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json', ...(headers || {}) },
      signal,
    };
    if (data !== undefined) opts.body = JSON.stringify(data);
    const res = await fetch(`${BASE}${endpoint}`, opts);
    if (!res.ok) {
      let detail = '';
      try { const j = await res.json(); detail = j.detail || j.message || ''; } catch {}
      throw new Error(`API ${method} ${endpoint} failed: ${res.status} ${res.statusText} ${detail}`.trim());
    }
    const contentType = res.headers.get('content-type') || '';
    return contentType.includes('application/json') ? res.json() : res.text();
  }

  // CRUD helpers
  const create = (endpoint, data, options) => request('POST', endpoint, { data, ...(options || {}) });
  const read = (endpoint, id, options) => request('GET', `${endpoint}/${encodeURIComponent(id)}`, options);
  const update = (endpoint, id, data, options) => request('PUT', `${endpoint}/${encodeURIComponent(id)}`, { data, ...(options || {}) });
  const remove = (endpoint, id, options) => request('DELETE', `${endpoint}/${encodeURIComponent(id)}`, options);
  const list = (endpoint, query, options) => request('GET', `${endpoint}${toQuery(query)}`, options);

  // Batch helpers
  const batchDelete = (endpoint, ids = []) => create(`${endpoint}/batch-delete`, { ids });
  const batchUpdate = (endpoint, updates = []) => create(`${endpoint}/batch-update`, { updates });

  // Upload with progress (XHR)
  function uploadWithProgress(endpoint, formData, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${BASE}${endpoint}`);
      xhr.upload.onprogress = (evt) => {
        if (evt.lengthComputable && typeof onProgress === 'function') {
          const pct = Math.round((evt.loaded / evt.total) * 100);
          onProgress(pct, evt);
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try { resolve(JSON.parse(xhr.responseText)); }
          catch { resolve(xhr.responseText); }
        } else {
          reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
        }
      };
      xhr.onerror = () => reject(new Error('Network error during upload'));
      xhr.send(formData);
    });
  }

  // Query builder
  function query(endpoint) {
    const qs = {};
    const api = {
      filter(k, v) { qs[k] = v; return api; },
      sort(k, dir = 'asc') { qs.sort = k; qs.dir = dir; return api; },
      limit(n) { qs.limit = n; return api; },
      offset(n) { qs.offset = n; return api; },
      execute(options) { return list(endpoint, qs, options); },
    };
    return api;
  }

  return { request, create, read, update, delete: remove, list, batchDelete, batchUpdate, uploadWithProgress, query };
})();

// Provide global alias for convenience in tools
window.API = API;
