/**
 * ACAD=GIS Shared React Components
 * Version: 2.0
 * 
 * Reusable React components for all tools.
 * Import this file AFTER React, ReactDOM, and Babel are loaded.
 * 
 * Usage:
 * <script src="../shared/react-components.js"></script>
 */

// ============================================
// DATATABLE COMPONENT
// ============================================

/**
 * DataTable - Sortable, searchable, paginated table component
 * 
 * Props:
 * - data: Array of objects to display
 * - columns: Array of column definitions
 *   - key: string - property name in data object
 *   - label: string - display name for column
 *   - sortable: boolean - enable sorting (default: true)
 *   - render: function(value, row) - custom render function
 *   - format: string - 'date', 'number', 'currency'
 * - onRowClick: function(row) - called when row is clicked
 * - onEdit: function(row) - shows edit button, called when clicked
 * - onDelete: function(row) - shows delete button, called when clicked
 * - onView: function(row) - shows view button, called when clicked
 * - searchable: boolean - enable search bar (default: true)
 * - pagination: boolean - enable pagination (default: true)
 * - pageSize: number - rows per page (default: 20)
 * - emptyMessage: string - message when no data
 * - loading: boolean - show loading state
 */
function DataTable({
    data = [],
    columns = [],
    onRowClick = null,
    onEdit = null,
    onDelete = null,
    onView = null,
    searchable = true,
    pagination = true,
    pageSize = 20,
    emptyMessage = 'No data available',
    loading = false
}) {
    const { useState, useMemo } = React;
    
    // State
    const [searchTerm, setSearchTerm] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
    const [currentPage, setCurrentPage] = useState(1);
    
    // Filter data by search term
    const filteredData = useMemo(() => {
        if (!searchTerm) return data;
        
        return data.filter(row => {
            return columns.some(col => {
                const value = row[col.key];
                if (value == null) return false;
                return String(value).toLowerCase().includes(searchTerm.toLowerCase());
            });
        });
    }, [data, searchTerm, columns]);
    
    // Sort data
    const sortedData = useMemo(() => {
        if (!sortConfig.key) return filteredData;
        
        const sorted = [...filteredData].sort((a, b) => {
            const aVal = a[sortConfig.key];
            const bVal = b[sortConfig.key];
            
            if (aVal == null) return 1;
            if (bVal == null) return -1;
            
            if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        });
        
        return sorted;
    }, [filteredData, sortConfig]);
    
    // Paginate data
    const paginatedData = useMemo(() => {
        if (!pagination) return sortedData;
        
        const startIndex = (currentPage - 1) * pageSize;
        return sortedData.slice(startIndex, startIndex + pageSize);
    }, [sortedData, currentPage, pageSize, pagination]);
    
    // Calculate pagination info
    const totalPages = Math.ceil(sortedData.length / pageSize);
    
    // Handle sort
    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };
    
    // Format cell value
    const formatValue = (value, column) => {
        if (column.render) {
            return column.render(value);
        }
        
        if (value == null) return '-';
        
        switch (column.format) {
            case 'date':
                return formatDate(value);
            case 'number':
                return Number(value).toLocaleString();
            case 'currency':
                return new Intl.NumberFormat('en-US', { 
                    style: 'currency', 
                    currency: 'USD' 
                }).format(value);
            default:
                return String(value);
        }
    };
    
    // Show actions column?
    const hasActions = onEdit || onDelete || onView;
    
    if (loading) {
        return React.createElement('div', { className: 'text-center p-lg' },
            React.createElement('div', { className: 'spinner', style: { margin: '0 auto' } }),
            React.createElement('p', { className: 'loading-text' }, 'Loading data...')
        );
    }
    
    return React.createElement('div', { className: 'datatable-wrapper' },
        // Search bar
        searchable && React.createElement('div', { className: 'datatable-search mb-md' },
            React.createElement('input', {
                type: 'text',
                className: 'form-input',
                placeholder: 'Search...',
                value: searchTerm,
                onChange: (e) => {
                    setSearchTerm(e.target.value);
                    setCurrentPage(1); // Reset to first page on search
                }
            })
        ),
        
        // Stats
        sortedData.length > 0 && React.createElement('div', { 
            className: 'datatable-stats mb-md',
            style: { color: 'var(--color-text-muted)', fontSize: '0.875rem' }
        },
            `Showing ${paginatedData.length} of ${sortedData.length} results`,
            searchTerm && ` (filtered from ${data.length} total)`
        ),
        
        // Table
        React.createElement('div', { 
            className: 'datatable-container',
            style: { overflowX: 'auto' }
        },
            React.createElement('table', { className: 'datatable' },
                // Header
                React.createElement('thead', null,
                    React.createElement('tr', null,
                        columns.map((col, idx) =>
                            React.createElement('th', {
                                key: idx,
                                onClick: col.sortable !== false ? () => handleSort(col.key) : undefined,
                                style: { 
                                    cursor: col.sortable !== false ? 'pointer' : 'default',
                                    userSelect: 'none'
                                }
                            },
                                col.label,
                                col.sortable !== false && sortConfig.key === col.key && 
                                    React.createElement('i', {
                                        className: `fas fa-sort-${sortConfig.direction === 'asc' ? 'up' : 'down'}`,
                                        style: { marginLeft: '8px', fontSize: '0.75rem' }
                                    })
                            )
                        ),
                        hasActions && React.createElement('th', { style: { width: '120px' } }, 'Actions')
                    )
                ),
                
                // Body
                React.createElement('tbody', null,
                    paginatedData.length === 0 ?
                        React.createElement('tr', null,
                            React.createElement('td', {
                                colSpan: columns.length + (hasActions ? 1 : 0),
                                style: { textAlign: 'center', padding: '2rem' }
                            },
                                React.createElement('div', { style: { opacity: 0.5 } },
                                    React.createElement('i', { 
                                        className: 'fas fa-inbox',
                                        style: { fontSize: '3rem', marginBottom: '1rem' }
                                    }),
                                    React.createElement('p', null, emptyMessage)
                                )
                            )
                        )
                    :
                        paginatedData.map((row, rowIdx) =>
                            React.createElement('tr', {
                                key: rowIdx,
                                onClick: onRowClick ? () => onRowClick(row) : undefined,
                                style: { cursor: onRowClick ? 'pointer' : 'default' }
                            },
                                columns.map((col, colIdx) =>
                                    React.createElement('td', { key: colIdx },
                                        formatValue(row[col.key], col)
                                    )
                                ),
                                hasActions && React.createElement('td', null,
                                    React.createElement('div', { 
                                        className: 'flex gap-sm',
                                        style: { justifyContent: 'center' }
                                    },
                                        onView && React.createElement('button', {
                                            className: 'btn btn-icon btn-ghost',
                                            onClick: (e) => {
                                                e.stopPropagation();
                                                onView(row);
                                            },
                                            title: 'View'
                                        },
                                            React.createElement('i', { className: 'fas fa-eye' })
                                        ),
                                        onEdit && React.createElement('button', {
                                            className: 'btn btn-icon btn-secondary',
                                            onClick: (e) => {
                                                e.stopPropagation();
                                                onEdit(row);
                                            },
                                            title: 'Edit'
                                        },
                                            React.createElement('i', { className: 'fas fa-edit' })
                                        ),
                                        onDelete && React.createElement('button', {
                                            className: 'btn btn-icon btn-danger',
                                            onClick: (e) => {
                                                e.stopPropagation();
                                                onDelete(row);
                                            },
                                            title: 'Delete'
                                        },
                                            React.createElement('i', { className: 'fas fa-trash' })
                                        )
                                    )
                                )
                            )
                        )
                )
            )
        ),
        
        // Pagination
        pagination && totalPages > 1 && React.createElement('div', { 
            className: 'datatable-pagination mt-md',
            style: { display: 'flex', justifyContent: 'center', gap: '8px', alignItems: 'center' }
        },
            React.createElement('button', {
                className: 'btn btn-ghost',
                disabled: currentPage === 1,
                onClick: () => setCurrentPage(currentPage - 1)
            },
                React.createElement('i', { className: 'fas fa-chevron-left' })
            ),
            
            React.createElement('span', { 
                style: { 
                    padding: '0 16px',
                    color: 'var(--color-text-secondary)'
                }
            },
                `Page ${currentPage} of ${totalPages}`
            ),
            
            React.createElement('button', {
                className: 'btn btn-ghost',
                disabled: currentPage === totalPages,
                onClick: () => setCurrentPage(currentPage + 1)
            },
                React.createElement('i', { className: 'fas fa-chevron-right' })
            )
        )
    );
}

