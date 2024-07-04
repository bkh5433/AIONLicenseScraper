document.addEventListener('DOMContentLoaded', function () {
    const versionBadge = document.getElementById('version-badge');
    if (!versionBadge) return;  // Exit if the badge isn't present

    const buildDate = new Date(versionBadge.dataset.buildDate);
    const now = new Date();
    const daysSinceBuild = (now - buildDate) / (1000 * 60 * 60 * 24);

    if (daysSinceBuild < 7) {
        versionBadge.classList.add('recent');
    } else if (daysSinceBuild < 30) {
        versionBadge.classList.add('moderate');
    } else {
        versionBadge.classList.add('old');
    }
});