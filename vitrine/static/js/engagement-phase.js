(function () {
    const PHASE_DEFAULTS = {
        poc: { budget: '10k–50k€', duration: '3–6 mois' },
        scale: { budget: '150k–500k€', duration: '6–12 mois' },
        partnership: { budget: '500k€+', duration: '12+ mois' },
    };

    function applyPhaseDefaults(phaseSelect, budgetSelect, durationSelect) {
        const phase = phaseSelect.value;
        const defaults = PHASE_DEFAULTS[phase];
        if (!defaults) return;
        if (budgetSelect && !budgetSelect.dataset.userTouched) {
            budgetSelect.value = defaults.budget;
        }
        if (durationSelect && !durationSelect.dataset.userTouched) {
            durationSelect.value = defaults.duration;
        }
    }

    function wireForm(form) {
        const phaseSelect = form.querySelector('[data-phase-select]');
        const budgetSelect = form.querySelector('[data-budget-select]');
        const durationSelect = form.querySelector('[data-duration-select]');
        if (!phaseSelect) return;

        [budgetSelect, durationSelect].forEach((el) => {
            if (!el) return;
            el.addEventListener('change', () => { el.dataset.userTouched = '1'; });
        });

        phaseSelect.addEventListener('change', () => {
            if (budgetSelect) budgetSelect.dataset.userTouched = '';
            if (durationSelect) durationSelect.dataset.userTouched = '';
            applyPhaseDefaults(phaseSelect, budgetSelect, durationSelect);
        });

        if (phaseSelect.value) {
            applyPhaseDefaults(phaseSelect, budgetSelect, durationSelect);
        }
    }

    document.querySelectorAll('form.register-form, #projectForm').forEach(wireForm);
})();
