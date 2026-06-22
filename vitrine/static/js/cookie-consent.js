(function () {
    const STORAGE_KEY = 'iot_cookie_consent';
    const COOKIE_NAME = 'iot_consent';
    const COOKIE_MAX_AGE = 60 * 60 * 24 * 395; // ~13 months

    const banner = document.getElementById('cookie-banner');
    const modal = document.getElementById('cookie-modal');
    const manageBtn = document.getElementById('cookie-manage-btn');
    const analyticsToggle = document.getElementById('cookie-analytics-toggle');
    if (!banner) return;

    function readConsent() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (raw) return JSON.parse(raw);
        } catch (_) {}
        const match = document.cookie.match(new RegExp('(?:^|; )' + COOKIE_NAME + '=([^;]*)'));
        if (match) {
            try {
                return JSON.parse(decodeURIComponent(match[1]));
            } catch (_) {}
        }
        return null;
    }

    function writeConsent(consent) {
        const payload = {
            analytics: !!consent.analytics,
            updated_at: new Date().toISOString(),
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
        document.cookie = COOKIE_NAME + '=' + encodeURIComponent(JSON.stringify(payload))
            + '; path=/; max-age=' + COOKIE_MAX_AGE + '; SameSite=Lax';
        return payload;
    }

    function loadGoogleAnalytics() {
        const gaId = document.querySelector('meta[name="iot-ga-id"]')?.content;
        if (!gaId || window.__iotGaLoaded) return;
        window.__iotGaLoaded = true;
        const script = document.createElement('script');
        script.async = true;
        script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(gaId);
        document.head.appendChild(script);
        window.dataLayer = window.dataLayer || [];
        function gtag() { window.dataLayer.push(arguments); }
        window.gtag = gtag;
        gtag('js', new Date());
        gtag('config', gaId);
    }

    function applyConsent(consent, reloadIfChanged) {
        const hadAnalytics = readConsent()?.analytics;
        writeConsent(consent);
        banner.hidden = true;
        modal.hidden = true;
        manageBtn.hidden = false;
        if (consent.analytics) {
            loadGoogleAnalytics();
            const meta = document.querySelector('meta[name="iot-analytics"]');
            if (meta && !document.querySelector('script[data-iot-analytics]')) {
                const s = document.createElement('script');
                s.src = meta.dataset.src || '/vitrine/static/js/analytics.js';
                s.dataset.iotAnalytics = '1';
                document.body.appendChild(s);
            }
        }
        if (reloadIfChanged && !!hadAnalytics !== !!consent.analytics) {
            window.location.reload();
        }
    }

    function showBanner() {
        banner.hidden = false;
        manageBtn.hidden = true;
    }

    const existing = readConsent();
    if (existing) {
        applyConsent(existing, false);
    } else {
        showBanner();
    }

    document.getElementById('cookie-accept')?.addEventListener('click', () => {
        applyConsent({ analytics: true }, true);
    });

    document.getElementById('cookie-reject')?.addEventListener('click', () => {
        applyConsent({ analytics: false }, true);
    });

    document.getElementById('cookie-customize')?.addEventListener('click', () => {
        const current = readConsent() || { analytics: false };
        if (analyticsToggle) analyticsToggle.checked = !!current.analytics;
        modal.hidden = false;
    });

    document.getElementById('cookie-modal-cancel')?.addEventListener('click', () => {
        modal.hidden = true;
    });

    document.getElementById('cookie-modal-backdrop')?.addEventListener('click', () => {
        modal.hidden = true;
    });

    document.getElementById('cookie-save')?.addEventListener('click', () => {
        applyConsent({ analytics: analyticsToggle?.checked }, true);
    });

    manageBtn?.addEventListener('click', () => {
        const current = readConsent() || { analytics: false };
        if (analyticsToggle) analyticsToggle.checked = !!current.analytics;
        modal.hidden = false;
    });
})();
