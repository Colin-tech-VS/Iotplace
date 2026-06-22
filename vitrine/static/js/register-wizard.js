(function () {
    const form = document.querySelector('[data-reg-wizard]');
    if (!form) return;

    const panels = [...form.querySelectorAll('[data-wizard-step]')];
    const progressBars = [...document.querySelectorAll('[data-wizard-progress]')];
    const stepPills = [...document.querySelectorAll('[data-wizard-pill]')];
    const stepLabel = document.querySelector('[data-wizard-step-label]');
    const backBtn = form.querySelector('[data-wizard-back]');
    const nextBtn = form.querySelector('[data-wizard-next]');
    const submitBtn = form.querySelector('[data-wizard-submit]');
    const total = panels.length;
    let current = 0;

    function setBtnVisible(btn, visible) {
        if (!btn) return;
        btn.hidden = !visible;
        btn.style.display = visible ? '' : 'none';
        btn.disabled = !visible;
    }

    function showStep(index) {
        current = Math.max(0, Math.min(index, total - 1));
        const isLast = current === total - 1;

        panels.forEach((panel, i) => {
            panel.classList.toggle('is-active', i === current);
            panel.hidden = i !== current;
        });
        progressBars.forEach((bar, i) => {
            bar.classList.toggle('is-active', i === current);
            bar.classList.toggle('is-done', i < current);
        });
        stepPills.forEach((pill, i) => {
            pill.classList.toggle('is-active', i === current);
        });
        if (stepLabel) {
            const tpl = stepLabel.dataset.template || 'Step {current} of {total}';
            stepLabel.textContent = tpl.replace('{current}', String(current + 1)).replace('{total}', String(total));
        }

        setBtnVisible(backBtn, current > 0);
        setBtnVisible(nextBtn, !isLast);
        setBtnVisible(submitBtn, isLast);
    }

    function validateStep(index) {
        const panel = panels[index];
        if (!panel) return true;
        const fields = [...panel.querySelectorAll('input, textarea, select')].filter((el) => {
            if (el.disabled || el.type === 'hidden') return false;
            if (el.closest('[hidden]')) return false;
            return true;
        });
        for (const field of fields) {
            if (!field.checkValidity()) {
                field.reportValidity();
                return false;
            }
        }
        const pw = form.querySelector('#password');
        const pwc = form.querySelector('#password_confirm');
        if (index === 0 && pw && pwc && pw.value !== pwc.value) {
            pwc.setCustomValidity(pwc.dataset.mismatch || 'Passwords do not match');
            pwc.reportValidity();
            pwc.setCustomValidity('');
            return false;
        }
        if (index === 1) {
            const sectorInput = form.querySelector('#sector_id');
            if (sectorInput && sectorInput.required && !sectorInput.value) {
                sectorInput.setCustomValidity(sectorInput.dataset.requiredMsg || 'Required');
                sectorInput.reportValidity();
                sectorInput.setCustomValidity('');
                return false;
            }
        }
        return true;
    }

    backBtn?.addEventListener('click', () => showStep(current - 1));
    nextBtn?.addEventListener('click', () => {
        if (validateStep(current)) showStep(current + 1);
    });

    form.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && current !== total - 1) {
            const tag = (e.target && e.target.tagName) || '';
            if (tag !== 'TEXTAREA' && e.target !== submitBtn) {
                e.preventDefault();
                if (validateStep(current)) showStep(current + 1);
            }
        }
    });

    form.addEventListener('submit', (e) => {
        if (current !== total - 1) {
            e.preventDefault();
            if (validateStep(current)) showStep(current + 1);
            return;
        }
        if (!validateStep(current)) e.preventDefault();
    });

    showStep(0);
})();