// ============================================
// SHARED UI COMPONENTS
// ============================================

function ApiStatus() {
  const { useEffect, useState } = React;
  const [connected, setConnected] = useState(false);
  const [checking, setChecking] = useState(true);
  useEffect(() => {
    let alive = true;
    const check = async () => {
      try { const ok = await (window.api?.checkHealth?.() || API.request('GET', '/health').then(() => true).catch(() => false));
        if (alive) { setConnected(ok); setChecking(false); }
      } catch { if (alive) { setConnected(false); setChecking(false); } }
    };
    check();
    const t = setInterval(check, 30000);
    return () => { alive = false; clearInterval(t); };
  }, []);
  if (checking) {
    return React.createElement('div', { className: 'status-indicator', style: { background: 'rgba(59,130,246,0.2)' } },
      React.createElement('i', { className: 'fas fa-spinner fa-spin' }),
      React.createElement('span', null, 'Checking API...')
    );
  }
  return React.createElement('div', { className: `status-indicator ${connected ? 'status-online' : 'status-offline'}` },
    React.createElement('span', { className: 'status-dot' }),
    React.createElement('span', null, connected ? 'API Connected' : 'API Offline')
  );
}

function LoadingSpinner({ text = 'Loading...' }) {
  return React.createElement('div', { className: 'text-center', style: { padding: '3rem' } },
    React.createElement('div', { className: 'spinner', style: { margin: '0 auto' } }),
    React.createElement('p', { className: 'loading-text mt-md' }, text)
  );
}

