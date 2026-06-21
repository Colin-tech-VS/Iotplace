(function () {
    const meta = document.querySelector('meta[name="iot-analytics"]');
    if (!meta) return;

    const config = JSON.parse(meta.content);
    const sessionKey = 'iot_sid';
    let sessionId = sessionStorage.getItem(sessionKey) || config.session_id;
    if (!sessionId) {
        sessionId = crypto.randomUUID?.().slice(0, 12) || Math.random().toString(36).slice(2, 14);
    }
    sessionStorage.setItem(sessionKey, sessionId);

    function ping() {
        fetch('/api/analytics/ping', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                session_id: sessionId,
                page: config.page,
                path: window.location.pathname + window.location.search,
            }),
        }).catch(() => {});
    }

    ping();
    setInterval(ping, 15000);
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') ping();
    });
})();
