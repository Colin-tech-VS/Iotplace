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

document.querySelectorAll('.kpi-card').forEach((card, i) => {
    card.classList.add('iot-enter');
    card.style.animationDelay = `${i * 0.06}s`;
});

const crmReveal = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
            entry.target.style.animationDelay = `${i * 0.05}s`;
            entry.target.classList.add('iot-enter');
            crmReveal.unobserve(entry.target);
        }
    });
}, { threshold: 0.08 });

document.querySelectorAll('.table-card:not(.kpi-card)').forEach(el => {
    el.style.opacity = '0';
    crmReveal.observe(el);
});
