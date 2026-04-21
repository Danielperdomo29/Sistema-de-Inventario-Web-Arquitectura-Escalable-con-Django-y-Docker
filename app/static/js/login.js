/**
 * Controlador del carrusel de fondos en la página de login.
 * Se ejecuta solo si existen slides y controles.
 */
document.addEventListener('DOMContentLoaded', function() {
    const slides = document.querySelectorAll('.carousel-slide');
    const dots = document.querySelectorAll('.carousel-dot');
    if (!slides.length || slides.length <= 1) return;

    let currentIndex = 0;
    let interval;

    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.classList.toggle('active', i === index);
        });
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
        });
        currentIndex = index;
    }

    function nextSlide() {
        const next = (currentIndex + 1) % slides.length;
        showSlide(next);
    }

    dots.forEach((dot, idx) => {
        dot.addEventListener('click', () => {
            showSlide(idx);
            resetInterval();
        });
    });

    function resetInterval() {
        clearInterval(interval);
        interval = setInterval(nextSlide, 5000);
    }

    interval = setInterval(nextSlide, 5000);

    const carousel = document.querySelector('.background-carousel');
    if (carousel) {
        carousel.addEventListener('mouseenter', () => clearInterval(interval));
        carousel.addEventListener('mouseleave', resetInterval);
    }
});
