/**
 * Sistema de Gestión de Sidebar - Avanzado
 * Implementa toggle de sidebar con persistencia, animaciones y buenas prácticas
 * @version 2.0
 */

class SidebarManager {
    constructor() {
        // Elementos del DOM
        this.sidebar = null;
        this.mainContent = null;
        this.toggleBtn = null;
        this.overlay = null;
        this.hamburgerMenu = null;
        
        // Estado
        this.isCollapsed = false;
        this.isMobile = false;
        
        // Configuración
        this.STORAGE_KEY = 'sidebar_collapsed_state';
        this.MOBILE_BREAKPOINT = 768;
        this.ANIMATION_DURATION = 300;
        
        // Inicializar cuando el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    /**
     * Inicializa el gestor de sidebar
     */
    init() {
        this.cacheElements();
        this.checkMobileView();
        this.restoreState();
        this.attachEventListeners();
        this.setupResizeObserver();
    }
    
    /**
     * Cachea referencias a elementos del DOM
     */
    cacheElements() {
        this.sidebar = document.getElementById('sidebar');
        this.mainContent = document.querySelector('.main-content');
        this.toggleBtn = document.getElementById('sidebar-toggle');
        this.overlay = document.getElementById('sidebar-overlay');
        this.hamburgerMenu = document.getElementById('hamburger-menu');
        
        // Validar elementos críticos
        if (!this.sidebar) {
            console.error('❌ Sidebar element not found');
            return;
        }
    }
    
    /**
     * Verifica si estamos en vista móvil
     */
    checkMobileView() {
        this.isMobile = window.innerWidth < this.MOBILE_BREAKPOINT;
    }
    
    /**
     * Restaura el estado del sidebar desde localStorage
     */
    restoreState() {
        if (this.isMobile) return; // No aplicar estado guardado en móvil
        
        try {
            const savedState = localStorage.getItem(this.STORAGE_KEY);
            if (savedState === 'true') {
                this.collapse(false); // Sin animación en carga inicial
            }
        } catch (error) {
            console.warn('⚠️ Could not restore sidebar state:', error);
        }
    }
    
    /**
     * Guarda el estado del sidebar en localStorage
     */
    saveState() {
        if (this.isMobile) return; // No guardar estado en móvil
        
        try {
            localStorage.setItem(this.STORAGE_KEY, this.isCollapsed.toString());
        } catch (error) {
            console.warn('⚠️ Could not save sidebar state:', error);
        }
    }
    
    /**
     * Adjunta event listeners
     */
    attachEventListeners() {
        // Toggle button (desktop)
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggle();
            });
        }
        
        // Hamburger menu (mobile)
        if (this.hamburgerMenu) {
            this.hamburgerMenu.addEventListener('click', (e) => {
                e.preventDefault();
                this.openMobile();
            });
        }
        
        // Overlay click (mobile)
        if (this.overlay) {
            this.overlay.addEventListener('click', () => {
                this.closeMobile();
            });
        }
        
        // Cerrar sidebar en móvil al hacer click en un enlace
        if (this.sidebar) {
            const links = this.sidebar.querySelectorAll('a');
            links.forEach(link => {
                link.addEventListener('click', () => {
                    if (this.isMobile) {
                        this.closeMobile();
                    }
                });
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + B para toggle
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                if (!this.isMobile) {
                    this.toggle();
                }
            }
            
            // Escape para cerrar en móvil
            if (e.key === 'Escape' && this.isMobile) {
                this.closeMobile();
            }
        });
    }
    
    /**
     * Configura observer para cambios de tamaño de ventana
     */
    setupResizeObserver() {
        let resizeTimeout;
        
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                const wasMobile = this.isMobile;
                this.checkMobileView();
                
                // Si cambiamos de desktop a mobile o viceversa
                if (wasMobile !== this.isMobile) {
                    this.handleViewportChange(wasMobile);
                }
            }, 150); // Debounce de 150ms
        });
    }
    
    /**
     * Maneja cambios entre vista móvil y desktop
     */
    handleViewportChange(wasMobile) {
        if (this.isMobile) {
            // Cambiamos a móvil
            this.closeMobile();
            if (this.sidebar) {
                this.sidebar.classList.remove('collapsed');
            }
            if (this.mainContent) {
                this.mainContent.classList.remove('sidebar-collapsed');
            }
        } else {
            // Cambiamos a desktop
            this.restoreState();
        }
    }
    
    /**
     * Alterna el estado del sidebar (desktop)
     */
    toggle() {
        if (this.isMobile) return;
        
        if (this.isCollapsed) {
            this.expand();
        } else {
            this.collapse();
        }
    }
    
    /**
     * Colapsa el sidebar (desktop)
     */
    collapse(animate = true) {
        if (this.isMobile || !this.sidebar) return;
        
        this.isCollapsed = true;
        
        if (animate) {
            this.sidebar.style.transition = `all ${this.ANIMATION_DURATION}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            if (this.mainContent) {
                this.mainContent.style.transition = `margin-left ${this.ANIMATION_DURATION}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            }
        }
        
        this.sidebar.classList.add('collapsed');
        if (this.mainContent) {
            this.mainContent.classList.add('sidebar-collapsed');
        }
        
        this.saveState();
        this.updateTooltips();
        
        // Emitir evento personalizado
        this.dispatchEvent('sidebarCollapsed');
    }
    
    /**
     * Expande el sidebar (desktop)
     */
    expand(animate = true) {
        if (this.isMobile || !this.sidebar) return;
        
        this.isCollapsed = false;
        
        if (animate) {
            this.sidebar.style.transition = `all ${this.ANIMATION_DURATION}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            if (this.mainContent) {
                this.mainContent.style.transition = `margin-left ${this.ANIMATION_DURATION}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            }
        }
        
        this.sidebar.classList.remove('collapsed');
        if (this.mainContent) {
            this.mainContent.classList.remove('sidebar-collapsed');
        }
        
        this.saveState();
        
        // Emitir evento personalizado
        this.dispatchEvent('sidebarExpanded');
    }
    
    /**
     * Abre el sidebar en móvil
     */
    openMobile() {
        if (!this.isMobile || !this.sidebar) return;
        
        this.sidebar.classList.add('active');
        if (this.overlay) {
            this.overlay.classList.add('active');
        }
        document.body.style.overflow = 'hidden';
        
        this.dispatchEvent('sidebarOpenedMobile');
    }
    
    /**
     * Cierra el sidebar en móvil
     */
    closeMobile() {
        if (!this.sidebar) return;
        
        this.sidebar.classList.remove('active');
        if (this.overlay) {
            this.overlay.classList.remove('active');
        }
        document.body.style.overflow = '';
        
        this.dispatchEvent('sidebarClosedMobile');
    }
    
    /**
     * Actualiza tooltips para links del sidebar
     */
    updateTooltips() {
        if (!this.sidebar) return;
        
        const links = this.sidebar.querySelectorAll('.sidebar-menu a');
        links.forEach(link => {
            const text = link.textContent.trim();
            link.setAttribute('data-tooltip', text);
        });
    }
    
    /**
     * Emite un evento personalizado
     */
    dispatchEvent(eventName) {
        const event = new CustomEvent(eventName, {
            detail: {
                isCollapsed: this.isCollapsed,
                isMobile: this.isMobile
            }
        });
        window.dispatchEvent(event);
    }
    
    /**
     * Obtiene el estado actual
     */
    getState() {
        return {
            isCollapsed: this.isCollapsed,
            isMobile: this.isMobile
        };
    }
}

// Inicializar el gestor de sidebar
const sidebarManager = new SidebarManager();

// Exportar para uso global
window.sidebarManager = sidebarManager;

// Eventos disponibles para escuchar:
// - sidebarCollapsed: Cuando el sidebar se colapsa (desktop)
// - sidebarExpanded: Cuando el sidebar se expande (desktop)
// - sidebarOpenedMobile: Cuando el sidebar se abre (móvil)
// - sidebarClosedMobile: Cuando el sidebar se cierra (móvil)

// Ejemplo de uso:
// window.addEventListener('sidebarCollapsed', (e) => {
//     console.log('Sidebar collapsed', e.detail);
// });
