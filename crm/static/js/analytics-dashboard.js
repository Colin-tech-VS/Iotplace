(function () {
    const panel = document.getElementById('realtimePanel');
    if (!panel) return;

    const els = {
        active: document.getElementById('rtActive'),
        views30: document.getElementById('rtViews30'),
        updated: document.getElementById('rtUpdated'),
        chart: document.getElementById('minuteChart'),
        pages: document.getElementById('rtPagesTable')?.querySelector('tbody'),
        feed: document.getElementById('liveFeed'),
    };

    function formatTime(iso) {
        if (!iso) return '—';
        return iso.slice(11, 19);
    }

    function renderChart(data) {
        if (!els.chart) return;
        const max = Math.max(...data.map(d => d.views), 1);
        els.chart.innerHTML = data.map(bar => {
            const h = Math.max(4, Math.round((bar.views / max) * 56));
            return `<div class="minute-bar" style="height:${h}px" title="${bar.label}: ${bar.views}">
                <span class="minute-label">${bar.views ? bar.label.slice(-5) : ''}</span>
            </div>`;
        }).join('');
    }

    function renderPages(pages) {
        if (!els.pages) return;
        if (!pages.length) {
            els.pages.innerHTML = '<tr><td colspan="2" class="muted">En attente de visites…</td></tr>';
            return;
        }
        els.pages.innerHTML = pages.map(p =>
            `<tr><td>${p.label}</td><td>${p.views}</td></tr>`
        ).join('');
    }

    function renderFeed(events) {
        if (!els.feed) return;
        if (!events.length) {
            els.feed.innerHTML = '<p class="card-hint">Ouvrez la vitrine dans un autre onglet pour voir le flux en direct.</p>';
            return;
        }
        els.feed.innerHTML = events.map(e => `
            <div class="live-feed-item">
                <span class="live-time">${formatTime(e.at)}</span>
                <span class="live-page">${e.page_label || e.page}</span>
                <span class="live-path muted">${e.path || ''}</span>
            </div>
        `).join('');
    }

    async function refresh() {
        try {
            const res = await fetch('/crm/api/analytics/realtime');
            if (!res.ok) return;
            const data = await res.json();
            if (els.active) els.active.textContent = data.active_users;
            if (els.views30) els.views30.textContent = data.views_last_30min;
            if (els.updated) els.updated.textContent = 'MAJ ' + formatTime(data.updated_at);
            renderChart(data.minute_chart || []);
            renderPages(data.pages_realtime || []);
            renderFeed(data.live_feed || []);
        } catch (_) {}
    }

    refresh();
    setInterval(refresh, 5000);
})();
