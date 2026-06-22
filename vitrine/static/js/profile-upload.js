(function () {
    const root = document.getElementById('profileLogoUpload');
    if (!root) return;

    const drop = document.getElementById('profileLogoDrop');
    const input = document.getElementById('profileLogoInput');
    const browse = document.getElementById('profileLogoBrowse');
    const removeBtn = document.getElementById('profileLogoRemove');
    const statusEl = document.getElementById('profileLogoStatus');
    const preview = document.getElementById('profileLogoPreview');
    const uploadUrl = root.dataset.uploadUrl;
    const deleteUrl = root.dataset.deleteUrl;

    function showStatus(msg, type) {
        if (!statusEl) return;
        statusEl.hidden = !msg;
        statusEl.textContent = msg || '';
        statusEl.className = `profile-logo-status ${type || 'muted'}`;
    }

    function setPreview(url) {
        if (!preview) return;
        preview.innerHTML = url
            ? `<img src="${url}?t=${Date.now()}" alt="" id="profileLogoImg">`
            : `<span class="profile-logo-fallback lg" id="profileLogoFallback">?</span>`;
    }

    async function upload(file) {
        const fd = new FormData();
        fd.append('logo', file);
        showStatus(window.IOT_I18N?.profile?.logo_uploading || 'Upload…', 'info');
        const res = await fetch(uploadUrl, { method: 'POST', body: fd });
        const data = await res.json();
        if (!data.ok) {
            showStatus(data.error || 'Error', 'error');
            return;
        }
        setPreview(data.logo_url);
        showStatus(window.IOT_I18N?.profile?.logo_ok || 'Logo updated.', 'success');
        if (!removeBtn && drop) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-ghost btn-sm';
            btn.id = 'profileLogoRemove';
            btn.textContent = window.IOT_I18N?.profile?.logo_remove || 'Remove';
            btn.addEventListener('click', removeLogo);
            drop.appendChild(btn);
        }
    }

    async function removeLogo() {
        showStatus('', '');
        const res = await fetch(deleteUrl, { method: 'POST' });
        const data = await res.json();
        if (!data.ok) {
            showStatus(data.error || 'Error', 'error');
            return;
        }
        const fallback = document.getElementById('company_name')?.value
            || document.getElementById('startup_name')?.value
            || '?';
        preview.innerHTML = `<span class="profile-logo-fallback lg">${fallback.slice(0, 2).toUpperCase()}</span>`;
        document.getElementById('profileLogoRemove')?.remove();
        showStatus(window.IOT_I18N?.profile?.logo_removed || 'Logo removed.', 'info');
    }

    browse?.addEventListener('click', () => input?.click());
    input?.addEventListener('change', () => {
        const file = input.files?.[0];
        if (file) upload(file);
        input.value = '';
    });

    ['dragenter', 'dragover'].forEach((ev) => {
        drop?.addEventListener(ev, (e) => {
            e.preventDefault();
            drop.classList.add('drag-over');
        });
    });
    ['dragleave', 'drop'].forEach((ev) => {
        drop?.addEventListener(ev, (e) => {
            e.preventDefault();
            drop.classList.remove('drag-over');
        });
    });
    drop?.addEventListener('drop', (e) => {
        const file = e.dataTransfer?.files?.[0];
        if (file) upload(file);
    });
    drop?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            input?.click();
        }
    });

    removeBtn?.addEventListener('click', removeLogo);

    const verifyBtn = document.getElementById('profileVerifyBtn');
    const verifySection = document.getElementById('profileVerification');
    if (verifyBtn && verifySection) {
        verifyBtn.addEventListener('click', async () => {
            const siren = document.getElementById('siren')?.value || '';
            const siret = document.getElementById('siret')?.value || '';
            const legalName = document.getElementById('legal_name')?.value || '';
            const companyName = document.getElementById('company_name')?.value
                || document.getElementById('startup_name')?.value
                || legalName;
            verifyBtn.disabled = true;
            verifyBtn.textContent = window.IOT_I18N?.profile?.verify_running || 'Checking…';
            try {
                const res = await fetch(verifySection.dataset.verifyUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        siren,
                        siret,
                        legal_name: legalName,
                        profile_name: companyName,
                    }),
                });
                const data = await res.json();
                const msgEl = document.getElementById('profileVerifyMessage');
                const aiEl = document.getElementById('profileVerifyAi');
                const statusBox = document.getElementById('profileVerifyStatus');
                if (msgEl) {
                    msgEl.hidden = false;
                    msgEl.textContent = data.message || data.error || '';
                }
                if (aiEl && data.ai_summary) {
                    aiEl.hidden = false;
                    aiEl.textContent = data.ai_summary;
                }
                if (statusBox) {
                    statusBox.className = `profile-verify-status profile-verify-${data.status || 'failed'}`;
                    statusBox.innerHTML = data.verified
                        ? `<span class="cdash-status cdash-status-success">✓ ${window.IOT_I18N?.profile?.verified || 'Verified'}</span>`
                        : `<span class="cdash-status cdash-status-danger">${window.IOT_I18N?.profile?.verify_failed || 'Not verified'}</span>`;
                }
                if (data.official) {
                    if (data.official.siren) document.getElementById('siren').value = data.official.siren;
                    if (data.official.siret) document.getElementById('siret').value = data.official.siret;
                    if (data.official.legal_name) document.getElementById('legal_name').value = data.official.legal_name;
                }
            } catch (err) {
                showStatus(err.message, 'error');
            } finally {
                verifyBtn.disabled = false;
                verifyBtn.textContent = window.IOT_I18N?.profile?.verify_btn || 'Verify';
            }
        });
    }
})();
