function getFrontendRoute(mode) {
    const config = window.__APP_CONFIG__ || {};
    const routes = {
        rpgv2: config.rpgv2Path || '/rpgv2'
    };

    return routes[mode];
}

function getBackendBaseURL() {
    const config = window.__APP_CONFIG__ || {};
    return config.backendBaseUrl || window.location.origin;
}

function openMode(mode) {
    const url = getFrontendRoute(mode);
    if (!url) return;

    window.open(url, '_blank', 'noopener,noreferrer');
}

async function checkBackendStatus() {
    try {
        const response = await fetch(`${getBackendBaseURL()}/health`);
        if (response.ok) {
            console.log('✅ RPG v2 backend service available');
            return true;
        }
    } catch (error) {
        console.warn('⚠️ RPG v2 backend service unavailable');
    }
    return false;
}

window.addEventListener('load', () => {
    checkBackendStatus();
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' || e.key === '2') openMode('rpgv2');
});

console.log(`
╔════════════════════════════════════════╗
║        Anti-FraudX RPG v2 Only        ║
╠════════════════════════════════════════╣
║  快捷鍵：                               ║
║  Enter / 2 - 打開 RPG v2               ║
╚════════════════════════════════════════╝
`);