function Badge({ color = 'gray', children }) {
  const colors = {
    blue: { bg: 'rgba(59, 130, 246, 0.15)', text: '#93c5fd', border: 'rgba(59,130,246,0.4)' },
    green: { bg: 'rgba(16, 185, 129, 0.15)', text: '#86efac', border: 'rgba(16,185,129,0.4)' },
    orange: { bg: 'rgba(245, 158, 11, 0.15)', text: '#fcd34d', border: 'rgba(245,158,11,0.4)' },
    gray: { bg: 'rgba(148, 163, 184, 0.15)', text: '#cbd5e1', border: 'rgba(148,163,184,0.4)' },
    red: { bg: 'rgba(239,68,68,0.15)', text: '#fca5a5', border: 'rgba(239,68,68,0.4)' },
  };
  const c = colors[color] || colors.gray;
  return React.createElement('span', {
    style: {
      display: 'inline-block', padding: '2px 10px', borderRadius: 999,
      fontSize: '12px', fontWeight: 700, background: c.bg, color: c.text,
      border: `1px solid ${c.border}`
    }
  }, children);
}

function Header({ title, subtitle, showBackButton = false, right = null }) {
  return React.createElement('header', { className: 'header' },
    React.createElement('div', { className: 'header-content' },
      React.createElement('div', { className: 'header-title' },
        showBackButton && React.createElement('button', {
          className: 'btn btn-ghost', style: { marginRight: '12px' }, onClick: () => history.back()
        }, React.createElement('i', { className: 'fas fa-arrow-left' }), ' Back'),
        React.createElement('i', { className: 'fas fa-satellite-dish neon-cyan' }),
        React.createElement('div', null,
          React.createElement('h1', { className: 'orbitron' }, title || 'ACAD=GIS Tool'),
          subtitle && React.createElement('div', { className: 'header-subtitle' }, subtitle)
        )
      ),
      right || React.createElement(ApiStatus, null)
    )
  );
}

function Modal({ isOpen, onClose, title, footer = null, size = 'medium', children }) {
  if (!isOpen) return null;
  const widths = { small: '420px', medium: '720px', large: '960px' };
  return React.createElement('div', { className: 'modal-overlay', onClick: onClose },
    React.createElement('div', {
      className: 'modal', style: { width: widths[size] || widths.medium }, onClick: (e) => e.stopPropagation()
    },
      React.createElement('div', { className: 'modal-header' },
        React.createElement('h3', { className: 'modal-title' }, title || 'Modal'),
        React.createElement('button', { className: 'btn btn-icon btn-ghost', onClick: onClose },
          React.createElement('i', { className: 'fas fa-times' })
        )
      ),
      React.createElement('div', { className: 'modal-body' }, children),
      React.createElement('div', { className: 'modal-footer' }, footer)
    )
  );
}

