document.addEventListener('DOMContentLoaded', function () {
    const logsContainer = document.getElementById('logs-container');
    const logsOutput = document.getElementById('logs-output');
    const logLevel = document.getElementById('log-level');
    const logSearch = document.getElementById('log-search');
    const startDate = document.getElementById('start-date');
    const endDate = document.getElementById('end-date');
    const httpMethod = document.getElementById('http-method');
    const ipAddress = document.getElementById('ip-address');
    const path = document.getElementById('path');
    const userAgent = document.getElementById('user-agent');
    const excludeApi = document.getElementById('exclude-api');
    const applyFilters = document.getElementById('apply-filters');
    const loadingIndicator = document.getElementById('loading-indicator');
    const loadMoreButton = document.getElementById('load-more-logs');

    let currentPage = 1;
    let isLoading = false;
    let hasMoreLogs = true;

    fetchMetrics();

    // Uncomment the line below to enable automatic metrics refresh every 30 seconds
    // setInterval(fetchMetrics, 30000);

    function fetchLogs(append = false) {
        if (isLoading) return;

        isLoading = true;
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        if (loadMoreButton) loadMoreButton.style.display = 'none';

        const params = new URLSearchParams({
            level: logLevel ? logLevel.value : '',
            search: logSearch ? logSearch.value : '',
            start_date: startDate ? startDate.value : '',
            end_date: endDate ? endDate.value : '',
            http_method: httpMethod ? httpMethod.value : '',
            ip_address: ipAddress ? ipAddress.value : '',
            path: path ? path.value : '',
            user_agent: userAgent ? userAgent.value : '',
            exclude_api: excludeApi ? excludeApi.checked : false,
            page: currentPage,
            per_page: 50
        });

        fetch(`/api/logs?${params}`)
            .then(response => {
                if (response.status === 401) {
                    handleUnauthorized();
                    throw new Error('Unauthorized');
                }
                return response.json();
            })
            .then(data => {
                if (!append) {
                    logsOutput.innerHTML = '';
                }

                data.logs.forEach(log => {
                    const logEntry = document.createElement('div');

                    // Create a formatted timestamp
                    const timestamp = new Date(log.timestamp).toLocaleString();

                    // Construct the log message with more details
                    let logMessage = `
        <span class="log-timestamp">[${timestamp}]</span>
        <span class="log-level ${log.level.toLowerCase()}">${log.level.toUpperCase()}:</span>
        <pre class="log-event">${escapeHtml(log.event || 'No event')}</pre>
    `;

                    // Add additional fields if they exist
                    if (log.ip) {
                        logMessage += `<span class="log-ip">IP: ${escapeHtml(log.ip)}</span>`;
                    }
                    if (log.user_agent) {
                        logMessage += `<span class="log-user-agent">User Agent: ${escapeHtml(log.user_agent)}</span>`;
                    }
                    if (log.path) {
                        logMessage += `<span class="log-path">Path: ${escapeHtml(log.path)}</span>`;
                    }
                    if (log.method) {
                        logMessage += `<span class="log-method">Method: ${escapeHtml(log.method)}</span>`;
                    }
                    if (log.exception) {
                        logMessage += `<pre class="log-exception">Exception: ${escapeHtml(log.exception)}</pre>`;
                    }

                    logEntry.innerHTML = logMessage;
                    logEntry.className = `log-entry ${log.level.toLowerCase()}`;
                    logsOutput.appendChild(logEntry);
                });

                // Helper function to escape HTML
                function escapeHtml(unsafe) {
                    return unsafe
                        .replace(/&/g, "&amp;")
                        .replace(/</g, "&lt;")
                        .replace(/>/g, "&gt;")
                        .replace(/"/g, "&quot;")
                        .replace(/'/g, "&#039;");
                }

                hasMoreLogs = currentPage < data.total_pages;
                if (loadMoreButton) loadMoreButton.style.display = hasMoreLogs ? 'block' : 'none';

                isLoading = false;
                if (loadingIndicator) loadingIndicator.style.display = 'none';
            })
            .catch(error => {
                console.error('Error fetching logs:', error);
                if (error.message !== 'Unauthorized') {
                    logsOutput.innerHTML += '<p>Error loading logs</p>';
                }
                isLoading = false;
                if (loadingIndicator) loadingIndicator.style.display = 'none';
                if (loadMoreButton) loadMoreButton.style.display = 'none';
            });
    }

    if (applyFilters) {
        applyFilters.addEventListener('click', () => {
            currentPage = 1;
            hasMoreLogs = true;
            fetchLogs(false);
        });
    }

    if (loadMoreButton) {
        loadMoreButton.addEventListener('click', () => {
            currentPage++;
            fetchLogs(true);
        });
    }

    fetchLogs(false);

    const resetMetricsBtn = document.getElementById('reset-metrics-btn');

    resetMetricsBtn.addEventListener('click', function () {
        if (confirm('Are you sure you want to reset the metrics? This action cannot be undone.')) {
            fetch('/api/reset_metrics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.message) {
                        alert(data.message);
                        // Refresh the metrics display
                        fetchMetrics();
                    } else {
                        throw new Error(data.error || 'Unknown error occurred');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to reset metrics. Please try again.');
                });
        }
    });
});

function handleUnauthorized() {
    console.error('Unauthorized');
    document.body.innerHTML = '<h1>Unauthorized</h1><p>You do not have permission to view this page. Please log in.</p>';
}

function fetchMetrics() {
    fetch('/api/metrics')
        .then(response => {
            if (response.status === 401) {
                handleUnauthorized();
                throw new Error('Unauthorized');
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('unique-users-count').textContent = data.unique_users;
            document.getElementById('reports-generated-count').textContent = data.reports_generated;
        })
        .catch(error => {
            console.error('Error fetching metrics:', error);
            if (error.message !== 'Unauthorized') {
                document.getElementById('unique-users-count').textContent = 'Error loading';
                document.getElementById('reports-generated-count').textContent = 'Error loading';
            }
        });
}