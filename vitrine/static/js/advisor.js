(function () {
    const cfg = window.IOTPLACE_ADVISOR;
    const root = document.getElementById('advisor-root');
    if (!cfg || !root) return;

    const fab = document.getElementById('advisor-fab');
    const panel = document.getElementById('advisor-panel');
    const overlay = document.getElementById('advisor-overlay');
    const closeBtn = document.getElementById('advisor-close');
    const messagesEl = document.getElementById('advisor-messages');
    const suggestionsEl = document.getElementById('advisor-suggestions');
    const form = document.getElementById('advisor-form');
    const input = document.getElementById('advisor-input');
    const profileBtns = root.querySelectorAll('.advisor-profile-btn');

    let userType = 'enterprise';
    let history = [];
    let busy = false;

    function openPanel() {
        root.classList.add('open');
        panel.hidden = false;
        overlay.hidden = false;
        fab.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
        if (!messagesEl.children.length) showWelcome();
        renderSuggestions();
        input.focus();
    }

    function closePanel() {
        root.classList.remove('open');
        fab.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
        setTimeout(() => {
            if (!root.classList.contains('open')) {
                panel.hidden = true;
                overlay.hidden = true;
            }
        }, 350);
    }

    function formatBotMessage(text) {
        const escaped = escapeHtml(text);
        return escaped.replace(
            /(https?:\/\/[^\s<&]+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
    }

    function appendMessage(role, content, extraClass) {
        const el = document.createElement('div');
        el.className = `advisor-msg advisor-msg-${role}${extraClass ? ' ' + extraClass : ''}`;
        if (role === 'bot') {
            el.innerHTML = formatBotMessage(content);
        } else {
            el.textContent = content;
        }
        messagesEl.appendChild(el);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return el;
    }

    function escapeHtml(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function showWelcome() {
        const text = userType === 'startup' ? cfg.i18n.welcomeStartup : cfg.i18n.welcomeEnterprise;
        appendMessage('bot', text);
    }

    function renderSuggestions() {
        const list = userType === 'startup' ? cfg.i18n.suggestionsStartup : cfg.i18n.suggestionsEnterprise;
        suggestionsEl.innerHTML = '';
        (list || []).forEach(text => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'advisor-chip';
            btn.textContent = text;
            btn.addEventListener('click', () => {
                input.value = text;
                form.requestSubmit();
            });
            suggestionsEl.appendChild(btn);
        });
    }

    function setProfile(type) {
        userType = type;
        profileBtns.forEach(btn => {
            const active = btn.dataset.profile === type;
            btn.classList.toggle('active', active);
            btn.setAttribute('aria-selected', active ? 'true' : 'false');
        });
        messagesEl.innerHTML = '';
        history = [];
        showWelcome();
        renderSuggestions();
    }

    async function sendMessage(text) {
        if (busy || !text.trim()) return;
        busy = true;
        input.disabled = true;

        appendMessage('user', text.trim());
        history.push({ role: 'user', content: text.trim() });
        const thinking = appendMessage('bot', cfg.i18n.thinking, 'advisor-msg-thinking');

        try {
            const res = await fetch(cfg.chatUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_type: userType,
                    message: text.trim(),
                    history: history.slice(0, -1),
                }),
            });
            const data = await res.json();
            thinking.remove();

            if (!res.ok || !data.ok) {
                appendMessage('bot', data.error || cfg.i18n.errorGeneric);
                return;
            }

            appendMessage('bot', data.reply);
            history.push({ role: 'assistant', content: data.reply });
            if (data.suggestions?.length) {
                suggestionsEl.innerHTML = '';
                data.suggestions.forEach(s => {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'advisor-chip';
                    btn.textContent = s;
                    btn.addEventListener('click', () => {
                        input.value = s;
                        form.requestSubmit();
                    });
                    suggestionsEl.appendChild(btn);
                });
            }
        } catch (_) {
            thinking.remove();
            appendMessage('bot', cfg.i18n.errorGeneric);
        } finally {
            busy = false;
            input.disabled = false;
            input.value = '';
            input.focus();
        }
    }

    fab.addEventListener('click', openPanel);
    closeBtn.addEventListener('click', closePanel);
    overlay.addEventListener('click', closePanel);

    profileBtns.forEach(btn => {
        btn.addEventListener('click', () => setProfile(btn.dataset.profile));
    });

    form.addEventListener('submit', e => {
        e.preventDefault();
        sendMessage(input.value);
    });

    input.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            form.requestSubmit();
        }
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && root.classList.contains('open')) closePanel();
    });
})();
