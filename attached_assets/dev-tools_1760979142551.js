/**
 * ACAD=GIS Dev Tools and Mocks
 * Utilities to speed up development and demos.
 */

var mockData = window.mockData || {
  id(prefix = 'id') { return `${prefix}_${Math.random().toString(36).slice(2, 10)}`; },
  date(offsetDays = 0) { return new Date(Date.now() - offsetDays * 86400000).toISOString(); },
  project(overrides = {}) {
    return {
      project_id: this.id('proj'),
      project_name: 'New Project',
      project_number: 'PROJ-' + Math.floor(1000 + Math.random() * 9000),
      client_name: 'Client Co',
      description: '',
      created_at: this.date(Math.floor(Math.random() * 365)),
      drawing_count: Math.floor(Math.random() * 50),
      ...overrides,
    };
  },
  projects(n = 10) { return Array.from({ length: n }, () => this.project()); },
  drawing(overrides = {}) {
    return {
      drawing_id: this.id('dwg'),
      project_id: this.id('proj'),
      drawing_name: 'Site Plan',
      drawing_number: 'DWG-001',
      created_at: this.date(Math.floor(Math.random() * 365)),
      ...overrides,
    };
  },
  drawings(n = 10) { return Array.from({ length: n }, () => this.drawing()); },
};

var testHelpers = window.testHelpers || {
  waitFor(predicate, timeoutMs = 2000, intervalMs = 25) {
    return new Promise((resolve, reject) => {
      const start = Date.now();
      const t = setInterval(() => {
        if (predicate()) { clearInterval(t); resolve(true); }
        else if (Date.now() - start > timeoutMs) { clearInterval(t); reject(new Error('waitFor timeout')); }
      }, intervalMs);
    });
  },
  simulateClick(el) { el && el.click && el.click(); },
};

var devTools = window.devTools || {
  logState() { try { console.log('localStorage state', { ...localStorage }); } catch {} },
  inspectComponent(name) { console.log(`Inspect request: ${name}`); },
  benchmark(fn, name = 'benchmark', iters = 1000) {
    const t0 = performance.now(); for (let i = 0; i < iters; i++) fn();
    const t1 = performance.now(); console.log(`${name}: ${(t1 - t0).toFixed(2)}ms for ${iters} iters`);
  },
};

window.mockData = mockData;
window.testHelpers = testHelpers;
window.devTools = devTools;
