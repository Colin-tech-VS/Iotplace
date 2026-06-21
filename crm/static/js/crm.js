const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebarOverlay = document.getElementById('sidebarOverlay');

function closeSidebar() {
    sidebar?.classList.remove('open');
    sidebarOverlay?.classList.remove('visible');
}

sidebarToggle?.addEventListener('click', () => {
    sidebar?.classList.toggle('open');
    sidebarOverlay?.classList.toggle('visible');
});

sidebarOverlay?.addEventListener('click', closeSidebar);

document.querySelectorAll('[data-confirm]').forEach(form => {
    form.addEventListener('submit', e => {
        const msg = form.dataset.confirm || 'Confirmer ?';
        if (!confirm(msg)) e.preventDefault();
    });
});

document.querySelectorAll('.toast').forEach(toast => {
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
});
