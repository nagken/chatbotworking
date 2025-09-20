/**
 * Interactive SQL Results Table
 * Handles column sorting and global search functionality
 */

class InteractiveTable {
    constructor(container) {
        this.container = container;
        this.table = container.querySelector('.sql-data-table');
        this.headers = container.querySelectorAll('.table-header');
        this.rows = Array.from(container.querySelectorAll('.table-row'));
        this.originalOrder = [...this.rows];
        this.currentSort = { column: null, direction: null };
        this.searchTerm = '';
        
        // Debug logging
        console.log('🔧 InteractiveTable: Initializing for container with', this.rows.length, 'rows');
        
        this.init();
    }
    
    init() {
        // Ensure we don't interfere with chart rendering
        if (this.container.closest('.message-content')?.querySelector('.chart-display')) {
            // If there's a chart in the same message, delay initialization slightly
            setTimeout(() => {
                this.addTableControls();
                this.setupSorting();
                this.setupSearch();
            }, 200);
        } else {
            this.addTableControls();
            this.setupSorting();
            this.setupSearch();
        }
    }
    
    addTableControls() {
        // Check if controls already exist
        if (this.container.querySelector('.table-controls')) {
            return;
        }
        
        // Create table controls section
        const controlsHtml = `
            <div class="table-controls">
                <div class="global-search-container">
                    <i class="fas fa-search search-icon"></i>
                    <input type="text" 
                           class="global-search" 
                           placeholder="Search across all data..."
                           autocomplete="off">
                    <button class="search-clear" type="button" title="Clear search">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="search-results-info">
                    <span class="visible-rows">${this.rows.length}</span> of 
                    <span class="total-rows">${this.rows.length}</span> rows
                </div>
            </div>
        `;
        
        // Insert controls after results summary but before table
        const resultsummary = this.container.querySelector('.results-summary');
        const tableContainer = this.container.querySelector('.data-table-container');
        
        if (resultsummary && tableContainer) {
            resultsummary.insertAdjacentHTML('afterend', controlsHtml);
        } else {
            // Fallback: insert after query info but before table
            const queryInfo = this.container.querySelector('.sql-query-info');
            if (queryInfo && tableContainer) {
                queryInfo.insertAdjacentHTML('afterend', controlsHtml);
            }
        }
    }
    
    setupSorting() {
        this.headers.forEach((header, index) => {
            // Skip if already setup
            if (header.classList.contains('sortable')) {
                return;
            }
            
            header.classList.add('sortable');
            
            // Check if sort indicator already exists
            if (!header.querySelector('.sort-indicator')) {
                header.innerHTML += '<span class="sort-indicator"></span>';
            }
            
            header.style.cursor = 'pointer';
            
            // Remove any existing click listeners to prevent duplicates
            header.removeEventListener('click', header._sortHandler);
            
            // Create and store the handler
            header._sortHandler = (e) => {
                e.preventDefault();
                this.sortColumn(index, header);
            };
            
            header.addEventListener('click', header._sortHandler);
        });
    }
    
