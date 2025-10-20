/**
 * ACAD=GIS State Helpers
 * Simple localStorage-backed state hook for tools.
 */

function useToolState(toolName, initialState) {
  const { useEffect, useRef, useState } = React;
  const storageKey = `acadgis:${toolName}:state`;
  const mounted = useRef(false);

  // Hydrate from storage
  let start = initialState;
  try {
    const raw = localStorage.getItem(storageKey);
    if (raw) start = { ...initialState, ...JSON.parse(raw) };
  } catch {}

  const [state, setState] = useState(start);

  // Persist to storage on change (skip first render)
  useEffect(() => {
    if (!mounted.current) { mounted.current = true; return; }
    try { localStorage.setItem(storageKey, JSON.stringify(state)); } catch {}
  }, [state]);

  // Helpers
  const set = (updates) => setState(prev => ({ ...prev, ...(typeof updates === 'function' ? updates(prev) : updates) }));
  const reset = () => setState(initialState);

  return [state, set, reset];
}

// Expose globally for inline Babel scripts
window.useToolState = useToolState;

