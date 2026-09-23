function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    if (menu) menu.classList.toggle('hidden');
}

// Start loading internal pages before the visitor clicks them. This keeps
// normal navigation intact while making the next page feel much faster.
(function prefetchInternalPages() {
    const prefetched = new Set();
    document.querySelectorAll('a[href]').forEach(function (link) {
        const url = new URL(link.href, window.location.href);
        if (url.origin !== window.location.origin || url.pathname === window.location.pathname ||
            url.pathname.startsWith('/admin') || url.pathname.startsWith('/api/') ||
            url.protocol !== 'http:' && url.protocol !== 'https:') return;
        function prefetch() {
            if (prefetched.has(url.href)) return;
            prefetched.add(url.href);
            const hint = document.createElement('link');
            hint.rel = 'prefetch';
            hint.href = url.href;
            document.head.appendChild(hint);
        }
        link.addEventListener('pointerenter', prefetch, { once: true });
        link.addEventListener('focus', prefetch, { once: true });
        link.addEventListener('touchstart', prefetch, { once: true, passive: true });
    });
})();

document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        document.querySelectorAll('[id^="modal-"], #lightbox').forEach(function (element) {
            element.classList.add('hidden');
        });
        document.body.style.overflow = '';
    }
});
