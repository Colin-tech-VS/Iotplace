(function (global) {
    const DEFAULT_DURATION = 4800;
    const TITLES = {
        success: 'Succès',
        info: 'Info',
        warning: 'Attention',
        error: 'Erreur',
    };
    const ICONS = {
        success: '✓',
        info: 'i',
        warning: '!',
        error: '×',
    };

    function normalizeType(category) {
        const c = (category || 'info').toLowerCase();
        if (c === 'message' || c === 'notice') return 'info';
        if (c === 'danger') return 'error';
        if (['success', 'info', 'warning', 'error'].includes(c)) return c;
        return 'info';
    }

    function ensureStack() {
        let stack = document.getElementById('iot-toast-stack');
        if (!stack) {
            stack = document.createElement('div');
            stack.id = 'iot-toast-stack';
            stack.className = 'iot-toast-stack';
            stack.setAttribute('aria-live', 'polite');
            stack.setAttribute('aria-atomic', 'false');
            document.body.appendChild(stack);
        }
        return stack;
    }

    function dismiss(toast, delay) {
        if (!toast || toast.dataset.dismissed === '1') return;
        toast.dataset.dismissed = '1';
        setTimeout(() => {
            toast.classList.add('iot-toast-out');
            setTimeout(() => toast.remove(), 360);
        }, delay || 0);
    }

    function show(message, options) {
        const opts = options || {};
        const type = normalizeType(opts.type || opts.category || 'info');
        const title = opts.title || TITLES[type] || TITLES.info;
        const duration = opts.duration == null ? DEFAULT_DURATION : opts.duration;
        const stack = ensureStack();

        const toast = document.createElement('div');
        toast.className = `iot-toast iot-toast--${type}`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <span class="iot-toast-icon" aria-hidden="true">${ICONS[type] || ICONS.info}</span>
            <div class="iot-toast-body">
                <p class="iot-toast-title">${escapeHtml(title)}</p>
                <p class="iot-toast-message">${escapeHtml(String(message || ''))}</p>
            </div>
            <button type="button" class="iot-toast-close" aria-label="Fermer">&times;</button>
        `;

        toast.querySelector('.iot-toast-close')?.addEventListener('click', () => dismiss(toast));
        stack.appendChild(toast);

        if (duration > 0) {
            dismiss(toast, duration);
        }
        return toast;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function hydrateFromFlashes() {
        document.querySelectorAll('[data-iot-flash]').forEach((node) => {
            const type = node.dataset.iotFlash || 'info';
            const title = node.dataset.iotFlashTitle || '';
            const message = node.textContent.trim();
            if (message) {
                show(message, { type, title: title || undefined });
            }
            node.remove();
        });

        document.querySelectorAll('.flash-container, #toasts, .crm-login-flashes').forEach((container) => {
            container.querySelectorAll('.flash, .toast, .crm-login-flash').forEach((node) => {
                const classes = node.className;
                let type = 'info';
                if (classes.includes('success')) type = 'success';
                else if (classes.includes('error')) type = 'error';
                else if (classes.includes('warning')) type = 'warning';
                else if (classes.includes('info')) type = 'info';
                const message = node.textContent.trim();
                if (message) show(message, { type });
            });
            container.remove();
        });
    }

    const IotToast = { show, dismiss, hydrateFromFlashes, normalizeType };
    global.IotToast = IotToast;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', hydrateFromFlashes);
    } else {
        hydrateFromFlashes();
    }
})(window);
