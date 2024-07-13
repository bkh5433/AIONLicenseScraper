document.addEventListener('DOMContentLoaded', function () {
    const logsOutput = document.getElementById('logs-output');
    const logLevel = document.getElementById('log-level');
    const logSearch = document.getElementById('log-search');
    const startDate = document.getElementById('start-date');
    const endDate = document.getElementById('end-date');
    const httpMethod = document.getElementById('http-method');
    const ipAddress = document.getElementById('ip-address');
    const path = document.getElementById('path');
    const userAgent = document.getElementById('user-agent');
    const applyFilters = document.getElementById('apply-filters');
    const loadingIndicator = document.getElementById('loading-indicator');

    let currentPage = 1;
    let isLoading = false;
    let hasMoreLogs = true;

    fetchMetrics();

    //     setInterval(fetchMetrics, 60000); // Refresh metrics every minute

    function fetchLogs(append = false) {
        if (isLoading || !hasMoreLogs) return;

        isLoading = true;
        loadingIndicator.style.display = 'block';

        const params = new URLSearchParams({
            level: logLevel.value,
            search: logSearch.value,
            start_date: startDate.value,
            end_date: endDate.value,
            http_method: httpMethod.value,
            ip_address: ipAddress.value,
            path: path.value,
            user_agent: userAgent.value,
            page: currentPage,
            per_page: 50
        });

        fetch(`/api/logs?${params}`)
            .then(response => response.json())
            .then(data => {
                if (!append) {
                    logsOutput.innerHTML = '';
                    currentPage = 1;
                }

                data.logs.forEach(log => {
                    const logEntry = document.createElement('div');

                    // Create a formatted timestamp
                    const timestamp = new Date(log.timestamp).toLocaleString();

                    // Construct the log message with more details
                    let logMessage = `
                        <span class="log-timestamp">[${timestamp}]</span>
                        <span class="log-level ${log.level}">${log.level.toUpperCase()}:</span>
                        <span class="log-event">${log.event}</span>
                    `;

                    // Add additional fields if they exist
                    if (log.ip) {
                        logMessage += `<span class="log-ip">IP: ${log.ip}</span>`;
                    }
                    if (log.user_agent) {
                        logMessage += `<span class="log-user-agent">User Agent: ${log.user_agent}</span>`;
                    }
                    if (log.path) {
                        logMessage += `<span class="log-path">Path: ${log.path}</span>`;
                    }
                    if (log.method) {
                        logMessage += `<span class="log-method">Method: ${log.method}</span>`;
                    }
                    if (log.exception) {
                        logMessage += `<pre class="log-exception">Exception: ${log.exception}</pre>`;
                    }

                    logEntry.innerHTML = logMessage;
                    logEntry.className = `log-entry ${log.level}`;
                    logsOutput.appendChild(logEntry);
                });

                hasMoreLogs = currentPage < data.total_pages;
                isLoading = false;
                loadingIndicator.style.display = 'none';
            })
            .catch(error => {
                console.error('Error fetching logs:', error);
                isLoading = false;
                loadingIndicator.style.display = 'none';
            });
    }

    function handleScroll() {
        const scrollPosition = window.innerHeight + window.scrollY;
        const bodyHeight = document.body.offsetHeight;

        if (scrollPosition >= bodyHeight - 200 && !isLoading && hasMoreLogs) {
            currentPage++;
            fetchLogs(true);
        }
    }

    applyFilters.addEventListener('click', () => {
        currentPage = 1;
        hasMoreLogs = true;
        fetchLogs(false);
    });

    window.addEventListener('scroll', handleScroll);

    fetchLogs(false);
});


function fetchMetrics() {
    fetch('/api/metrics')
        .then(response => response.json())
        .then(data => {
            document.getElementById('unique-users-count').textContent = data.unique_users;
            document.getElementById('reports-generated-count').textContent = data.reports_generated;
        })
        .catch(error => console.error('Error fetching metrics:', error));
}