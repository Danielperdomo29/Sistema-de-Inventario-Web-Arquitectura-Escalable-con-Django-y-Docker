/**
 * Sidebar Sections Manager
 * Maneja el colapso independiente de secciones del sidebar
 * @version 1.0
 */

class SidebarSectionsManager {
    constructor() {
        this.STORAGE_KEY_PREFIX = 'sidebar_section_';
        this.init();
    }

    init() {
        // Esperar a que el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.attachSectionToggles();
                this.restoreSectionStates();
            });
        } else {
            this.attachSectionToggles();
            this.restoreSectionStates();
        }
    }

    attachSectionToggles() {
        const sectionHeaders = document.querySelectorAll('.sidebar-section-header');
        
        sectionHeaders.forEach(header => {
            header.addEventListener('click', (e) => {
                // Prevenir que el click en el botón dispare dos veces
                if (e.target.closest('.section-toggle')) {
                    return;
                }
                
                const section = header.closest('.sidebar-section');
                const sectionName = header.querySelector('.section-toggle').dataset.section;
                this.toggleSection(section, sectionName);
            });
        });

        // También manejar clicks directos en el botón
        const toggleButtons = document.querySelectorAll('.section-toggle');
        toggleButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevenir propagación al header
                const section = button.closest('.sidebar-section');
                const sectionName = button.dataset.section;
                this.toggleSection(section, sectionName);
            });
        });
    }

    toggleSection(sectionElement, sectionName) {
        const isCollapsed = sectionElement.classList.contains('collapsed');
        
        if (isCollapsed) {
            this.expandSection(sectionElement, sectionName);
        } else {
            this.collapseSection(sectionElement, sectionName);
        }
    }

    collapseSection(sectionElement, sectionName) {
        sectionElement.classList.add('collapsed');
        this.saveSectionState(sectionName, true);
        
        // Emitir evento
        window.dispatchEvent(new CustomEvent('sectionCollapsed', {
            detail: { section: sectionName }
        }));
        
        console.log(`✅ Sección "${sectionName}" colapsada`);
    }

    expandSection(sectionElement, sectionName) {
        sectionElement.classList.remove('collapsed');
        this.saveSectionState(sectionName, false);
        
        // Emitir evento
        window.dispatchEvent(new CustomEvent('sectionExpanded', {
            detail: { section: sectionName }
        }));
        
        console.log(`✅ Sección "${sectionName}" expandida`);
    }

    saveSectionState(sectionName, isCollapsed) {
        try {
            localStorage.setItem(
                `${this.STORAGE_KEY_PREFIX}${sectionName}`,
                isCollapsed.toString()
            );
        } catch (error) {
            console.warn('⚠️ No se pudo guardar el estado de la sección:', error);
        }
    }

    restoreSectionStates() {
        const sections = document.querySelectorAll('.sidebar-section');
        
        sections.forEach(section => {
            const toggleBtn = section.querySelector('.section-toggle');
            if (!toggleBtn) return;
            
            const sectionName = toggleBtn.dataset.section;
            const savedState = localStorage.getItem(`${this.STORAGE_KEY_PREFIX}${sectionName}`);
            
            if (savedState === 'true') {
                section.classList.add('collapsed');
            }
        });
        
        console.log('✅ Estados de secciones restaurados');
    }
}

// Inicializar el gestor de secciones
const sidebarSectionsManager = new SidebarSectionsManager();

// Exportar para uso global
window.sidebarSectionsManager = sidebarSectionsManager;

// Eventos disponibles para escuchar:
// - sectionCollapsed: Cuando una sección se colapsa
// - sectionExpanded: Cuando una sección se expande

// Ejemplo de uso:
// window.addEventListener('sectionCollapsed', (e) => {
//     console.log('Sección colapsada:', e.detail.section);
// });
