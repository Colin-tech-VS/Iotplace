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
    const sendBtn = document.getElementById('advisor-send');
    const profileBtns = root.querySelectorAll('.advisor-profile-btn');

    let userType = 'enterprise';
    let history = [];
    let busy = false;
    let typewriterToken = 0;
    let pendingRequest = null;

    const CHARS_PER_MS = 0.28;
    const PAUSE_SENTENCE_MS = 16;
    const PAUSE_COMMA_MS = 7;
    const MIN_CHARS_PER_FRAME = 2;
    const MAX_CHARS_PER_FRAME = 14;

    function openPanel() {
        root.classList.add('open');
        panel.hidden = false;
        overlay.hidden = false;
        fab.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
        if (!messagesEl.children.length) showWelcome();
        renderSuggestions();
        autoResizeInput();
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

    function autoResizeInput() {
        input.style.height = 'auto';
        const next = Math.min(input.scrollHeight, 140);
        input.style.height = `${Math.max(48, next)}px`;
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

    function wrapMessage(role, bubbleEl) {
        const row = document.createElement('div');
        row.className = `advisor-msg-row advisor-msg-row-${role}`;
        if (role === 'bot') {
            const avatar = document.createElement('div');
            avatar.className = 'advisor-avatar';
            avatar.setAttribute('aria-hidden', 'true');
            row.appendChild(avatar);
        }
        row.appendChild(bubbleEl);
        messagesEl.appendChild(row);
        scrollMessages();
        return bubbleEl;
    }

    function appendMessage(role, content, extraClass) {
        const el = document.createElement('div');
        el.className = `advisor-msg advisor-msg-${role}${extraClass ? ' ' + extraClass : ''}`;
        if (role === 'bot') {
            el.innerHTML = formatBotMessage(content);
        } else {
            el.textContent = content;
        }
        wrapMessage(role, el);
        return el;
    }

    function createBotBubble(extraClass) {
        const el = document.createElement('div');
        el.className = `advisor-msg advisor-msg-bot${extraClass ? ' ' + extraClass : ''}`;
        wrapMessage('bot', el);
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
        if (pendingRequest) {
            pendingRequest.abort();
            pendingRequest = null;
        }
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

    function setBusyState(isBusy) {
        busy = isBusy;
        input.disabled = isBusy;
        sendBtn.disabled = isBusy;
        sendBtn.classList.toggle('is-loading', isBusy);
        if (!isBusy) {
            input.focus();
        }
    }

    function renderSuggestionList(list) {
        if (!list?.length) return;
        suggestionsEl.innerHTML = '';
        list.forEach(s => {
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

    // Render streamed text live into a bubble, throttled to one paint per frame.
    function liveRenderer(el) {
        let full = '';
        let raf = 0;
        const paint = () => {
            raf = 0;
            const visible = trimIncompleteMarkdown(full);
            el.innerHTML = `${formatBotMessage(visible)}<span class="advisor-cursor" aria-hidden="true"></span>`;
            scrollMessagesThrottled();
        };
        return {
            push(chunk) {
                full += chunk;
                if (!raf) raf = requestAnimationFrame(paint);
            },
            finalize() {
                if (raf) { cancelAnimationFrame(raf); raf = 0; }
                el.innerHTML = formatBotMessage(full);
                el.classList.remove('advisor-msg-typing');
                scrollMessages(true);
                return full;
            },
            get text() { return full; },
        };
    }

    async function streamMessage(text) {
        pendingRequest = new AbortController();
        const res = await fetch(cfg.streamUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
            signal: pendingRequest.signal,
            body: JSON.stringify({
                user_type: userType,
                message: text,
                history: history.slice(0, -1).slice(-10),
            }),
        });
        if (!res.ok || !res.body) {
            throw new Error('stream-unavailable');
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let bubble = null;
        let renderer = null;
        let gotError = null;

        const handleEvent = (block) => {
            const lines = block.split('\n');
            let eventName = 'message';
            let dataStr = '';
            for (const line of lines) {
                if (line.startsWith('event:')) eventName = line.slice(6).trim();
                else if (line.startsWith('data:')) dataStr += line.slice(5).trim();
            }
            if (!dataStr) return;
            let data = {};
            try { data = JSON.parse(dataStr); } catch (_) { return; }

            if (eventName === 'meta') {
                if (data.suggestions) renderSuggestionList(data.suggestions);
            } else if (eventName === 'delta') {
                if (!bubble) {
                    bubble = createBotBubble();
                    bubble.classList.add('advisor-msg-typing');
                    renderer = liveRenderer(bubble);
                }
                renderer.push(data.text || '');
            } else if (eventName === 'error') {
                gotError = data.error || cfg.i18n.errorGeneric;
            }
        };

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            let idx;
            while ((idx = buffer.indexOf('\n\n')) !== -1) {
                const block = buffer.slice(0, idx);
                buffer = buffer.slice(idx + 2);
                handleEvent(block);
            }
        }

        if (gotError) {
            if (renderer) renderer.finalize();
            else await appendBotMessage(gotError, '', true);
            return null;
        }
        if (!renderer) return null;
        return renderer.finalize();
    }

    async function sendMessage(text) {
        if (busy || !text.trim()) return;
        const clean = text.trim();
        setBusyState(true);

        appendMessage('user', clean);
        history.push({ role: 'user', content: clean });
        const thinking = createBotBubble('advisor-msg-thinking');
        thinking.innerHTML = `<span class="advisor-thinking-dots">${escapeHtml(cfg.i18n.thinking)}<span class="advisor-dot">.</span><span class="advisor-dot">.</span><span class="advisor-dot">.</span></span>`;

        try {
            let reply = null;
            try {
                reply = await streamMessage(clean);
                thinking.remove();
            } catch (streamErr) {
                if (streamErr && streamErr.name === 'AbortError') { thinking.remove(); return; }
                // Streaming unavailable (proxy/buffering/old browser): fall back
                // to the blocking endpoint so the advisor still answers.
                const res = await fetch(cfg.chatUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    signal: pendingRequest ? pendingRequest.signal : undefined,
                    body: JSON.stringify({
                        user_type: userType,
                        message: clean,
                        history: history.slice(0, -1).slice(-10),
                    }),
                });
                const data = await res.json();
                thinking.remove();
                if (!res.ok || !data.ok) {
                    await appendBotMessage(data.error || cfg.i18n.errorGeneric, '', true);
                    return;
                }
                await appendBotMessage(data.reply, '', true);
                renderSuggestionList(data.suggestions);
                reply = data.reply;
            }

            if (reply) history.push({ role: 'assistant', content: reply });
        } catch (err) {
            thinking.remove();
            if (err && err.name === 'AbortError') return;
            await appendBotMessage(cfg.i18n.errorGeneric, '', true);
        } finally {
            pendingRequest = null;
            setBusyState(false);
            input.value = '';
            autoResizeInput();
            updateSendEnabled();
        }
    }

    function updateSendEnabled() {
        if (busy) return;
        sendBtn.disabled = !input.value.trim();
    }

    function warmStarter() {
        if (messagesEl.children.length) return;
        showWelcome();
        renderSuggestions();
    }

    if ('requestIdleCallback' in window) {
        window.requestIdleCallback(warmStarter, { timeout: 1200 });
    } else {
        setTimeout(warmStarter, 800);
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

    input.addEventListener('input', () => {
        autoResizeInput();
        updateSendEnabled();
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && root.classList.contains('open')) closePanel();
    });

    autoResizeInput();
    updateSendEnabled();
})();
