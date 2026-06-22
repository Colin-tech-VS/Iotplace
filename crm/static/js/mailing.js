(function () {
    const testSmtpBtn = document.getElementById('testSmtpBtn');
    const sendTestEmailBtn = document.getElementById('sendTestEmailBtn');
    const testImapBtn = document.getElementById('testImapBtn');
    const syncInboxBtn = document.getElementById('syncInboxBtn');
    const smtpStatus = document.getElementById('smtpTestStatus');
    const imapStatus = document.getElementById('imapTestStatus');
    const audienceSelect = document.getElementById('audience');
    const customField = document.getElementById('customRecipientsField');
    const mailPreviewBtn = document.getElementById('mailPreviewBtn');
    const localeEl = document.getElementById('mail-locale');

    function showStatus(el, message, isError) {
        if (!el) return;
        el.hidden = !message;
        el.textContent = message || '';
        el.classList.toggle('ai-status-error', Boolean(isError));
    }

    async function postJson(url, body) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body || {}),
        });
        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || data.message || 'Erreur');
        return data;
    }

    testSmtpBtn?.addEventListener('click', async () => {
        testSmtpBtn.disabled = true;
        showStatus(smtpStatus, 'Test SMTP en cours…', false);
        try {
            const data = await postJson('/crm/api/mailing/test-smtp', {
                locale: localeEl?.value || 'fr',
            });
            showStatus(smtpStatus, data.message || 'Connexion OK', false);
            if (window.IotToast) IotToast.show(data.message, { type: 'success' });
        } catch (err) {
            showStatus(smtpStatus, err.message, true);
            if (window.IotToast) IotToast.show(err.message, { type: 'error' });
        } finally {
            testSmtpBtn.disabled = false;
        }
    });

    sendTestEmailBtn?.addEventListener('click', async () => {
        const to = document.getElementById('testEmailTo')?.value?.trim();
        if (!to) {
            showStatus(smtpStatus, 'Indiquez une adresse email de test.', true);
            return;
        }
        sendTestEmailBtn.disabled = true;
        showStatus(smtpStatus, 'Envoi du test…', false);
        try {
            const data = await postJson('/crm/api/mailing/test-smtp', {
                to,
                locale: localeEl?.value || 'fr',
            });
            showStatus(smtpStatus, data.message, false);
            if (window.IotToast) IotToast.show(data.message, { type: 'success' });
        } catch (err) {
            showStatus(smtpStatus, err.message, true);
            if (window.IotToast) IotToast.show(err.message, { type: 'error' });
        } finally {
            sendTestEmailBtn.disabled = false;
        }
    });

    testImapBtn?.addEventListener('click', async () => {
        testImapBtn.disabled = true;
        showStatus(imapStatus, 'Test IMAP en cours…', false);
        try {
            const data = await postJson('/crm/api/mailing/test-imap', {});
            showStatus(imapStatus, `${data.message} (${data.messages || 0} messages)`, false);
            if (window.IotToast) IotToast.show(data.message, { type: 'success' });
        } catch (err) {
            showStatus(imapStatus, err.message, true);
            if (window.IotToast) IotToast.show(err.message, { type: 'error' });
        } finally {
            testImapBtn.disabled = false;
        }
    });

    syncInboxBtn?.addEventListener('click', async () => {
        syncInboxBtn.disabled = true;
        syncInboxBtn.textContent = 'Synchronisation…';
        try {
            const data = await postJson('/crm/api/mailing/sync-inbox', {});
            if (window.IotToast) IotToast.show(`${data.count} message(s) synchronisé(s).`, { type: 'success' });
            window.location.reload();
        } catch (err) {
            if (window.IotToast) IotToast.show(err.message, { type: 'error' });
            else alert(err.message);
        } finally {
            syncInboxBtn.disabled = false;
            syncInboxBtn.textContent = 'Synchroniser';
        }
    });

    mailPreviewBtn?.addEventListener('click', async () => {
        if (!window.IotMailPreview) return;
        mailPreviewBtn.disabled = true;
        mailPreviewBtn.textContent = 'Aperçu…';
        try {
            await window.IotMailPreview.refreshFromForm();
            if (window.IotToast) IotToast.show('Aperçu Iotplace mis à jour.', { type: 'success' });
        } catch (err) {
            if (window.IotToast) IotToast.show(err.message, { type: 'error' });
            else alert(err.message);
        } finally {
            mailPreviewBtn.disabled = false;
            mailPreviewBtn.textContent = 'Aperçu Iotplace';
        }
    });

    audienceSelect?.addEventListener('change', () => {
        if (!customField) return;
        customField.hidden = audienceSelect.value !== 'custom';
    });

    document.querySelectorAll('[data-confirm]').forEach((el) => {
        el.addEventListener('click', (event) => {
            const msg = el.dataset.confirm;
            if (msg && !confirm(msg)) event.preventDefault();
        });
    });
})();
