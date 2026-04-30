/**
 * Sidebar Mobile Toggle - Premium UX
 * Maneja el despliegue del sidebar en dispositivos móviles
 * @version 2.0
 */

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const navbarBrand = document.querySelector('.navbar-brand');
    const closeBtn = document.getElementById('sidebarCloseBtn');
    const sidebarToggleBtn = document.getElementById('sidebarToggle');

    function openSidebar() {
        if (sidebar) {
            sidebar.classList.add('active');
            if (sidebarOverlay) {
                sidebarOverlay.classList.add('active');
            }
            document.body.style.overflow = 'hidden';
        }
    }

    function closeSidebar() {
        if (sidebar) {
            sidebar.classList.remove('active');
            if (sidebarOverlay) {
                sidebarOverlay.classList.remove('active');
            }
            document.body.style.overflow = '';
        }
    }

    // Toggle sidebar con botón hamburguesa (nuevo)
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (sidebar.classList.contains('active')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    // Toggle sidebar al tocar "HUB DE GESTIÓN" (compatibilidad)
    if (navbarBrand) {
        navbarBrand.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                if (sidebar.classList.contains('active')) {
                    closeSidebar();
                } else {
                    openSidebar();
                }
            }
        });
    }

    // Cerrar sidebar con botón X
    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            closeSidebar();
        });
    }

    // Cerrar sidebar al tocar overlay
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            closeSidebar();
        });
    }

    // Cerrar sidebar al seleccionar un enlace (navegación)
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                // Pequeño delay para feedback visual antes de navegar
                setTimeout(closeSidebar, 150);
            }
        });
    });

    // Cerrar sidebar con tecla Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });

    // Cerrar sidebar si se redimensiona la ventana a desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && sidebar && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });
});
