(function () {
    const input = document.querySelector('[data-directory-live-search]');
    const grid = document.querySelector('[data-directory-grid]');
    const list = document.querySelector('[data-directory-list]');
    const meta = document.getElementById('directoryResultsMeta');
    const emptyLive = document.getElementById('directoryEmptyLive');
    const form = document.getElementById('directorySearchForm');

    if (!input) return;

    const items = () => {
        const container = grid || list;
        if (!container) return [];
        return Array.from(container.querySelectorAll('[data-directory-item]'));
    };

    function countLabel(visible, total) {
        const tpl = meta?.dataset.countTemplate || '{visible} / {total}';
        return tpl
            .replace('{visible}', String(visible))
            .replace('{total}', String(total))
            .replace('{count}', String(visible));
    }

    function applyFilter() {
        const query = input.value.trim().toLowerCase();
        const all = items();
        let visible = 0;
        all.forEach((el) => {
            const text = (el.dataset.searchText || el.textContent || '').toLowerCase();
            const show = !query || text.includes(query);
            el.classList.toggle('is-hidden', !show);
            if (show) visible += 1;
        });
        if (meta) {
            const total = parseInt(meta.dataset.total || String(all.length), 10);
            meta.textContent = query
                ? countLabel(visible, total)
                : meta.dataset.staticLabel || meta.textContent;
        }
        if (emptyLive) {
            emptyLive.classList.toggle('visible', all.length > 0 && visible === 0);
        }
    }

    let debounce;
    input.addEventListener('input', () => {
        clearTimeout(debounce);
        debounce = setTimeout(applyFilter, 120);
    });

    form?.addEventListener('submit', (event) => {
        const query = input.value.trim();
        if (!query) {
            event.preventDefault();
            applyFilter();
        }
    });

    if (input.value.trim()) {
        applyFilter();
    }
})();
