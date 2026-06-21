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
    let typewriterToken = 0;

    const CHARS_PER_MS = 0.14;
    const PAUSE_SENTENCE_MS = 22;
    const PAUSE_COMMA_MS = 10;
    const MIN_CHARS_PER_FRAME = 2;
    const MAX_CHARS_PER_FRAME = 8;

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

    function escapeHtml(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function trimIncompleteMarkdown(text) {
        return text
            .replace(/\*\*[^*]*$/, '')
            .replace(/\*[^*]*$/, '')
            .replace(/\[([^\]]*)?$/, '');
    }

    function formatBotMessage(text) {
        let html = escapeHtml(text);
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="advisor-em">$1</strong>');
        html = html.replace(
            /(https?:\/\/[^\s<&]+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        const blocks = html.split(/\n\n+/).filter(Boolean);
        if (blocks.length > 1) {
            return blocks.map(block => `<p>${block.replace(/\n/g, '<br>')}</p>`).join('');
        }
        return html.replace(/\n/g, '<br>');
    }

    function scrollMessages(smooth) {
        if (smooth) {
            messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: 'smooth' });
        } else {
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }
    }

    let scrollRaf = 0;
    function scrollMessagesThrottled() {
        if (scrollRaf) return;
        scrollRaf = requestAnimationFrame(() => {
            scrollRaf = 0;
            messagesEl.scrollTop = messagesEl.scrollHeight;
        });
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
        scrollMessages();
        return el;
    }

    function createBotBubble(extraClass) {
        const el = document.createElement('div');
        el.className = `advisor-msg advisor-msg-bot${extraClass ? ' ' + extraClass : ''}`;
        messagesEl.appendChild(el);
        scrollMessages();
        return el;
    }

    function punctuationPause(text, from, to) {
        const chunk = text.slice(from, to);
        if (/[.!?…](?:\s|$)/.test(chunk)) return PAUSE_SENTENCE_MS;
        if (/[,;:\n]/.test(chunk)) return PAUSE_COMMA_MS;
        return 0;
    }

    function typewriterBotMessage(el, fullText) {
        const token = ++typewriterToken;
        el.classList.add('advisor-msg-typing');
        let index = 0;
        let pauseUntil = 0;
        let lastTime = 0;
        let charCarry = 0;

        return new Promise(resolve => {
            function frame(now) {
                if (token !== typewriterToken) {
                    resolve();
                    return;
                }

                if (!lastTime) lastTime = now;
                if (now < pauseUntil) {
                    requestAnimationFrame(frame);
                    return;
                }

                const dt = Math.min(now - lastTime, 48);
                lastTime = now;
                charCarry += dt * CHARS_PER_MS;

                let advance = Math.floor(charCarry);
                if (advance < MIN_CHARS_PER_FRAME && index < fullText.length) {
                    requestAnimationFrame(frame);
                    return;
                }
                advance = Math.min(
                    Math.max(advance, MIN_CHARS_PER_FRAME),
                    MAX_CHARS_PER_FRAME,
                    fullText.length - index
                );
                charCarry -= advance;

                const prev = index;
                index += advance;

                if (index >= fullText.length) {
                    el.innerHTML = formatBotMessage(fullText);
                    el.classList.remove('advisor-msg-typing');
                    scrollMessages(true);
                    resolve();
                    return;
                }

                const pause = punctuationPause(fullText, prev, index);
                if (pause) pauseUntil = now + pause;

                const visible = trimIncompleteMarkdown(fullText.slice(0, index));
                el.innerHTML = `${formatBotMessage(visible)}<span class="advisor-cursor" aria-hidden="true"></span>`;
                scrollMessagesThrottled();
                requestAnimationFrame(frame);
            }
            requestAnimationFrame(frame);
        });
    }

    async function appendBotMessage(text, extraClass, animate) {
        const el = createBotBubble(extraClass);
        if (animate && text && !extraClass?.includes('thinking')) {
            await typewriterBotMessage(el, text);
        } else {
            el.innerHTML = formatBotMessage(text);
        }
        return el;
    }

    function showWelcome() {
        const text = userType === 'startup' ? cfg.i18n.welcomeStartup : cfg.i18n.welcomeEnterprise;
        appendBotMessage(text, '', true);
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
        typewriterToken += 1;
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
        const thinking = createBotBubble('advisor-msg-thinking');
        thinking.innerHTML = `<span class="advisor-thinking-dots">${escapeHtml(cfg.i18n.thinking)}<span class="advisor-dot">.</span><span class="advisor-dot">.</span><span class="advisor-dot">.</span></span>`;

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
                await appendBotMessage(data.error || cfg.i18n.errorGeneric, '', true);
                return;
            }

            await appendBotMessage(data.reply, '', true);
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
            await appendBotMessage(cfg.i18n.errorGeneric, '', true);
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
