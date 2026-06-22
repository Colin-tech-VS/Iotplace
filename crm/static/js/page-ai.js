(function () {
    const panel = document.getElementById('ai-panel');
    if (!panel) return;

    const generateUrl = panel.dataset.generateUrl;
    const promptEl = document.getElementById('ai-prompt');
    const includeSeoEl = document.getElementById('ai-include-seo');
    const includeFaqEl = document.getElementById('ai-include-faq');
    const generateBtn = document.getElementById('ai-generate-btn');
    const applyBtn = document.getElementById('ai-apply-btn');
    const saveBtn = document.getElementById('ai-save-btn');
    const statusEl = document.getElementById('ai-status');
    const previewEl = document.getElementById('ai-preview');
    const form = document.getElementById('page-form');

    let lastResult = null;

    function setStatus(message, isError) {
        if (!statusEl) return;
        statusEl.hidden = !message;
        statusEl.textContent = message || '';
        statusEl.classList.toggle('ai-status-error', Boolean(isError));
    }

    function setLoading(loading) {
        generateBtn.disabled = loading || generateBtn.hasAttribute('data-disabled');
        if (saveBtn) saveBtn.disabled = loading;
        generateBtn.textContent = loading ? 'Génération en cours…' : 'Générer avec Mistral';
    }

    function showPreview(result) {
        if (!previewEl) return;
        previewEl.hidden = false;
        previewEl.textContent = JSON.stringify(result, null, 2);
    }

    function applyToForm(content) {
        if (!form || !content) return;
        Object.entries(content).forEach(([name, value]) => {
            const field = form.querySelector(`[name="${name}"]`);
            if (field) field.value = value ?? '';
        });
    }

    async function callApi(save) {
        setLoading(true);
        setStatus(save ? 'Génération et enregistrement…' : 'Génération du contenu…', false);
        try {
            const response = await fetch(generateUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: promptEl?.value || '',
                    include_seo: includeSeoEl?.checked !== false,
                    include_faq: includeFaqEl?.checked !== false,
                    save: Boolean(save),
                }),
            });
            const data = await response.json();
            if (!response.ok || !data.ok) {
                throw new Error(data.error || 'Generation failed');
            }
            lastResult = data;
            showPreview(data);
            applyBtn.hidden = false;
            saveBtn.hidden = false;
            setStatus(
                save
                    ? 'Contenu, SEO et FAQ enregistrés. La page a été mise à jour.'
                    : 'Contenu généré. Cliquez sur « Appliquer au formulaire » ou « Générer et enregistrer ».',
                false
            );
            if (save) {
                applyToForm(data.content);
                if (window.IotToast) {
                    IotToast.show('Contenu, SEO et FAQ enregistrés.', { type: 'success' });
                }
                if (data.seo) {
                    setStatus('Contenu, SEO et FAQ enregistrés. Rechargez la page SEO pour les voir.', false);
                }
            }
        } catch (error) {
            const msg = error.message || 'Erreur Mistral';
            setStatus(msg, true);
            if (window.IotToast) IotToast.show(msg, { type: 'error' });
        } finally {
            setLoading(false);
        }
    }

    generateBtn?.addEventListener('click', () => callApi(false));
    applyBtn?.addEventListener('click', () => {
        if (!lastResult?.content) return;
        applyToForm(lastResult.content);
        setStatus('Contenu appliqué au formulaire. N’oubliez pas d’enregistrer.', false);
    });
    saveBtn?.addEventListener('click', () => {
        if (!confirm('Générer et enregistrer directement cette page (contenu, SEO, FAQ) ?')) return;
        callApi(true);
    });

    if (generateBtn?.hasAttribute('disabled')) {
        generateBtn.dataset.disabled = '1';
    }
})();
