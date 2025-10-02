// FILE: static/app.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('URL Monitor dashboard loaded.');

    // Auto-refresh the page every 60 seconds to get the latest status
    const autoRefreshInterval = 60000; // 60 seconds in milliseconds
    
    setTimeout(() => {
        window.location.reload();
    }, autoRefreshInterval);
});