// Simple toast manager
var ToastManager = window.ToastManager || (() => {
  let container;
  function ensure() {
    if (container) return container;
    container = document.createElement('div');
    container.style.position = 'fixed';
    container.style.top = '16px';
    container.style.right = '16px';
    container.style.zIndex = 9999;
    document.body.appendChild(container);
    return container;
  }
  function show(message, type = 'info') {
    const c = ensure();
    const colors = {
      info: '#3b82f6', success: '#10b981', warning: '#f59e0b', error: '#ef4444'
    };
    const el = document.createElement('div');
    el.style.marginTop = '8px';
    el.style.padding = '10px 14px';
    el.style.borderRadius = '8px';
    el.style.background = 'rgba(15,23,42,0.95)';
    el.style.border = `1px solid ${colors[type] || colors.info}`;
    el.style.color = 'white';
    el.style.boxShadow = '0 0 20px rgba(59,130,246,0.25)';
    el.textContent = message;
    c.appendChild(el);
    setTimeout(() => {
      el.style.transition = 'opacity .3s ease';
      el.style.opacity = '0';
      setTimeout(() => c.removeChild(el), 320);
    }, 2500);
  }
  return {
    info: (m) => show(m, 'info'),
    success: (m) => show(m, 'success'),
    warning: (m) => show(m, 'warning'),
    error: (m) => show(m, 'error'),
  };
})();

// Expose for inline scripts
window.DataTable = window.DataTable || DataTable;
window.ApiStatus = window.ApiStatus || ApiStatus;
window.LoadingSpinner = window.LoadingSpinner || LoadingSpinner;
window.Badge = window.Badge || Badge;
window.Header = window.Header || Header;
window.Modal = window.Modal || Modal;
window.ToastManager = ToastManager;


// ============================================
// MODAL COMPONENT
// ============================================

/**
 * Modal - Dialog overlay component
 * 
 * Props:
 * - isOpen: boolean - control visibility
 * - onClose: function - called when modal should close
 * - title: string - modal title
 * - children: ReactNode - modal content
 * - footer: ReactNode - modal footer (optional)
 * - size: string - 'small', 'medium', 'large' (default: 'medium')
 */
function Modal({ isOpen, onClose, title, children, footer, size = 'medium' }) {
    if (!isOpen) return null;
    
    const sizes = {
        small: '400px',
        medium: '600px',
        large: '900px'
    };
    
    return React.createElement('div', {
        className: 'modal-overlay',
        onClick: onClose
    },
        React.createElement('div', {
            className: 'modal-content',
            style: { maxWidth: sizes[size] },
            onClick: (e) => e.stopPropagation()
        },
            React.createElement('div', { className: 'modal-header' },
                React.createElement('h2', { className: 'modal-title' }, title),
                React.createElement('button', {
                    className: 'btn btn-icon btn-ghost',
                    onClick: onClose
                },
                    React.createElement('i', { className: 'fas fa-times' })
                )
            ),
            React.createElement('div', { className: 'modal-body' }, children),
            footer && React.createElement('div', { className: 'modal-footer' }, footer)
        )
    );
}

// ============================================
// CONFIRM DIALOG COMPONENT
// ============================================

/**
 * ConfirmDialog - Confirmation prompt
 * 
 * Props:
 * - isOpen: boolean
 * - onClose: function
 * - onConfirm: function
 * - title: string
 * - message: string
 * - confirmText: string (default: 'Confirm')
 * - cancelText: string (default: 'Cancel')
 * - danger: boolean - use danger styling
 */
function ConfirmDialog({
    isOpen,
    onClose,
    onConfirm,
    title = 'Confirm',
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    danger = false
}) {
    const handleConfirm = () => {
        onConfirm();
        onClose();
    };
    
    return React.createElement(Modal, {
        isOpen,
        onClose,
        title,
        size: 'small',
        footer: React.createElement(React.Fragment, null,
            React.createElement('button', {
                className: 'btn btn-ghost',
                onClick: onClose
            }, cancelText),
            React.createElement('button', {
                className: danger ? 'btn btn-danger' : 'btn btn-primary',
                onClick: handleConfirm
            }, confirmText)
        )
    },
        React.createElement('p', null, message)
    );
}

// ============================================
// LOADING SPINNER COMPONENT
// ============================================

/**
 * LoadingSpinner - Loading indicator
 * 
 * Props:
 * - text: string - optional loading message
 * - overlay: boolean - show as full-screen overlay
 */
