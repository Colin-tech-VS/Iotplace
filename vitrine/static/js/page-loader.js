(function (global) {
    const LOADER_ID = 'iot-page-loader';
    const MIN_VISIBLE_MS = 60;
    let shownAt = 0;
    let hideTimer = null;
    let initialLoad = document.readyState === 'loading';

    function getLoader() {
        return document.getElementById(LOADER_ID);
    }

    function labels() {
        const lang = (document.documentElement.lang || 'en').toLowerCase();
        if (lang.startsWith('fr')) {
            return { title: 'Chargement', sub: 'Connexion à la plateforme…' };
        }
        return { title: 'Loading', sub: 'Connecting to the platform…' };
    }

    function ensureLoader() {
        let loader = getLoader();
        if (loader) return loader;

        const { title, sub } = labels();
        loader = document.createElement('div');
        loader.id = LOADER_ID;
        loader.className = 'iot-page-loader';
        loader.setAttribute('role', 'status');
        loader.setAttribute('aria-live', 'polite');
        loader.setAttribute('aria-busy', 'false');
        loader.innerHTML = `
            <div class="iot-page-loader-inner">
                <span class="iot-brand-mark iot-brand-mark--lg is-animated iot-page-loader-mark" aria-hidden="true">
                    <img class="iot-brand-mark-img" src="/vitrine/static/brand/iotplace-mark.svg" alt="" width="24" height="24" decoding="async">
                    <span class="iot-brand-mark-ring"></span>
                </span>
                <p class="iot-page-loader-text">${title}</p>
                <p class="iot-page-loader-sub">${sub}</p>
                <div class="iot-page-loader-bar" aria-hidden="true"><span></span></div>
            </div>`;
        document.body.appendChild(loader);
        return loader;
    }

    function show() {
        const loader = ensureLoader();
        if (hideTimer) {
            clearTimeout(hideTimer);
            hideTimer = null;
        }
        shownAt = Date.now();
        document.documentElement.classList.add('iot-loading');
        loader.classList.remove('is-leaving');
        loader.classList.add('is-active');
        loader.setAttribute('aria-busy', 'true');
    }

    function hide() {
        const loader = getLoader();
        if (!loader || !loader.classList.contains('is-active')) {
            document.documentElement.classList.remove('iot-loading');
            return;
        }

        const elapsed = Date.now() - shownAt;
        const delay = Math.max(0, MIN_VISIBLE_MS - elapsed);

        hideTimer = setTimeout(() => {
            loader.classList.add('is-leaving');
            loader.classList.remove('is-active');
            loader.setAttribute('aria-busy', 'false');
            document.documentElement.classList.remove('iot-loading');
            setTimeout(() => loader.classList.remove('is-leaving'), 200);
        }, delay);
    }

    function shouldHandleLink(anchor, event) {
        if (!anchor || !anchor.href) return false;
        if (anchor.target === '_blank' || anchor.hasAttribute('download')) return false;
        if (anchor.dataset.noLoader !== undefined) return false;
        if (anchor.dataset.cdashSection !== undefined) return false;
        if (event && (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)) return false;
        const href = anchor.getAttribute('href') || '';
        if (!href || href.startsWith('#') || href.startsWith('javascript:')) return false;
        if (href.startsWith('mailto:') || href.startsWith('tel:')) return false;
        try {
            const url = new URL(anchor.href, window.location.href);
            if (url.origin !== window.location.origin) return false;
            if (url.pathname === window.location.pathname && url.search === window.location.search) {
                return false;
            }
        } catch (_) {
            return false;
        }
        return false;
    }

    function bindNavigation() {
        document.addEventListener('submit', (event) => {
            const form = event.target;
            if (!(form instanceof HTMLFormElement)) return;
            if (form.target === '_blank' || form.dataset.noLoader !== undefined) return;
            if (form.method && form.method.toLowerCase() === 'get') return;
            show();
        }, true);
    }

    function onReady() {
        hide();
        document.querySelectorAll('.reveal').forEach((el, i) => {
            el.style.animationDelay = `${Math.min(i * 0.04, 0.35)}s`;
        });
    }

    global.IotPageLoader = { show, hide };

    // Show the brand splash only when a load is genuinely slow. Fast and
    // prefetched pages render instantly with no loading flash, which is what
    // makes navigation feel fluid.
    const SLOW_LOAD_MS = 320;

    if (initialLoad) {
        document.documentElement.classList.add('iot-loading');
        const splashTimer = setTimeout(show, SLOW_LOAD_MS);
        document.addEventListener('DOMContentLoaded', () => {
            clearTimeout(splashTimer);
            onReady();
        }, { once: true });
    } else {
        onReady();
    }

    window.addEventListener('pageshow', (event) => {
        if (event.persisted) hide();
    });

    bindNavigation();
})(window);
