(function () {
    const panel = document.getElementById('mail-ai-panel');
    if (!panel) return;

    const generateUrl = panel.dataset.generateUrl;
    const previewUrl = panel.dataset.previewUrl;
    const promptEl = document.getElementById('ai-prompt');
    const toneEl = document.getElementById('ai-tone');
    const localeEl = document.getElementById('mail-locale');
    const audienceEl = document.getElementById('audience');
    const generateBtn = document.getElementById('aiGenerateBtn');
    const applyBtn = document.getElementById('aiApplyBtn');
    const statusEl = document.getElementById('ai-status');
    const previewWrap = document.getElementById('mail-preview-wrap');
    const previewFrame = document.getElementById('mail-preview-frame');
    const subjectEl = document.getElementById('subject');
    const bodyHtmlEl = document.getElementById('body_html');
    const bodyTextEl = document.getElementById('body_text');
    const sourceEl = document.getElementById('mailSource');
    const aiPromptHidden = document.getElementById('aiPromptHidden');

    let lastResult = null;

    function setStatus(message, isError) {
        if (!statusEl) return;
        statusEl.hidden = !message;
        statusEl.textContent = message || '';
        statusEl.classList.toggle('ai-status-error', Boolean(isError));
    }

    function showBrandedPreview(html) {
        if (!previewWrap || !previewFrame) return;
        previewWrap.hidden = false;
        previewFrame.srcdoc = html;
    }

    generateBtn?.addEventListener('click', async () => {
        if (generateBtn.disabled) return;
        generateBtn.disabled = true;
        generateBtn.textContent = 'Génération…';
        setStatus('Génération du contenu email…', false);
        try {
            const res = await fetch(generateUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: promptEl?.value || '',
                    audience: audienceEl?.value || 'contacts',
                    subject_hint: subjectEl?.value || '',
                    tone: toneEl?.value || 'professional',
                    locale: localeEl?.value || 'fr',
                }),
            });
            const data = await res.json();
            if (!res.ok || !data.ok) throw new Error(data.error || 'Échec génération');
            lastResult = data;
            if (data.preview_html) {
                showBrandedPreview(data.preview_html);
            }
            if (applyBtn) applyBtn.hidden = false;
            setStatus('Aperçu Iotplace généré — cliquez sur « Appliquer au formulaire ».', false);
        } catch (err) {
            setStatus(err.message, true);
            if (window.IotToast) IotToast.show(err.message, { type: 'error' });
        } finally {
            generateBtn.disabled = generateBtn.hasAttribute('data-disabled');
            generateBtn.textContent = 'Générer avec Mistral';
        }
    });

    applyBtn?.addEventListener('click', () => {
        if (!lastResult) return;
        if (subjectEl) subjectEl.value = lastResult.subject || '';
        if (bodyHtmlEl) bodyHtmlEl.value = lastResult.body_html || '';
        if (bodyTextEl) bodyTextEl.value = lastResult.body_text || '';
        if (sourceEl) sourceEl.value = 'ai';
        if (aiPromptHidden && promptEl) aiPromptHidden.value = promptEl.value || '';
        if (localeEl && lastResult.locale) localeEl.value = lastResult.locale;
        setStatus('Contenu appliqué au formulaire.', false);
        if (window.IotToast) IotToast.show('Email appliqué au formulaire.', { type: 'success' });
    });

    window.IotMailPreview = {
        async refreshFromForm() {
            if (!previewUrl || !bodyHtmlEl?.value?.trim()) {
                throw new Error('Renseignez le corps HTML avant l\'aperçu.');
            }
            const res = await fetch(previewUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    body_html: bodyHtmlEl.value,
                    subject: subjectEl?.value || '',
                    locale: localeEl?.value || 'fr',
                }),
            });
            const data = await res.json();
            if (!res.ok || !data.ok) throw new Error(data.error || 'Échec aperçu');
            showBrandedPreview(data.preview_html);
            return data;
        },
    };
})();
