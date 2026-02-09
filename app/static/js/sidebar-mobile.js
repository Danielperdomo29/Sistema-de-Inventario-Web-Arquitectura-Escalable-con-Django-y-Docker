/**
 * Sidebar Mobile Toggle
 * Maneja el despliegue del sidebar en dispositivos móviles
 * @version 1.0
 */

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const navbarBrand = document.querySelector('.navbar-brand');
    
    // Función para abrir sidebar
    function openSidebar() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.add('active');
            sidebarOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    // Función para cerrar sidebar
    function closeSidebar() {
        if (sidebar && sidebarOverlay) {
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    // Toggle sidebar al tocar "HUB DE GESTIÓN" (solo en móviles)
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
        
        // Cambiar cursor en móviles
        navbarBrand.style.cursor = 'pointer';
    }
    
    // Cerrar sidebar al tocar overlay
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            closeSidebar();
        });
    }
    
    // Cerrar sidebar al seleccionar un enlace
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                closeSidebar();
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
