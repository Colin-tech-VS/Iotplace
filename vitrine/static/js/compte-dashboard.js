(function () {
    const sidebar = document.getElementById('cdashSidebar');
    const overlay = document.getElementById('cdashOverlay');
    const menuBtn = document.getElementById('cdashMenuBtn');
    const navItems = document.querySelectorAll('[data-cdash-section]');
    const panels = document.querySelectorAll('.cdash-panel');

    function closeSidebar() {
        sidebar?.classList.remove('open');
        overlay?.classList.remove('visible');
        overlay?.setAttribute('hidden', '');
    }

    function openSidebar() {
        sidebar?.classList.add('open');
        overlay?.classList.add('visible');
        overlay?.removeAttribute('hidden');
    }

    menuBtn?.addEventListener('click', () => {
        if (sidebar?.classList.contains('open')) closeSidebar();
        else openSidebar();
    });

    overlay?.addEventListener('click', closeSidebar);

    function activate(section) {
        if (!section) return;
        navItems.forEach((el) => {
            const isNav = el.classList.contains('cdash-nav-item');
            if (!isNav) return;
            el.classList.toggle('active', el.dataset.cdashSection === section);
        });
        panels.forEach((panel) => {
            panel.classList.toggle('active', panel.dataset.section === section);
        });
        const url = new URL(window.location.href);
        url.searchParams.set('section', section);
        if (history.replaceState) {
            history.replaceState(null, '', url.pathname + url.search);
        }
        closeSidebar();
        window.IotPageLoader?.hide?.();
        if (section === 'messages') {
            window.IotMessenger?.refresh?.();
            setTimeout(() => window.IotMessenger?.maybeAutoOpenThread?.(), 250);
        }
    }

    navItems.forEach((el) => {
        el.addEventListener('click', (e) => {
            const section = el.dataset.cdashSection;
            if (!section) return;
            if (panels.length) {
                e.preventDefault();
                activate(section);
            }
        });
    });

    document.querySelectorAll('.cdash-open-chat').forEach((btn) => {
        btn.addEventListener('click', () => {
            activate('messages');
            setTimeout(() => {
                window.IotMessenger?.openThread({
                    counterpart_user_id: btn.dataset.counterpart,
                    project_id: btn.dataset.project || null,
                    counterpart_name: btn.dataset.name,
                    counterpart_role: btn.dataset.role,
                });
            }, 180);
        });
    });

    const params = new URLSearchParams(window.location.search);
    const initial = params.get('section');
    const hash = window.location.hash.replace('#', '');
    const section = initial || (hash === 'messages' ? 'messages' : null);
    if (section && document.querySelector(`[data-section="${section}"]`)) {
        activate(section);
    }

    const stored = sessionStorage.getItem('openChat');
    if (stored) {
        try {
            const data = JSON.parse(stored);
            sessionStorage.removeItem('openChat');
            activate('messages');
            setTimeout(() => {
                window.IotMessenger?.openThread({
                    counterpart_user_id: data.counterpart,
                    project_id: data.project || null,
                    counterpart_name: data.name,
                    counterpart_role: data.role,
                });
            }, 400);
        } catch (_) {
            sessionStorage.removeItem('openChat');
        }
    }
})();
