document.addEventListener('DOMContentLoaded', function () {
    const logsOutput = document.getElementById('logs-output');
    const logLevel = document.getElementById('log-level');
    const logSearch = document.getElementById('log-search');
    const httpMethod = document.getElementById('http-method');
    const excludeApi = document.getElementById('exclude-api');
    const applyFilters = document.getElementById('apply-filters');
    const loadingIndicator = document.getElementById('loading-indicator');
    const loadMoreButton = document.getElementById('load-more-logs');
    const resetMetricsBtn = document.getElementById('reset-metrics-btn');

    let currentPage = 1;
    let isLoading = false;
    let hasMoreLogs = true;

    fetchMetrics();
    setInterval(fetchMetrics, 10000)
    fetchLogs(false);

    applyFilters.addEventListener('click', () => {
        currentPage = 1;
        hasMoreLogs = true;
        fetchLogs(false);
    });

    loadMoreButton.addEventListener('click', () => {
        currentPage++;
        fetchLogs(true);
    });

    resetMetricsBtn.addEventListener('click', resetMetrics);

    function fetchLogs(append = false) {
        if (isLoading) return;

        isLoading = true;
        loadingIndicator.style.display = 'block';
        loadMoreButton.style.display = 'none';

        const params = new URLSearchParams({
            level: logLevel.value,
            search: logSearch.value,
            http_method: httpMethod.value,
            exclude_api: excludeApi.checked,
            page: currentPage,
            per_page: 50
        });

        fetch(`/api/logs?${params}`)
            .then(handleResponse)
            .then(data => {
                if (!append) {
                    logsOutput.innerHTML = '';
                }

                data.logs.forEach(log => {
                    const logEntry = createLogEntry(log);
                    logsOutput.appendChild(logEntry);
                });

                hasMoreLogs = currentPage < data.total_pages;
                loadMoreButton.style.display = hasMoreLogs ? 'block' : 'none';

                isLoading = false;
                loadingIndicator.style.display = 'none';
            })
            .catch(handleError);
    }

    function fetchMetrics() {
        fetch('/api/metrics')
            .then(handleResponse)
            .then(data => {
                document.getElementById('unique-users-count').textContent = data.unique_users;
                document.getElementById('reports-generated-count').textContent = data.reports_generated;
            })
            .catch(handleError);
    }

    function resetMetrics() {
        if (confirm('Are you sure you want to reset the metrics? This action cannot be undone.')) {
            fetch('/api/reset_metrics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
                .then(handleResponse)
                .then(data => {
                    alert(data.message);
                    fetchMetrics();
                })
                .catch(handleError);
        }
    }

    function handleResponse(response) {
        if (response.status === 401) {
            handleUnauthorized();
            throw new Error('Unauthorized');
        }
        return response.json();
    }

    function handleError(error) {
        console.error('Error:', error);
        if (error.message !== 'Unauthorized') {
            alert('An error occurred. Please try again.');
        }
        isLoading = false;
        loadingIndicator.style.display = 'none';
        loadMoreButton.style.display = 'none';
    }

    function handleUnauthorized() {
        document.body.innerHTML = '<h1>Unauthorized</h1><p>You do not have permission to view this page. Please log in.</p>';
    }

    function createLogEntry(log) {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${log.level.toLowerCase()}`;

        const timestamp = new Date(log.timestamp).toLocaleString();
        const logContent = `
            <span class="log-timestamp">[${timestamp}]</span>
            <span class="log-level ${log.level.toLowerCase()}">${log.level.toUpperCase()}:</span>
            <pre class="log-event">${escapeHtml(log.event || 'No event')}</pre>
            ${log.ip ? `<span class="log-ip">IP: ${escapeHtml(log.ip)}</span>` : ''}
            ${log.user_agent ? `<span class="log-user-agent">User Agent: ${escapeHtml(log.user_agent)}</span>` : ''}
            ${log.path ? `<span class="log-path">Path: ${escapeHtml(log.path)}</span>` : ''}
            ${log.method ? `<span class="log-method">Method: ${escapeHtml(log.method)}</span>` : ''}
            ${log.exception ? `<pre class="log-exception">Exception: ${escapeHtml(log.exception)}</pre>` : ''}
        `;

        logEntry.innerHTML = logContent;
        return logEntry;
    }

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});