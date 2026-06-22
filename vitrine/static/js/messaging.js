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
    const i18n = () => (window.IOT_I18N && window.IOT_I18N.messenger) || {};
    const uiLocale = () => ((window.IOT_I18N && window.IOT_I18N.locale) === 'en' ? 'en-US' : 'fr-FR');

    const els = {
        threads: document.getElementById('messengerThreads'),
        unreadTotal: document.getElementById('messengerUnreadTotal'),
        empty: document.getElementById('messengerEmpty'),
        active: document.getElementById('messengerActive'),
        messages: document.getElementById('messengerMessages'),
        peerName: document.getElementById('messengerPeerName'),
        peerMeta: document.getElementById('messengerPeerMeta'),
        peerAvatar: document.getElementById('messengerPeerAvatar'),
        form: document.getElementById('messengerForm'),
        input: document.getElementById('messengerInput'),
        search: document.getElementById('messengerSearch'),
        appActions: document.getElementById('messengerAppActions'),
        back: document.getElementById('messengerBack'),
        sidebar: document.getElementById('messengerSidebar'),
    };

    let state = {
        since: new Date().toISOString(),
        conversations: [],
        activeThread: null,
        activeMessages: [],
        polling: null,
        searchQuery: '',
    };

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function initials(name) {
        const parts = (name || '?').trim().split(/\s+/).filter(Boolean);
        if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
        return (parts[0] || '?').slice(0, 2).toUpperCase();
    }

    function formatTime(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        const now = new Date();
        const isToday = d.toDateString() === now.toDateString();
        return isToday
            ? d.toLocaleTimeString(uiLocale(), { hour: '2-digit', minute: '2-digit' })
            : d.toLocaleDateString(uiLocale(), { day: 'numeric', month: 'short' });
    }

    function dayLabel(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        const now = new Date();
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        if (d.toDateString() === now.toDateString()) return i18n().today || 'Today';
        if (d.toDateString() === yesterday.toDateString()) return i18n().yesterday || 'Yesterday';
        return d.toLocaleDateString(uiLocale(), { weekday: 'long', day: 'numeric', month: 'long' });
    }

    function roleClass(role) {
        return role === 'enterprise' ? 'enterprise' : 'startup';
    }

    function roleLabel(role) {
        return role === 'enterprise'
            ? (i18n().role_enterprise || 'Enterprise')
            : (i18n().role_startup || 'Startup');
    }

    function filteredConversations() {
        const q = state.searchQuery.trim().toLowerCase();
        if (!q) return state.conversations;
        return state.conversations.filter((c) => {
            const hay = [
                c.counterpart_name,
                c.project_title,
                c.last_message,
                roleLabel(c.counterpart_role),
            ].join(' ').toLowerCase();
            return hay.includes(q);
        });
    }

    function autoResizeInput() {
        if (!els.input) return;
        els.input.style.height = 'auto';
        els.input.style.height = `${Math.min(els.input.scrollHeight, 140)}px`;
    }

    function updateBadges(unread) {
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
                els.unreadTotal.textContent = unread > 99 ? '99+' : unread;
                els.unreadTotal.hidden = false;
            } else {
                els.unreadTotal.hidden = true;
            }
        }
        document.querySelectorAll('[data-stat-unread]').forEach((el) => {
            el.textContent = unread;
            const card = el.closest('.ux-stat');
            if (card) card.classList.toggle('ux-stat-highlight', unread > 0);
        });
    }

    function showToast(title, body) {
        if (window.IotToast) {
            IotToast.show(body, { title, type: 'info' });
            return;
        }
        if (Notification.permission === 'granted' && document.hidden) {
            new Notification(title, { body, icon: '/vitrine/static/brand/favicon-32.png' });
        }
    }

    function renderThreads() {
        const list = filteredConversations();
        if (!list.length) {
            const hint = root.dataset.emptyHint || '';
            const noMatch = state.searchQuery.trim() && state.conversations.length;
            els.threads.innerHTML = `
                <div class="msg-no-threads">
                    <p>${escapeHtml(noMatch ? (i18n().no_search || 'No results') : (i18n().no_threads || 'No conversations'))}</p>
                    ${noMatch ? '' : `<span class="muted">${escapeHtml(hint)}</span>`}
                </div>`;
            return;
        }

        els.threads.innerHTML = list.map((c) => {
            const active = state.activeThread &&
                state.activeThread.counterpart_user_id === c.counterpart_user_id &&
                (state.activeThread.project_id || '') === (c.project_id || '');
            const rc = roleClass(c.counterpart_role);
            return `
                <button type="button" class="msg-thread ${active ? 'active' : ''} ${c.unread ? 'unread' : ''}" role="listitem"
                    data-counterpart="${c.counterpart_user_id}"
                    data-project="${c.project_id || ''}"
                    data-name="${escapeHtml(c.counterpart_name)}"
                    data-role="${c.counterpart_role}"
                    data-project-title="${escapeHtml(c.project_title || '')}">
                    <div class="msg-thread-avatar ${rc}">${escapeHtml(initials(c.counterpart_name))}</div>
                    <div class="msg-thread-body">
                        <div class="msg-thread-top">
                            <span class="msg-thread-name">${escapeHtml(c.counterpart_name)}</span>
                            <span class="msg-thread-time">${formatTime(c.last_at)}</span>
                        </div>
                        <div class="msg-thread-preview">${escapeHtml(c.last_message)}</div>
                        <div class="msg-thread-foot">
                            <span class="msg-thread-role">${escapeHtml(roleLabel(c.counterpart_role))}</span>
                            ${c.project_title ? `<span class="msg-thread-project">${escapeHtml(c.project_title)}</span>` : ''}
                            ${c.unread ? `<span class="msg-thread-badge">${c.unread}</span>` : ''}
                        </div>
                    </div>
                </button>`;
        }).join('');

        els.threads.querySelectorAll('.msg-thread').forEach((btn) => {
            btn.addEventListener('click', () => openThread({
                counterpart_user_id: btn.dataset.counterpart,
                project_id: btn.dataset.project || null,
                counterpart_name: btn.dataset.name,
                counterpart_role: btn.dataset.role,
                project_title: btn.dataset.projectTitle || '',
            }));
        });
    }

    function renderMessages() {
        let lastDay = '';
        const parts = [];

        state.activeMessages.forEach((m) => {
            const day = m.created_at ? new Date(m.created_at).toDateString() : '';
            if (day && day !== lastDay) {
                lastDay = day;
                parts.push(`<div class="msg-day-sep">${escapeHtml(dayLabel(m.created_at))}</div>`);
            }

            const mine = m.is_mine;
            const isApp = m.kind === 'application';
            const appActions = (!mine && isApp && userRole === 'enterprise' && m.status === 'pending')
                ? `<div class="msg-actions" data-msg-id="${m.id}">
                    <button type="button" class="btn btn-primary btn-sm" data-action="accepted">${escapeHtml(i18n().accept || 'Accept')}</button>
                    <button type="button" class="btn btn-ghost btn-sm" data-action="declined">${escapeHtml(i18n().decline || 'Decline')}</button>
                   </div>`
                : '';

            parts.push(`
                <div class="msg-row ${mine ? 'mine' : 'theirs'} ${isApp ? 'application' : ''} ${!m.read && !mine ? 'unread' : ''}">
                    <div class="msg-bubble">
                        ${isApp ? `<span class="msg-kind">${escapeHtml(m.kind_label || i18n().application || 'Application')}</span>` : ''}
                        <p>${escapeHtml(m.body)}</p>
                        ${m.status && isApp ? `<span class="status-pill status-${m.status}">${escapeHtml(m.status_label)}</span>` : ''}
                        ${appActions}
                    </div>
                    <time class="msg-time">${formatTime(m.created_at)}</time>
                </div>`);
        });

        els.messages.innerHTML = parts.join('');

        els.messages.querySelectorAll('[data-action]').forEach((btn) => {
            btn.addEventListener('click', () => {
                const wrap = btn.closest('[data-msg-id]');
                updateApplicationStatus(wrap.dataset.msgId, btn.dataset.action);
            });
        });

        els.messages.scrollTop = els.messages.scrollHeight;
    }

    function setPeerHeader(thread) {
        const rc = roleClass(thread.counterpart_role);
        els.peerName.textContent = thread.counterpart_name || '—';
        if (els.peerAvatar) {
            els.peerAvatar.textContent = initials(thread.counterpart_name);
            els.peerAvatar.className = `msg-peer-avatar ${rc}`;
        }
        const parts = [roleLabel(thread.counterpart_role)];
        if (thread.project_title) parts.push(thread.project_title);
        els.peerMeta.textContent = parts.join(' · ');
    }

    async function openThread(thread) {
        state.activeThread = thread;
        els.empty.hidden = true;
        els.active.hidden = false;
        setPeerHeader(thread);
        root.classList.add('thread-open');

        const params = new URLSearchParams({ counterpart: thread.counterpart_user_id });
        if (thread.project_id) params.set('project_id', thread.project_id);

        els.messages.innerHTML = `<div class="msg-loading"><span class="msg-loading-dot"></span><span class="msg-loading-dot"></span><span class="msg-loading-dot"></span></div>`;

        try {
            const res = await fetch(`${urls.thread}?${params}`);
            const data = await res.json();
            if (!data.ok) throw new Error(data.error);
            state.activeMessages = data.messages || [];
            const conv = state.conversations.find((c) =>
                c.counterpart_user_id === thread.counterpart_user_id &&
                (c.project_id || '') === (thread.project_id || '')
            );
            if (conv && !thread.project_title) {
                thread.project_title = conv.project_title || '';
                setPeerHeader(thread);
            }
            renderMessages();
            renderThreads();
            await poll();
            els.input?.focus();
        } catch (err) {
            els.messages.innerHTML = `<p class="msg-no-threads">${escapeHtml(err.message)}</p>`;
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
        autoResizeInput();
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
            if (window.IotToast) IotToast.show(data.error || i18n().generic_error || 'Error', { type: 'error' });
            else alert(data.error || i18n().generic_error || 'Error');
            return;
        }
        if (status === 'accepted') {
            if (window.IotToast) IotToast.show(i18n().app_accepted || 'Application accepted.', { type: 'success' });
        } else if (status === 'declined' && window.IotToast) {
            IotToast.show(i18n().app_declined || 'Application declined.', { type: 'info' });
        }
        if (status === 'accepted' && data.payment?.invoice_url) {
            if (confirm(i18n().invoice_confirm || 'Open invoice for escrow payment?')) {
                window.open(data.payment.invoice_url, '_blank', 'noopener');
            }
        } else if (status === 'accepted' && data.payment?.error) {
            const tpl = i18n().invoice_warning || 'Accepted, but invoice: {error}';
            if (window.IotToast) IotToast.show(tpl.replace('{error}', data.payment.error), { type: 'warning' });
            else alert(tpl.replace('{error}', data.payment.error));
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
                        showToast(n.counterpart_name || i18n().new_message || 'New message', (n.body || '').slice(0, 80));
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
        const sendBtn = document.getElementById('messengerSendBtn');
        els.input.disabled = true;
        if (sendBtn) sendBtn.disabled = true;
        try {
            await sendMessage(body);
        } catch (err) {
            if (window.IotToast) IotToast.show(err.message, { type: 'error' });
            else alert(err.message);
        } finally {
            els.input.disabled = false;
            if (sendBtn) sendBtn.disabled = false;
            els.input.focus();
        }
    });

    els.back?.addEventListener('click', () => {
        state.activeThread = null;
        els.active.hidden = true;
        els.empty.hidden = false;
        root.classList.remove('thread-open');
    });

    els.input?.addEventListener('input', autoResizeInput);

    els.input?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            els.form.requestSubmit();
        }
    });

    els.search?.addEventListener('input', () => {
        state.searchQuery = els.search.value;
        renderThreads();
    });

    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }

    window.IotMessenger = {
        openThread,
        poll,
        refresh: poll,
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
                project_title: t.project_title || '',
            }), 400);
        } catch (_) {
            sessionStorage.removeItem('openChat');
        }
    }
})();
