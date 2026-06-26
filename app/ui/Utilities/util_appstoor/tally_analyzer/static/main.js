// Tally DayBook Dashboard Frontend Logic

// Global chart variables
let salesPurchaseChartObj = null;
let receiptPaymentChartObj = null;
let particularTrendChartObj = null;
let voucherTypeTrendChartObj = null;

// Pagination and filtering state
let currentPage = 1;
const pageSize = 20;
let totalRecords = 0;
let totalFiltered = 0;

// Currency formatter
const formatCurrency = (value) => {
    if (value === null || value === undefined) return '₹0.00';
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 2
    }).format(value);
};

// Toast notification helper
const showToast = (message, type = 'info') => {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let iconClass = 'fa-info-circle';
    if (type === 'success') iconClass = 'fa-circle-check';
    if (type === 'error') iconClass = 'fa-triangle-exclamation';
    if (type === 'warning') iconClass = 'fa-exclamation-circle';
    
    toast.innerHTML = `
        <i class="fa-solid ${iconClass}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideUp 0.3s reverse forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
};

// API Fetch wrapper
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API Call failed for ${url}:`, error);
        showToast(error.message, 'error');
        return null;
    }
}

// Initial status check
async function checkStatus() {
    const res = await apiCall('/api/status');
    if (res && res.status === 'success') {
        const pathDisplay = document.getElementById('file-path-display');
        const refreshBtn = document.getElementById('btn-refresh');
        const statusDot = document.getElementById('db-status-dot');
        const statusText = document.getElementById('db-status-text');
        const recordsCount = document.getElementById('db-records-count');
        const lastRefresh = document.getElementById('db-last-refresh');

        if (res.file_path) {
            pathDisplay.textContent = res.file_path;
            pathDisplay.classList.add('has-path');
            refreshBtn.disabled = false;
        } else {
            pathDisplay.textContent = "No Excel file selected. Click 'Browse' to select Tally.xlsx";
            pathDisplay.classList.remove('has-path');
            refreshBtn.disabled = true;
        }

        if (res.row_count > 0) {
            statusDot.className = "status-dot"; // emerald
            statusText.textContent = "SQLite: Connected";
            recordsCount.textContent = `${res.row_count} Records`;
            lastRefresh.textContent = `Last Sync: ${res.last_refresh || 'Unknown'}`;
        } else {
            statusDot.className = "status-dot stale"; // amber
            statusText.textContent = "SQLite: Empty Database";
            recordsCount.textContent = "0 Records";
            lastRefresh.textContent = "Last Sync: Never";
        }
    }
}

// Select Excel File
document.getElementById('btn-browse').addEventListener('click', async () => {
    showToast('Opening file picker...', 'info');
    const res = await apiCall('/api/select_file', { method: 'POST' });
    if (res && res.status === 'success') {
        if (res.file_path) {
            showToast('Excel file selected successfully!', 'success');
            await checkStatus();
        } else {
            showToast('File selection cancelled.', 'warning');
        }
    }
});

