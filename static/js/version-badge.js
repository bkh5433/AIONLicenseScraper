/**
 * Version Badge Functionality
 *
 * This script adds dynamic behavior to the version badge in the AION License Count application.
 * It calculates the age of the current build and applies appropriate CSS classes to color-code
 * the badge based on how recent the build is.
 *
 * The script waits for the DOM to be fully loaded before executing to ensure all elements are available.
 */

document.addEventListener('DOMContentLoaded', function () {
    // Find the version badge element
    const versionBadge = document.getElementById('version-badge');

    // Exit the function if the badge element isn't found
    if (!versionBadge) return;

    // Extract the build date from the badge's data attribute
    const buildDate = new Date(versionBadge.dataset.buildDate);

    const now = new Date();

    // Calculate the number of days since the build
    // 1000 ms * 60 s * 60 min * 24 h = 1 day in milliseconds
    const daysSinceBuild = (now - buildDate) / (1000 * 60 * 60 * 24);

    // Apply appropriate CSS class based on the age of the build
    if (daysSinceBuild < 7) {
        // Less than a week old
        versionBadge.classList.add('recent');
    } else if (daysSinceBuild < 30) {
        // Less than a month old
        versionBadge.classList.add('moderate');
    } else {
        // More than a month old
        versionBadge.classList.add('old');
    }
});