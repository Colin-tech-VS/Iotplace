(function () {
    const page = document.querySelector('.profile-page');
    if (!page) return;

    const form = document.getElementById('profileForm');
    const panels = [...page.querySelectorAll('.profile-panel')];
    const tabs = [...page.querySelectorAll('[data-profile-tab]')];
    const stickyBar = document.getElementById('profileStickyBar');
    const nextBtn = document.getElementById('profileNextTab');
    let activeIndex = Math.max(0, tabs.findIndex((t) => t.classList.contains('active')));

    function showPanel(index) {
        if (!panels.length) return;
        activeIndex = Math.max(0, Math.min(index, panels.length - 1));
        const id = tabs[activeIndex]?.dataset.profileTab || panels[activeIndex]?.dataset.panel;

        tabs.forEach((tab, i) => {
            tab.classList.toggle('active', i === activeIndex);
            tab.setAttribute('aria-selected', i === activeIndex ? 'true' : 'false');
        });

        panels.forEach((panel) => {
            const on = panel.dataset.panel === id;
            panel.classList.toggle('active', on);
            panel.hidden = !on;
        });

        if (nextBtn) {
            const isLast = activeIndex >= panels.length - 1;
            nextBtn.textContent = isLast
                ? (window.IOT_I18N?.profile?.save_hint || 'Save at the bottom')
                : (window.IOT_I18N?.profile?.next_section || 'Next section →');
            nextBtn.dataset.isLast = isLast ? '1' : '0';
        }

        const url = new URL(window.location.href);
        if (id) url.searchParams.set('section', id);
        history.replaceState(null, '', url.pathname + url.search);
    }

    tabs.forEach((tab, i) => {
        tab.addEventListener('click', () => showPanel(i));
    });

    nextBtn?.addEventListener('click', () => {
        if (nextBtn.dataset.isLast === '1') {
            form?.querySelector('.profile-form-actions')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }
        if (activeIndex < panels.length - 1) showPanel(activeIndex + 1);
    });

    const params = new URLSearchParams(window.location.search);
    const initial = params.get('section');
    if (initial) {
        const idx = tabs.findIndex((t) => t.dataset.profileTab === initial);
        if (idx >= 0) showPanel(idx);
    } else {
        showPanel(0);
    }

    // Sticky bar visibility on scroll
    if (stickyBar && form) {
        const observer = new IntersectionObserver(
            ([entry]) => stickyBar.classList.toggle('is-visible', !entry.isIntersecting),
            { root: null, threshold: 0, rootMargin: '0px 0px -80px 0px' }
        );
        const anchor = form.querySelector('.profile-form-actions-anchor');
        if (anchor) observer.observe(anchor);
    }

    // Subtle field focus animation
    form?.querySelectorAll('input, textarea, select').forEach((el) => {
        el.addEventListener('focus', () => el.closest('.form-group')?.classList.add('is-focused'));
        el.addEventListener('blur', () => el.closest('.form-group')?.classList.remove('is-focused'));
    });

    // Reveal panels on first paint
    requestAnimationFrame(() => page.classList.add('is-ready'));
})();
