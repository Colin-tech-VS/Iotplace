(function () {
    function updateSectorField(field) {
        const select = field.querySelector('[data-sector-select]');
        const badge = field.querySelector('[data-sector-badge]');
        const hint = field.querySelector('[data-sector-hint]');
        const otherWrap = field.querySelector('[data-sector-other-wrap]');
        if (!select) return;

        const option = select.options[select.selectedIndex];
        const demand = option && option.value ? option.getAttribute('data-demand') : '';
        const isOther = option && option.value === 'other';

        if (badge) {
            const demandLabel = option ? option.getAttribute('data-demand-label') : '';
            if (demand && demandLabel) {
                badge.textContent = demandLabel;
                badge.className = 'sector-demand-badge sector-demand-' + demand;
                badge.hidden = false;
            } else {
                badge.hidden = true;
                badge.textContent = '';
            }
        }

        if (otherWrap) {
            otherWrap.hidden = !isOther;
            const otherInput = otherWrap.querySelector('[name="sector_other"]');
            if (otherInput) {
                otherInput.required = isOther;
            }
        }

        if (hint) {
            const parts = [];
            const tagline = option ? option.getAttribute('data-tagline') : '';
            const apps = option ? option.getAttribute('data-applications') : '';
            const clients = option ? option.getAttribute('data-clients') : '';
            const appsLabel = field.getAttribute('data-label-apps') || 'Applications:';
            const clientsLabel = field.getAttribute('data-label-clients') || 'Typical clients:';
            if (tagline) parts.push(tagline);
            if (apps) parts.push(appsLabel + ' ' + apps);
            if (clients) parts.push(clientsLabel + ' ' + clients);
            if (parts.length) {
                hint.textContent = parts.join(' · ');
                hint.hidden = false;
            } else {
                hint.textContent = '';
                hint.hidden = true;
            }
        }
    }

    function init() {
        document.querySelectorAll('[data-sector-field]').forEach(function (field) {
            const select = field.querySelector('[data-sector-select]');
            if (!select) return;
            select.addEventListener('change', function () {
                updateSectorField(field);
            });
            updateSectorField(field);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