    setupSearch() {
        const searchInput = this.container.querySelector('.global-search');
        const clearButton = this.container.querySelector('.search-clear');
        
        if (!searchInput) return;
        
        // Debounced search
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });
        
        // Clear search
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                searchInput.value = '';
                this.performSearch('');
                searchInput.focus();
            });
        }
        
        // Handle Enter key
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch(e.target.value);
            }
        });
    }
    
    sortColumn(columnIndex, headerElement) {
        // Remove sort classes from all headers
        this.headers.forEach(h => {
            h.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Determine sort direction
        let direction = 'asc';
        if (this.currentSort.column === columnIndex) {
            if (this.currentSort.direction === 'asc') {
                direction = 'desc';
            } else if (this.currentSort.direction === 'desc') {
                // Third click resets to original order
                this.resetSort();
                return;
            }
        }
        
        // Update current sort state
        this.currentSort = { column: columnIndex, direction };
        headerElement.classList.add(`sort-${direction}`);
        
        // Perform sort
        this.sortRows(columnIndex, direction);
    }
    
    sortRows(columnIndex, direction) {
        const tbody = this.table.querySelector('tbody');
        // Always get fresh rows from DOM instead of using cached this.rows
        const currentRows = Array.from(this.container.querySelectorAll('.table-row'));
        const visibleRows = currentRows.filter(row => !row.classList.contains('search-hidden'));
        
        // Get data type for smart sorting
        const sampleCell = visibleRows[0]?.querySelectorAll('.table-cell')[columnIndex];
        const dataType = this.detectDataType(sampleCell?.textContent.trim());
        
        // Sort rows
        const sortedRows = [...visibleRows].sort((a, b) => {
            const aCell = a.querySelectorAll('.table-cell')[columnIndex];
            const bCell = b.querySelectorAll('.table-cell')[columnIndex];
            
            let aValue = aCell?.textContent.trim() || '';
            let bValue = bCell?.textContent.trim() || '';
            
            // Handle null/empty values
            if (!aValue && !bValue) return 0;
            if (!aValue) return direction === 'asc' ? 1 : -1;
            if (!bValue) return direction === 'asc' ? -1 : 1;
            
            // Sort based on data type
            let comparison = 0;
            switch (dataType) {
                case 'number':
                    const aNum = parseFloat(aValue.replace(/[,$%]/g, ''));
                    const bNum = parseFloat(bValue.replace(/[,$%]/g, ''));
                    comparison = aNum - bNum;
                    break;
                case 'date':
                    const aDate = new Date(aValue);
                    const bDate = new Date(bValue);
                    comparison = aDate - bDate;
                    break;
                default:
                    comparison = aValue.localeCompare(bValue, undefined, { 
                        numeric: true, 
                        sensitivity: 'base' 
                    });
            }
            
            return direction === 'asc' ? comparison : -comparison;
        });
        
        // Reorder DOM elements
        sortedRows.forEach(row => tbody.appendChild(row));
        
        // Update row classes for alternating colors
        this.updateRowClasses();
    }
    
    resetSort() {
        // Remove sort classes from fresh headers
        const currentHeaders = this.container.querySelectorAll('.table-header');
        currentHeaders.forEach(h => {
            h.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Reset sort state
        this.currentSort = { column: null, direction: null };
        
        // Restore original order for visible rows
        const tbody = this.table.querySelector('tbody');
        const currentRows = Array.from(this.container.querySelectorAll('.table-row'));
        const visibleRows = currentRows.filter(row => !row.classList.contains('search-hidden'));
        
        // Find original positions of visible rows using fresh original order
        const freshOriginalOrder = [...this.originalOrder];
        const originalVisible = freshOriginalOrder.filter(row => 
            !row.classList.contains('search-hidden') && row.parentNode // Ensure row still exists in DOM
        );
        
        originalVisible.forEach(row => tbody.appendChild(row));
        this.updateRowClasses();
    }
    
    performSearch(searchTerm) {
        this.searchTerm = searchTerm.toLowerCase().trim();
        let visibleCount = 0;
        
        // Always get fresh rows from DOM
        const currentRows = Array.from(this.container.querySelectorAll('.table-row'));
        currentRows.forEach(row => {
            if (!searchTerm) {
                // Show all rows if search is empty
                row.classList.remove('search-hidden');
                this.clearHighlights(row);
                visibleCount++;
            } else {
                // Check if any cell contains search term
                const cells = row.querySelectorAll('.table-cell');
                let rowMatches = false;
                
                cells.forEach(cell => {
                    const cellText = cell.textContent.toLowerCase();
                    this.clearHighlights(cell);
                    
                    if (cellText.includes(this.searchTerm)) {
                        rowMatches = true;
                        this.highlightText(cell, this.searchTerm);
                    }
                });
                
                if (rowMatches) {
                    row.classList.remove('search-hidden');
                    visibleCount++;
                } else {
                    row.classList.add('search-hidden');
                }
            }
        });
        
        // Update search results info
        this.updateSearchInfo(visibleCount);
        
        // Update row classes for visible rows
        this.updateRowClasses();
        
        // Re-sort if there's an active sort
        if (this.currentSort.column !== null) {
            this.sortRows(this.currentSort.column, this.currentSort.direction);
        }
    }
    
    highlightText(element, searchTerm) {
        const text = element.textContent;
        const regex = new RegExp(`(${this.escapeRegex(searchTerm)})`, 'gi');
        const highlightedText = text.replace(regex, '<span class="search-highlight">$1</span>');
        element.innerHTML = highlightedText;
    }
    
    clearHighlights(element) {
        const highlights = element.querySelectorAll('.search-highlight');
        highlights.forEach(highlight => {
            const parent = highlight.parentNode;
            parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
            parent.normalize();
        });
    }
    
    updateSearchInfo(visibleCount) {
        const visibleSpan = this.container.querySelector('.visible-rows');
        const totalSpan = this.container.querySelector('.total-rows');
        
        // Get fresh row count from DOM
        const currentRowCount = this.container.querySelectorAll('.table-row').length;
        
        if (visibleSpan) visibleSpan.textContent = visibleCount;
        if (totalSpan) totalSpan.textContent = currentRowCount;
    }
    
    updateRowClasses() {
        // Always get fresh rows from DOM
        const currentRows = Array.from(this.container.querySelectorAll('.table-row'));
        const visibleRows = currentRows.filter(row => !row.classList.contains('search-hidden'));
        visibleRows.forEach((row, index) => {
            row.classList.remove('even', 'odd');
            row.classList.add(index % 2 === 0 ? 'even' : 'odd');
        });
    }
    
    detectDataType(value) {
        if (!value) return 'text';
        
        // Check for number (including currency, percentages)
        if (/^[+-]?[\d,]+\.?\d*[%$]?$/.test(value.replace(/\s/g, ''))) {
            return 'number';
        }
        
        // Check for date
        const dateValue = new Date(value);
        if (!isNaN(dateValue.getTime()) && value.length > 4) {
            return 'date';
        }
        
        return 'text';
    }
    
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    // Public method to refresh the table (useful for dynamically loaded content)
    refresh() {
        // Update cached DOM elements
        this.table = this.container.querySelector('.sql-data-table');
        this.headers = this.container.querySelectorAll('.table-header');
        this.rows = Array.from(this.container.querySelectorAll('.table-row'));
        this.originalOrder = [...this.rows];
        
        // Re-setup sorting for any new headers (but don't duplicate existing)
        this.setupSorting();
        
        // Update search info
        this.updateSearchInfo(this.rows.length);
    }
}

// Auto-initialize interactive tables when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeInteractiveTables();
});

// Function to initialize all SQL result tables
function initializeInteractiveTables() {
    const sqlContainers = document.querySelectorAll('.sql-results-container');
    sqlContainers.forEach(container => {
        // Check if already initialized
        if (!container.dataset.interactive) {
            const tableInstance = new InteractiveTable(container);
            container.interactiveTableInstance = tableInstance; // Store instance reference
            container.dataset.interactive = 'true';
        } else if (container.interactiveTableInstance) {
            // If already initialized, just refresh the existing instance
            container.interactiveTableInstance.refresh();
        }
    });
}

// Export for use in other scripts
window.InteractiveTable = InteractiveTable;
window.initializeInteractiveTables = initializeInteractiveTables; 