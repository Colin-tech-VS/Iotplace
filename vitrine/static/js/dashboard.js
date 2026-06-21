(function () {
    const tabs = document.querySelectorAll('.ux-tab');
    const panels = document.querySelectorAll('.ux-panel');
    if (!tabs.length) return;

    function activate(tabName) {
        tabs.forEach((t) => t.classList.toggle('active', t.dataset.tab === tabName));
        panels.forEach((p) => p.classList.toggle('active', p.id === 'ux-panel-' + tabName));
        if (history.replaceState) {
            history.replaceState(null, '', '#' + tabName);
        }
    }

    tabs.forEach((btn) => {
        btn.addEventListener('click', () => activate(btn.dataset.tab));
    });

    document.querySelectorAll('.ux-stat-clickable').forEach((el) => {
        el.addEventListener('click', (e) => {
            const tab = el.dataset.tab;
            if (tab) {
                e.preventDefault();
                activate(tab);
                document.querySelector('.ux-tabs')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
    });

    const hash = location.hash.replace('#', '');
    const valid = Array.from(tabs).some((t) => t.dataset.tab === hash);
    if (valid) activate(hash);
    else if (hash === 'messages') activate('messages');
})();