// Refresh Data from Excel to DB
document.getElementById('btn-refresh').addEventListener('click', async () => {
    const btn = document.getElementById('btn-refresh');
    const origHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Syncing...`;
    
    showToast('Reading Excel and syncing SQLite database. Please wait...', 'info');
    
    const res = await apiCall('/api/refresh', { method: 'POST' });
    
    btn.disabled = false;
    btn.innerHTML = origHtml;
    
    if (res && res.status === 'success') {
        showToast(`Sync complete! Added: ${res.added}, Updated: ${res.updated}, Deleted: ${res.deleted}`, 'success');
        await checkStatus();
        await loadDashboardData();
    }
});

// Load Dashboard Data (KPIs, Charts, Table)
async function loadDashboardData() {
    // 1. Load data table & KPIs
    await loadTableData();
    // 2. Load general trends
    await loadTrendCharts();
    // 3. Load particulars dropdown
    await loadParticularsDropdown();
}

// Load Table Data with search, filter and pagination
async function loadTableData() {
    const search = document.getElementById('table-search').value;
    const voucherType = document.getElementById('filter-voucher-type').value;
    
    const url = `/api/data?page=${currentPage}&page_size=${pageSize}&search=${encodeURIComponent(search)}&voucher_type=${encodeURIComponent(voucherType)}`;
    const res = await apiCall(url);
    
    if (res && res.status === 'success') {
        // Update Table
        const tbody = document.getElementById('table-body');
        tbody.innerHTML = '';
        
        if (res.data.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                        No transactions found matching the criteria.
                    </td>
                </tr>
            `;
        } else {
            res.data.forEach(row => {
                const tr = document.createElement('tr');
                
                // Determine active voucher amount
                let amt = 0;
                let amtClass = 'amt-neutral';
                
                if (row.voucher_type === 'Sales' || row.voucher_type === 'Receipt' || row.voucher_type === 'Credit Note') {
                    amtClass = 'amt-credit';
                } else if (row.voucher_type === 'Purchase' || row.voucher_type === 'Payment' || row.voucher_type === 'Debit Note') {
                    amtClass = 'amt-debit';
                }
                
                // Fetch the actual amount from non-null columns or calculated amount
                amt = row.amount || 0;
                
                // Format Date
                let formattedDate = row.date;
                if (row.date) {
                    const d = new Date(row.date);
                    if (!isNaN(d.getTime())) {
                        formattedDate = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
                    }
                }
                
                // Badge for voucher type
                let badgeClass = 'badge-other';
                const vt = (row.voucher_type || '').toLowerCase();
                if (vt === 'sales') badgeClass = 'badge-sales';
                else if (vt === 'purchase') badgeClass = 'badge-purchase';
                else if (vt === 'payment') badgeClass = 'badge-payment';
                else if (vt === 'receipt') badgeClass = 'badge-receipt';
                else if (vt === 'journal') badgeClass = 'badge-journal';
                
                tr.innerHTML = `
                    <td>${formattedDate}</td>
                    <td><strong>${row.particular || '-'}</strong></td>
                    <td><code>${row.voucher_no || '-'}</code></td>
                    <td><span class="badge ${badgeClass}">${row.voucher_type || '-'}</span></td>
                    <td class="col-amount ${amtClass}">${formatCurrency(amt)}</td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        // Update stats summary text
        totalRecords = res.total_records;
        totalFiltered = res.total_filtered;
        const start = totalFiltered === 0 ? 0 : (currentPage - 1) * pageSize + 1;
        const end = Math.min(currentPage * pageSize, totalFiltered);
        document.getElementById('table-stats').textContent = `Showing ${start} to ${end} of ${totalFiltered} entries (filtered from ${totalRecords} total)`;
        
        // Update pagination buttons
        document.getElementById('page-num').textContent = `Page ${currentPage} of ${res.pages || 1}`;
        document.getElementById('btn-prev').disabled = currentPage <= 1;
        document.getElementById('btn-next').disabled = currentPage >= res.pages;
        
        // Update KPI values
        if (res.stats) {
            document.getElementById('stat-sales-val').textContent = formatCurrency(res.stats.sales);
            document.getElementById('stat-purchases-val').textContent = formatCurrency(res.stats.purchase);
            document.getElementById('stat-receipts-val').textContent = formatCurrency(res.stats.receipt);
            document.getElementById('stat-payments-val').textContent = formatCurrency(res.stats.payment);
        }
    }
}

// Load Particulars dropdown list
async function loadParticularsDropdown() {
    const res = await apiCall('/api/particulars');
    if (res && res.status === 'success') {
        const select = document.getElementById('select-particular');
        
        // Store current selection if any
        const currentSel = select.value;
        
        select.innerHTML = '<option value="">-- Select Particular --</option>';
        res.data.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p;
            opt.textContent = p;
            select.appendChild(opt);
        });
        
        // Re-select if it still exists
        if (currentSel && res.data.includes(currentSel)) {
            select.value = currentSel;
        } else if (res.data.length > 0 && !select.value) {
            // Select first option by default
            select.selectedIndex = 1;
            updateParticularTrend();
        }
    }
}

// Load static general charts (Sales/Purchases and Receipts/Payments)
async function loadTrendCharts() {
    const res = await apiCall('/api/trends');
    if (res && res.status === 'success') {
        const months = res.cashflow.months;
        const sales = res.cashflow.sales;
        const purchases = res.cashflow.purchases;
        
        const receipts = res.cashflow.receipts;
        const payments = res.cashflow.payments;
        
        // Sales vs Purchases Chart
        if (salesPurchaseChartObj) salesPurchaseChartObj.destroy();
        const ctx1 = document.getElementById('salesPurchaseChart').getContext('2d');
        salesPurchaseChartObj = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Sales (Income)',
                        data: sales,
                        backgroundColor: 'rgba(16, 185, 129, 0.6)',
                        borderColor: '#10b981',
                        borderWidth: 1
                    },
                    {
                        label: 'Purchase (Expense)',
                        data: purchases,
                        backgroundColor: 'rgba(244, 63, 94, 0.6)',
                        borderColor: '#f43f5e',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#9ca3af' } },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#9ca3af', callback: v => '₹' + v.toLocaleString('en-IN') }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
        
        // Receipts vs Payments Chart
        if (receiptPaymentChartObj) receiptPaymentChartObj.destroy();
        const ctx2 = document.getElementById('receiptPaymentChart').getContext('2d');
        receiptPaymentChartObj = new Chart(ctx2, {
            type: 'line',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Receipts',
                        data: receipts,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Payments',
                        data: payments,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        fill: true,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#9ca3af' } },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#9ca3af', callback: v => '₹' + v.toLocaleString('en-IN') }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }
}

// Update Particular Trend Chart
async function updateParticularTrend() {
    const pVal = document.getElementById('select-particular').value;
    if (!pVal) {
        if (particularTrendChartObj) particularTrendChartObj.destroy();
        return;
    }
    
    const res = await apiCall(`/api/trends?particular=${encodeURIComponent(pVal)}`);
    if (res && res.status === 'success') {
        const months = res.particular.months;
        const values = res.particular.values;
        const counts = res.particular.counts;
        
        if (particularTrendChartObj) particularTrendChartObj.destroy();
        const ctx3 = document.getElementById('particularTrendChart').getContext('2d');
        particularTrendChartObj = new Chart(ctx3, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Total Value (₹)',
                        data: values,
                        backgroundColor: 'rgba(139, 92, 246, 0.6)',
                        borderColor: '#8b5cf6',
                        borderWidth: 1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Transaction Count',
                        data: counts,
                        type: 'line',
                        borderColor: '#3b82f6',
                        backgroundColor: '#3b82f6',
                        borderWidth: 2,
                        pointRadius: 4,
                        yAxisID: 'yCount',
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#9ca3af' } },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.dataset.yAxisID === 'y') {
                                    return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                                }
                                return context.dataset.label + ': ' + context.parsed.y;
                            }
                        }
                    }
                },
                scales: {
                    x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        ticks: { color: '#9ca3af', callback: v => '₹' + v.toLocaleString('en-IN') },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    },
                    yCount: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: { color: '#9ca3af', stepSize: 1 },
                        grid: { drawOnChartArea: false } // Only keep grid lines for left axis
                    }
                }
            }
        });
    }
}

// Update Voucher Type Trend Chart
async function updateVoucherTypeTrend() {
    const vtVal = document.getElementById('select-voucher-type').value;
    
    const res = await apiCall(`/api/trends?voucher_type=${encodeURIComponent(vtVal)}`);
    if (res && res.status === 'success') {
        const months = res.voucher.months;
        const values = res.voucher.values;
        const counts = res.voucher.counts;
        
        let colorTheme = '#8b5cf6';
        let bgTheme = 'rgba(139, 92, 246, 0.6)';
        
        if (vtVal === 'Sales') { colorTheme = '#10b981'; bgTheme = 'rgba(16, 185, 129, 0.6)'; }
        else if (vtVal === 'Purchase') { colorTheme = '#f43f5e'; bgTheme = 'rgba(244, 63, 94, 0.6)'; }
        else if (vtVal === 'Payment') { colorTheme = '#f59e0b'; bgTheme = 'rgba(245, 158, 11, 0.6)'; }
        else if (vtVal === 'Receipt') { colorTheme = '#3b82f6'; bgTheme = 'rgba(59, 130, 246, 0.6)'; }
        
        if (voucherTypeTrendChartObj) voucherTypeTrendChartObj.destroy();
        const ctx4 = document.getElementById('voucherTypeTrendChart').getContext('2d');
        voucherTypeTrendChartObj = new Chart(ctx4, {
            type: 'line',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Total Value (₹)',
                        data: values,
                        borderColor: colorTheme,
                        backgroundColor: bgTheme.replace('0.6', '0.1'),
                        fill: true,
                        tension: 0.3,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Volume (Counts)',
                        data: counts,
                        type: 'bar',
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1,
                        yAxisID: 'yCount'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#9ca3af' } },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                if (context.dataset.yAxisID === 'y') {
                                    return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                                }
                                return context.dataset.label + ': ' + context.parsed.y + ' txs';
                            }
                        }
                    }
                },
                scales: {
                    x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        ticks: { color: '#9ca3af', callback: v => '₹' + v.toLocaleString('en-IN') },
                        grid: { color: 'rgba(255,255,255,0.05)' }
                    },
                    yCount: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: { color: '#9ca3af', stepSize: 1 },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
    }
}

// Event Listeners for Filters
document.getElementById('table-search').addEventListener('input', () => {
    currentPage = 1;
    loadTableData();
});

document.getElementById('filter-voucher-type').addEventListener('change', () => {
    currentPage = 1;
    loadTableData();
});

document.getElementById('select-particular').addEventListener('change', updateParticularTrend);
document.getElementById('select-voucher-type').addEventListener('change', updateVoucherTypeTrend);

// Pagination actions
document.getElementById('btn-prev').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        loadTableData();
    }
});

document.getElementById('btn-next').addEventListener('click', () => {
    const totalPages = Math.ceil(totalFiltered / pageSize);
    if (currentPage < totalPages) {
        currentPage++;
        loadTableData();
    }
});

// App Startup
async function init() {
    await checkStatus();
    const res = await apiCall('/api/status');
    if (res && res.row_count > 0) {
        await loadDashboardData();
        await updateVoucherTypeTrend();
    }
}

init();
