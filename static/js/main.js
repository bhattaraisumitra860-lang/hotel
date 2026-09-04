function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    if (menu) menu.classList.toggle('hidden');
}

document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        document.querySelectorAll('[id^="modal-"], #lightbox').forEach(function (element) {
            element.classList.add('hidden');
        });
        document.body.style.overflow = '';
    }
});
