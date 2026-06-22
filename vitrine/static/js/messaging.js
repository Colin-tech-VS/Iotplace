(function () {
    const root = document.getElementById('uxMessenger');
    if (!root) return;

    const POLL_MS = 5000;
    const urls = {
        poll: root.dataset.pollUrl,
        thread: root.dataset.threadUrl,
        send: root.dataset.sendUrl,
        read: root.dataset.readUrl,
        status: root.dataset.statusUrl,
    };
    const userRole = root.dataset.userRole || '';

    const els = {
        threads: document.getElementById('messengerThreads'),
        unreadTotal: document.getElementById('messengerUnreadTotal'),
        empty: document.getElementById('messengerEmpty'),
        active: document.getElementById('messengerActive'),
        messages: document.getElementById('messengerMessages'),
        peerName: document.getElementById('messengerPeerName'),
        peerMeta: document.getElementById('messengerPeerMeta'),
        form: document.getElementById('messengerForm'),
        input: document.getElementById('messengerInput'),
        appActions: document.getElementById('messengerAppActions'),
        back: document.getElementById('messengerBack'),
        sidebar: document.getElementById('messengerSidebar'),
        chat: document.getElementById('messengerChat'),
    };

    let state = {
        since: new Date().toISOString(),
        conversations: [],
        activeThread: null,
        activeMessages: [],
        polling: null,
        lastUnread: 0,
    };

    function formatTime(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        const now = new Date();
        const isToday = d.toDateString() === now.toDateString();
        return isToday
            ? d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
            : d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function updateBadges(unread) {
        state.lastUnread = unread;
        document.querySelectorAll('[data-msg-badge]').forEach((el) => {
            if (unread > 0) {
                el.textContent = unread > 99 ? '99+' : unread;
                el.hidden = false;
            } else {
                el.hidden = true;
            }
        });
        if (els.unreadTotal) {
            if (unread > 0) {
                els.unreadTotal.textContent = unread;
                els.unreadTotal.hidden = false;
            } else {
                els.unreadTotal.hidden = true;
            }
        }
        const statUnread = document.querySelector('.ux-stat-highlight .ux-stat-value');
        if (statUnread && document.querySelector('[data-tab="messages"]')?.classList.contains('active')) {
            /* keep stat in sync on poll */
        }
        document.querySelectorAll('[data-stat-unread]').forEach((el) => {
            el.textContent = unread;
            const card = el.closest('.ux-stat');
            if (card) card.classList.toggle('ux-stat-highlight', unread > 0);
        });
    }

    function showToast(title, body, type) {
        if (window.IotToast) {
            IotToast.show(body, { title, type: type || 'info' });
            return;
        }
        let container = document.getElementById('msg-toasts');
        if (!container) {
            container = document.createElement('div');
            container.id = 'msg-toasts';
            container.className = 'iot-toast-stack';
            document.body.appendChild(container);
        }
        const toast = document.createElement('div');
        toast.className = 'iot-toast iot-toast--info';
        toast.innerHTML = `<strong>${escapeHtml(title)}</strong><p>${escapeHtml(body)}</p>`;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4500);

        if (Notification.permission === 'granted' && document.hidden) {
            new Notification(title, { body, icon: '/vitrine/static/brand/favicon-32.png' });
        }
    }

    function renderThreads() {
        if (!state.conversations.length) {
            const hint = root.dataset.emptyHint || 'Les conversations apparaîtront ici.';
            els.threads.innerHTML = `
                <div class="ux-messenger-no-threads">
                    <p>Aucune conversation</p>
                    <span class="muted">${escapeHtml(hint)}</span>
                </div>`;
            return;
        }

        els.threads.innerHTML = state.conversations.map((c) => {
            const active = state.activeThread &&
                state.activeThread.counterpart_user_id === c.counterpart_user_id &&
                (state.activeThread.project_id || '') === (c.project_id || '');
            const roleLabel = c.counterpart_role === 'enterprise' ? 'Entreprise' : 'Startup';
            return `
                <button type="button" class="ux-thread-item ${active ? 'active' : ''} ${c.unread ? 'unread' : ''}"
                    data-counterpart="${c.counterpart_user_id}"
                    data-project="${c.project_id || ''}"
                    data-name="${escapeHtml(c.counterpart_name)}"
                    data-role="${c.counterpart_role}">
                    <div class="ux-thread-avatar">${c.counterpart_role === 'enterprise' ? '🏢' : '🚀'}</div>
                    <div class="ux-thread-body">
                        <div class="ux-thread-top">
                            <strong>${escapeHtml(c.counterpart_name)}</strong>
                            <span class="ux-thread-time">${formatTime(c.last_at)}</span>
                        </div>
                        <div class="ux-thread-preview">${escapeHtml(c.last_message)}</div>
                        <div class="ux-thread-meta">
                            <span>${roleLabel}</span>
                            ${c.project_title ? `<span>· ${escapeHtml(c.project_title)}</span>` : ''}
                            ${c.unread ? `<span class="ux-thread-badge">${c.unread}</span>` : ''}
                        </div>
                    </div>
                </button>`;
        }).join('');

        els.threads.querySelectorAll('.ux-thread-item').forEach((btn) => {
            btn.addEventListener('click', () => openThread({
                counterpart_user_id: btn.dataset.counterpart,
                project_id: btn.dataset.project || null,
                counterpart_name: btn.dataset.name,
                counterpart_role: btn.dataset.role,
            }));
        });
    }

    function renderMessages() {
        els.messages.innerHTML = state.activeMessages.map((m) => {
            const mine = m.is_mine;
            const appActions = (!mine && m.kind === 'application' && userRole === 'enterprise' && m.status === 'pending')
                ? `<div class="ux-msg-actions" data-msg-id="${m.id}">
                    <button type="button" class="btn btn-primary btn-sm" data-action="accepted">Accepter</button>
                    <button type="button" class="btn btn-ghost btn-sm" data-action="declined">Refuser</button>
                   </div>`
                : '';
            return `
                <div class="ux-msg ${mine ? 'mine' : 'theirs'} ${!m.read && !mine ? 'unread' : ''}">
                    <div class="ux-msg-bubble">
                        ${m.kind === 'application' ? `<span class="ux-msg-kind">${escapeHtml(m.kind_label)}</span>` : ''}
                        <p>${escapeHtml(m.body)}</p>
                        ${m.status && m.kind === 'application' ? `<span class="status-pill status-${m.status}">${escapeHtml(m.status_label)}</span>` : ''}
                        ${appActions}
                    </div>
                    <time class="ux-msg-time">${formatTime(m.created_at)}</time>
                </div>`;
        }).join('');

        els.messages.querySelectorAll('[data-action]').forEach((btn) => {
            btn.addEventListener('click', () => {
                const wrap = btn.closest('[data-msg-id]');
                updateApplicationStatus(wrap.dataset.msgId, btn.dataset.action);
            });
        });

        els.messages.scrollTop = els.messages.scrollHeight;
    }

    async function openThread(thread) {
        state.activeThread = thread;
        els.empty.hidden = true;
        els.active.hidden = false;
        els.peerName.textContent = thread.counterpart_name || '—';
        const roleLabel = thread.counterpart_role === 'enterprise' ? 'Entreprise' : 'Startup';
        els.peerMeta.textContent = roleLabel;
        els.sidebar?.classList.remove('mobile-open');
        root.classList.add('thread-open');

        const params = new URLSearchParams({ counterpart: thread.counterpart_user_id });
        if (thread.project_id) params.set('project_id', thread.project_id);

        try {
            const res = await fetch(`${urls.thread}?${params}`);
            const data = await res.json();
            if (!data.ok) throw new Error(data.error);
            state.activeMessages = data.messages || [];
            renderMessages();
            renderThreads();
            poll();
        } catch (err) {
            els.messages.innerHTML = `<p class="muted" style="padding:1rem">${escapeHtml(err.message)}</p>`;
        }
    }

    async function sendMessage(body) {
        if (!state.activeThread) return;
        const res = await fetch(urls.send, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                counterpart_user_id: state.activeThread.counterpart_user_id,
                project_id: state.activeThread.project_id || null,
                body,
            }),
        });
        const data = await res.json();
        if (!data.ok) throw new Error(data.error);
        state.activeMessages.push(data.message);
        renderMessages();
        els.input.value = '';
        state.since = new Date().toISOString();
        await poll();
    }

    async function updateApplicationStatus(messageId, status) {
        const url = urls.status.replace('__ID__', messageId);
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
        });
        const data = await res.json();
        if (!data.ok) {
            if (window.IotToast) IotToast.show(data.error || 'Erreur', { type: 'error' });
            else alert(data.error || 'Erreur');
            return;
        }
        if (status === 'accepted') {
            if (window.IotToast) {
                IotToast.show('Candidature acceptée.', { type: 'success' });
            }
        } else if (status === 'declined' && window.IotToast) {
            IotToast.show('Candidature refusée.', { type: 'info' });
        }
        if (status === 'accepted' && data.payment && data.payment.invoice_url) {
            if (confirm('Candidature acceptée. Ouvrir la facture pour paiement (séquestre) ?')) {
                window.open(data.payment.invoice_url, '_blank', 'noopener');
            }
        } else if (status === 'accepted' && data.payment && data.payment.error) {
            if (window.IotToast) {
                IotToast.show('Acceptée, mais facture : ' + data.payment.error, { type: 'warning' });
            } else {
                alert('Acceptée, mais facture : ' + data.payment.error);
            }
        }
        const idx = state.activeMessages.findIndex((m) => m.id === messageId);
        if (idx >= 0) state.activeMessages[idx] = data.message;
        renderMessages();
        await poll();
    }

    async function poll() {
        try {
            const res = await fetch(`${urls.poll}?since=${encodeURIComponent(state.since)}`);
            const data = await res.json();
            if (!data.ok) return;

            state.conversations = data.conversations || [];
            updateBadges(data.unread || 0);
            renderThreads();

            const notifications = data.notifications || [];
            if (notifications.length) {
                notifications.forEach((n) => {
                    if (!state.activeThread || n.from_user_id !== state.activeThread.counterpart_user_id) {
                        showToast(n.counterpart_name || 'Nouveau message', (n.body || '').slice(0, 80));
                    }
                });
                if (state.activeThread) {
                    const params = new URLSearchParams({ counterpart: state.activeThread.counterpart_user_id });
                    if (state.activeThread.project_id) params.set('project_id', state.activeThread.project_id);
                    const tRes = await fetch(`${urls.thread}?${params}`);
                    const tData = await tRes.json();
                    if (tData.ok) {
                        state.activeMessages = tData.messages || [];
                        renderMessages();
                    }
                }
            }

            state.since = data.server_time || new Date().toISOString();
        } catch (_) { /* silent */ }
    }

    els.form?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const body = els.input.value.trim();
        if (!body) return;
        els.input.disabled = true;
        try {
            await sendMessage(body);
            if (window.IotToast) IotToast.show('Message envoyé.', { type: 'success' });
        } catch (err) {
            if (window.IotToast) IotToast.show(err.message, { type: 'error' });
            else alert(err.message);
        } finally {
            els.input.disabled = false;
            els.input.focus();
        }
    });

    els.back?.addEventListener('click', () => {
        state.activeThread = null;
        els.active.hidden = true;
        els.empty.hidden = false;
        root.classList.remove('thread-open');
    });

    els.input?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            els.form.requestSubmit();
        }
    });

    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }

    window.IotMessenger = {
        openThread,
        poll,
        openMessagesTab() {
            document.querySelector('[data-tab="messages"]')?.click();
        },
    };

    poll();
    state.polling = setInterval(poll, POLL_MS);
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) poll();
    });

    const pending = sessionStorage.getItem('openChat');
    if (pending) {
        try {
            const t = JSON.parse(pending);
            sessionStorage.removeItem('openChat');
            setTimeout(() => openThread({
                counterpart_user_id: t.counterpart,
                project_id: t.project || null,
                counterpart_name: t.name,
                counterpart_role: t.role,
            }), 400);
        } catch (_) {}
    }
})();
