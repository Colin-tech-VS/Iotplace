(function () {
    function selectCard(field, card) {
        const input = field.querySelector('[data-sector-input]');
        if (!input || !card) return;
        const sectorId = card.getAttribute('data-sector-id') || '';
        input.value = sectorId;
        field.querySelectorAll('[data-domain-card]').forEach(function (btn) {
            const active = btn === card;
            btn.classList.toggle('domain-card-selected', active);
            btn.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
    }

    function init() {
        document.querySelectorAll('[data-sector-field]').forEach(function (field) {
            const input = field.querySelector('[data-sector-input]');
            field.querySelectorAll('[data-domain-card]').forEach(function (card) {
                card.addEventListener('click', function () {
                    selectCard(field, card);
                });
            });
            if (input && input.value) {
                const selected = field.querySelector('[data-domain-card][data-sector-id="' + input.value + '"]');
                if (selected) selectCard(field, selected);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