function LoadingSpinner({ text = 'Loading...', overlay = false }) {
    const spinner = React.createElement('div', { 
        className: 'text-center',
        style: { padding: '2rem' }
    },
        React.createElement('div', { 
            className: 'spinner',
            style: { margin: '0 auto' }
        }),
        text && React.createElement('p', { 
            className: 'loading-text',
            style: { marginTop: '1rem' }
        }, text)
    );
    
    if (overlay) {
        return React.createElement('div', { className: 'loading-overlay' }, spinner);
    }
    
    return spinner;
}

// ============================================
// ALERT COMPONENT
// ============================================

/**
 * Alert - Message box component
 * 
 * Props:
 * - type: string - 'success', 'error', 'warning', 'info'
 * - message: string
 * - onClose: function (optional)
 */
function Alert({ type = 'info', message, onClose }) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    return React.createElement('div', { className: `alert alert-${type}` },
        React.createElement('i', { className: `fas ${icons[type]}` }),
        React.createElement('span', { style: { flex: 1 } }, message),
        onClose && React.createElement('button', {
            className: 'btn btn-icon btn-ghost',
            onClick: onClose,
            style: { padding: '4px', width: '24px', height: '24px' }
        },
            React.createElement('i', { className: 'fas fa-times' })
        )
    );
}

// ============================================
// EMPTY STATE COMPONENT
// ============================================

/**
 * EmptyState - No data placeholder
 * 
 * Props:
 * - icon: string - Font Awesome icon name
 * - title: string
 * - message: string
 * - action: ReactNode - optional action button
 */
function EmptyState({ icon = 'inbox', title, message, action }) {
    return React.createElement('div', { 
        className: 'text-center',
        style: { padding: '4rem 2rem' }
    },
        React.createElement('i', {
            className: `fas fa-${icon}`,
            style: { 
                fontSize: '4rem',
                color: 'var(--color-text-muted)',
                marginBottom: '1rem'
            }
        }),
        title && React.createElement('h3', {
            style: { 
                fontSize: '1.5rem',
                marginBottom: '0.5rem',
                color: 'var(--color-text-secondary)'
            }
        }, title),
        message && React.createElement('p', {
            style: { 
                color: 'var(--color-text-muted)',
                marginBottom: '2rem'
            }
        }, message),
        action
    );
}

// ============================================
// HEADER COMPONENT
// ============================================

/**
 * Header - Page header component
 * 
 * Props:
 * - title: string
 * - subtitle: string (optional)
 * - showBackButton: boolean
 * - backUrl: string (default: '../tool_launcher.html')
 * - rightContent: ReactNode (optional)
 */
function Header({ 
    title, 
    subtitle, 
    showBackButton = false, 
    backUrl = '../tool_launcher.html',
    rightContent 
}) {
    return React.createElement('header', { className: 'header' },
        React.createElement('div', { className: 'header-content' },
            React.createElement('div', { className: 'header-title' },
                showBackButton && React.createElement('a', {
                    href: backUrl,
                    className: 'btn btn-icon btn-ghost',
                    title: 'Back to Tool Launcher'
                },
                    React.createElement('i', { className: 'fas fa-arrow-left' })
                ),
                React.createElement('div', null,
                    React.createElement('h1', { className: 'orbitron neon-blue' }, title),
                    subtitle && React.createElement('p', { className: 'header-subtitle' }, subtitle)
                )
            ),
            rightContent && React.createElement('div', null, rightContent)
        )
    );
}

// ============================================
// FOOTER COMPONENT
// ============================================

/**
 * Footer - Page footer component
 */
function Footer() {
    return React.createElement('footer', { className: 'footer' },
        React.createElement('p', null,
            'ACAD=GIS © 2025 | Mission Control Interface'
        )
    );
}

// ============================================
// STAT CARD COMPONENT
// ============================================

/**
 * StatCard - Statistics display card
 * 
 * Props:
 * - icon: string - Font Awesome icon name
 * - label: string
 * - value: number/string
 * - color: string - 'blue', 'green', 'orange', 'purple', 'red'
 */
function StatCard({ icon, label, value, color = 'blue' }) {
    const colors = {
        blue: 'var(--color-accent-blue)',
        green: 'var(--color-accent-green)',
        orange: 'var(--color-accent-orange)',
        red: 'var(--color-accent-red)',
        cyan: 'var(--color-accent-cyan)'
    };
    
    return React.createElement('div', { className: 'card' },
        React.createElement('div', { 
            className: 'flex items-center gap-md'
        },
            React.createElement('i', {
                className: `fas fa-${icon}`,
                style: { 
                    fontSize: '2.5rem',
                    color: colors[color]
                }
            }),
            React.createElement('div', null,
                React.createElement('div', {
                    style: {
                        fontSize: '2rem',
                        fontWeight: 700,
                        color: 'var(--color-text-primary)'
                    }
                }, value),
                React.createElement('div', {
                    style: {
                        fontSize: '0.875rem',
                        color: 'var(--color-text-muted)'
                    }
                }, label)
            )
        )
    );
}

