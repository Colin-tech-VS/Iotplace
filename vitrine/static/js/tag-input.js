(function () {
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function renderTags(input) {
        const preview = input.parentElement.querySelector('.tag-preview');
        if (!preview) return;
        const tags = input.value.split(',').map((t) => t.trim()).filter(Boolean);
        if (!tags.length) {
            preview.innerHTML = '<span class="tag-preview-hint">Séparez les compétences avec des virgules pour créer des badges</span>';
            return;
        }
        preview.innerHTML = tags.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join('');
    }

    document.querySelectorAll('.tag-input').forEach((input) => {
        renderTags(input);
        input.addEventListener('input', () => renderTags(input));
    });
})();
