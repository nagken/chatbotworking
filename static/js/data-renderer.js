/**
 * Data Renderer for PSS Knowledge Assist
 * Modular data table and SQL rendering system extracted from script.js
 * Handles SQL query display, data tables, and export functionality
 */

class DataRenderer {
    constructor() {
        this.currentData = null; // Store current data for export
    }

    /**
     * Expand SQL results to show all rows
     */
    expandResults(button) {
        const container = button.closest('.sql-results-container');
        const tbody = container.querySelector('tbody');
        const pagination = container.querySelector('.table-pagination');
        
        // Get the complete dataset from the stored data attribute
        // Try both fullData and full-data attribute names
        const fullDataStr = container.dataset.fullData || container.getAttribute('data-full-data') || '[]';
        const fullData = JSON.parse(fullDataStr);
        const columns = fullData.length > 0 ? Object.keys(fullData[0]) : [];
        
        // Add remaining rows to table (rows 6 and beyond)
        const remainingRows = fullData.slice(5);
        remainingRows.forEach((row, index) => {
            const tr = document.createElement('tr');
            tr.className = `table-row ${(index + 5) % 2 === 0 ? 'even' : 'odd'}`;
            tr.innerHTML = columns.map(col => `<td class="table-cell">${this.escapeHtml(String(row[col] || '')) || '<span class="null-value">NULL</span>'}</td>`).join('');
            tbody.appendChild(tr);
        });
        
        // Update pagination info
        pagination.innerHTML = `
            <div class="pagination-info">
                Showing all ${fullData.length} rows
            </div>
            <button class="pagination-btn collapse-btn" onclick="collapseSQLResults(this)">
                <i class="fas fa-chevron-up"></i>
                Show less
            </button>
            `;
        
        // Refresh interactive table to handle new rows
        requestAnimationFrame(() => {
            setTimeout(() => {
                if (window.initializeInteractiveTables) {
                    window.initializeInteractiveTables();
                }
            }, 50);
        });
    }

    /**
     * Collapse SQL results back to first 5 rows
     */
    collapseResults(button) {
        const container = button.closest('.sql-results-container');
        const tbody = container.querySelector('tbody');
        const pagination = container.querySelector('.table-pagination');
        
        // Get the complete dataset from the stored data attribute
        const fullData = JSON.parse(container.dataset.fullData || '[]');
        
        // Remove rows beyond the first 5
        const rows = tbody.querySelectorAll('tr');
        for (let i = rows.length - 1; i >= 5; i--) {
            rows[i].remove();
        }
        
        // Restore original pagination
        pagination.innerHTML = `
            <button class="pagination-btn" onclick="expandSQLResults(this)">
                <i class="fas fa-chevron-down"></i>
                Show ${fullData.length - 5} more rows
            </button>
            <div class="pagination-info">
                Showing 1-5 of ${fullData.length} rows
            </div>
            `;
        
        // Refresh interactive table to handle removed rows
        requestAnimationFrame(() => {
            setTimeout(() => {
                if (window.initializeInteractiveTables) {
                    window.initializeInteractiveTables();
                }
            }, 50);
        });
    }

    /**
     * Export SQL data as CSV
     */
    exportData(button) {
        const container = button.closest('.sql-results-container');
        const data = JSON.parse(container.dataset.fullData);
        const columns = data.length > 0 ? Object.keys(data[0]) : [];
        
        // Create CSV content
        const csvContent = [
            columns.join(','), 
            ...data.map(row => Object.values(row).map(cell => `"${String(cell || '')}"`).join(','))
        ].join('\n');
        
        // Create and trigger download
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'data_export.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        // Show success message
        this.showSuccessMessage('Data exported successfully!');
    }

    /**
     * Copy SQL query to clipboard
     */
    copyQuery(button) {
        const query = button.closest('.message-content')?.querySelector('.sql-query-text code')?.textContent;
        if (!query) {
            console.error('No query query text found to copy');
            return;
        }
        navigator.clipboard.writeText(query).then(() => {
            this.showSuccessMessage('SQL query copied to clipboard!');
        }).catch(() => {
            this.showErrorMessage('Failed to copy query. Please try again.');
        });
    }


    /**
     * Initialize interactive table features
     */
    initializeInteractiveTables() {
        if (window.initializeInteractiveTables) {
            requestAnimationFrame(() => {
                setTimeout(() => {
                    window.initializeInteractiveTables();
                }, 50);
            });
        }
    }

    /**
     * Show success message
     */
    showSuccessMessage(message) {
        if (typeof window.showValidationMessage === 'function') {
            window.showValidationMessage(message, 'success');
        } else {
            console.log('✅', message);
        }
    }

    /**
     * Show error message
     */
    showErrorMessage(message) {
        if (typeof window.showValidationMessage === 'function') {
            window.showValidationMessage(message, 'error');
        } else {
            console.error('❌', message);
        }
    }


    /**
     * Utility: Escape HTML
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return String(text);
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Utility: Escape text for JavaScript string
     */
    escapeForJS(text) {
        return text.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
    }
}

// =============================================================================
// GLOBAL INSTANCE AND EXPORTS
// =============================================================================

// Create global instance
window.dataRenderer = new DataRenderer();


window.expandSQLResults = function(button) {
    return window.dataRenderer.expandResults(button);
};

window.collapseSQLResults = function(button) {
    return window.dataRenderer.collapseResults(button);
};

window.exportSQLData = function(button) {
    return window.dataRenderer.exportData(button);
};

window.copySQLQuery = function(button) {
    return window.dataRenderer.copyQuery(button);
};

console.log('✅ Data Renderer module loaded');