// ============================================
// SEARCH BAR COMPONENT
// ============================================

/**
 * SearchBar - Search input with clear button
 * 
 * Props:
 * - value: string
 * - onChange: function
 * - onClear: function
 * - placeholder: string
 */
function SearchBar({ value, onChange, onClear, placeholder = 'Search...' }) {
    return React.createElement('div', { 
        style: { position: 'relative' }
    },
        React.createElement('input', {
            type: 'text',
            className: 'form-input',
            placeholder,
            value,
            onChange: (e) => onChange(e.target.value),
            style: { paddingRight: '40px' }
        }),
        value && React.createElement('button', {
            className: 'btn btn-icon btn-ghost',
            onClick: onClear,
            style: {
                position: 'absolute',
                right: '4px',
                top: '50%',
                transform: 'translateY(-50%)'
            }
        },
            React.createElement('i', { className: 'fas fa-times' })
        )
    );
}

// ============================================
// BADGE COMPONENT
// ============================================

/**
 * Badge - Small status indicator
 * 
 * Props:
 * - children: string - badge text
 * - color: string - 'blue', 'green', 'orange', 'red', 'gray'
 * - icon: string - Font Awesome icon name (optional)
 */
function Badge({ children, color = 'blue', icon }) {
    const colors = {
        blue: { bg: 'rgba(59, 130, 246, 0.2)', border: 'rgba(59, 130, 246, 0.5)', text: '#93c5fd' },
        green: { bg: 'rgba(16, 185, 129, 0.2)', border: 'rgba(16, 185, 129, 0.5)', text: '#6ee7b7' },
        orange: { bg: 'rgba(245, 158, 11, 0.2)', border: 'rgba(245, 158, 11, 0.5)', text: '#fcd34d' },
        red: { bg: 'rgba(239, 68, 68, 0.2)', border: 'rgba(239, 68, 68, 0.5)', text: '#fca5a5' },
        gray: { bg: 'rgba(148, 163, 184, 0.2)', border: 'rgba(148, 163, 184, 0.5)', text: '#cbd5e1' }
    };
    
    const style = colors[color];
    
    return React.createElement('span', {
        style: {
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 12px',
            borderRadius: '999px',
            fontSize: '0.75rem',
            fontWeight: 600,
            background: style.bg,
            border: `1px solid ${style.border}`,
            color: style.text
        }
    },
        icon && React.createElement('i', { className: `fas fa-${icon}` }),
        children
    );
}

// ============================================
// TOAST MANAGER
// ============================================

/**
 * ToastManager - Global toast notification system (legacy section)
 * Guarded to avoid redeclaration when the file is loaded multiple times.
 */
if (!window.ToastManager) { window.ToastManager = {
    container: null,
    
    init() {
        if (this.container) return;
        
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        `;
        document.body.appendChild(this.container);
    },
    
    show(message, type = 'info', duration = 3000) {
        this.init();
        
        const toast = document.createElement('div');
        toast.className = `alert alert-${type}`;
        toast.style.cssText = `
            min-width: 300px;
            animation: slideInRight 0.3s ease;
        `;
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        toast.innerHTML = `
            <i class="fas ${icons[type]}"></i>
            <span style="flex: 1;">${message}</span>
            <button class="btn btn-icon btn-ghost" style="padding: 4px; width: 24px; height: 24px;">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        const closeBtn = toast.querySelector('button');
        closeBtn.onclick = () => this.remove(toast);
        
        this.container.appendChild(toast);
        
        if (duration > 0) {
            setTimeout(() => this.remove(toast), duration);
        }
    },
    
    remove(toast) {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    },
    
    success(message, duration) {
        this.show(message, 'success', duration);
    },
    
    error(message, duration) {
        this.show(message, 'error', duration);
    },
    
    warning(message, duration) {
        this.show(message, 'warning', duration);
    },
    
    info(message, duration) {
        this.show(message, 'info', duration);
    }
}; }

// Add animation CSS if not already present
if (!document.getElementById('toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

console.log('✅ ACAD=GIS React components loaded');
console.log('📦 Available components ready');
