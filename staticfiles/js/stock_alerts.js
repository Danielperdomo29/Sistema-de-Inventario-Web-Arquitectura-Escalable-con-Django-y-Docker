/**
 * Sistema de alertas de stock en tiempo real
 * Hace polling cada 30 segundos para verificar alertas pendientes
 * Muestra notificaciones con SweetAlert2
 * 
 * Autor: Sistema de Inventario
 * Fecha: 2026-01-12
 */

class StockAlertManager {
    constructor() {
        this.pollingInterval = 30000; // 30 segundos
        this.lastAlertIds = new Set();
        this.isPolling = false;
        this.intervalId = null;
    }

    /**
     * Inicializa el sistema de alertas
     */
    init() {
        console.log('[StockAlertManager] Inicializando sistema de alertas...');
        
        // Verificar inmediatamente al cargar
        this.checkAlerts();
        
        // Iniciar polling
        this.startPolling();
    }

    /**
     * Inicia el polling periódico de alertas
     */
    startPolling() {
        if (this.isPolling) {
            console.log('[StockAlertManager] Polling ya está activo');
            return;
        }
        
        this.isPolling = true;
        this.intervalId = setInterval(() => {
            this.checkAlerts();
        }, this.pollingInterval);
        
        console.log(`[StockAlertManager] Polling iniciado (cada ${this.pollingInterval/1000}s)`);
    }

    /**
     * Detiene el polling
     */
    stopPolling() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            this.isPolling = false;
            console.log('[StockAlertManager] Polling detenido');
        }
    }

    /**
     * Verifica si hay alertas pendientes
     */
    async checkAlerts() {
        try {
            const response = await fetch('/api/stock/alertas-pendientes/');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.alertas && data.alertas.length > 0) {
                console.log(`[StockAlertManager] ${data.count} alertas pendientes encontradas`);
                
                // Mostrar solo alertas nuevas (que no hemos mostrado antes)
                const newAlerts = data.alertas.filter(
                    alerta => !this.lastAlertIds.has(alerta.id)
                );
                
                if (newAlerts.length > 0) {
                    console.log(`[StockAlertManager] ${newAlerts.length} alertas nuevas para mostrar`);
                    this.showAlerts(newAlerts);
                    
                    // Guardar IDs de alertas mostradas
                    newAlerts.forEach(alerta => {
                        this.lastAlertIds.add(alerta.id);
                    });
                }
            } else {
                console.log('[StockAlertManager] No hay alertas pendientes');
            }
        } catch (error) {
            console.error('[StockAlertManager] Error al verificar alertas:', error);
        }
    }

    /**
     * Muestra las alertas usando SweetAlert2 con iconos de Bootstrap 5
     * @param {Array} alertas - Lista de alertas a mostrar
     */
    showAlerts(alertas) {
        // Mostrar la alerta más crítica primero
        const alertaCritica = alertas.find(a => a.nivel === 'ROJO') || alertas[0];
        
        const icon = alertaCritica.nivel === 'ROJO' ? 'error' : 'warning';
        const iconColor = alertaCritica.nivel === 'ROJO' ? '#dc3545' : '#ffc107';
        
        // Iconos de Bootstrap 5 (ahora permitidos por CSP)
        const bootstrapIcon = alertaCritica.nivel === 'ROJO' 
            ? '<i class="bi bi-exclamation-triangle-fill text-danger" style="font-size: 3rem;"></i>'
            : '<i class="bi bi-exclamation-circle-fill text-warning" style="font-size: 3rem;"></i>';
        
        const title = alertaCritica.nivel === 'ROJO' ? 'Stock Crítico' : 'Stock Bajo';
        
        Swal.fire({
            icon: icon,
            title: title,
            html: `
                <div class="alert-content" style="text-align: left; padding: 1rem;">
                    <div class="d-flex align-items-center mb-3" style="display: flex; align-items: center; margin-bottom: 1rem;">
                        ${bootstrapIcon}
                        <div style="margin-left: 1rem;">
                            <h5 style="margin-bottom: 0.5rem;"><strong>${alertaCritica.producto_nombre}</strong></h5>
                            <span class="badge" style="background: ${iconColor}; color: white; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.85rem;">
                                ${alertaCritica.tipo}
                            </span>
                        </div>
                    </div>
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div>
                                <small style="color: #6c757d;">Stock actual</small>
                                <div style="font-size: 1.25rem; font-weight: bold; color: ${iconColor};">
                                    <i class="bi bi-box-seam"></i> ${alertaCritica.stock_actual}
                                </div>
                            </div>
                            <div>
                                <small style="color: #6c757d;">Stock mínimo</small>
                                <div style="font-size: 1.25rem; font-weight: bold; color: #6c757d;">
                                    <i class="bi bi-graph-down"></i> ${alertaCritica.stock_minimo}
                                </div>
                            </div>
                        </div>
                    </div>
                    ${alertas.length > 1 ? `
                        <div style="background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; padding: 0.75rem; border-radius: 0.25rem;">
                            <i class="bi bi-info-circle"></i> 
                            Tienes ${alertas.length - 1} alerta(s) más pendiente(s)
                        </div>
                    ` : ''}
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: '<i class="bi bi-plus-circle"></i> Aumentar Stock',
            cancelButtonText: '<i class="bi bi-x-circle"></i> Cerrar',
            confirmButtonColor: '#28a745',
            cancelButtonColor: '#6c757d',
            customClass: {
                popup: 'stock-alert-popup',
                confirmButton: 'btn btn-success',
                cancelButton: 'btn btn-secondary'
            },
            width: '550px',
            backdrop: `
                rgba(0,0,0,0.4)
                left top
                no-repeat
            `
        }).then((result) => {
            console.log('[StockAlertManager] SweetAlert result:', result);
            console.log('[StockAlertManager] isConfirmed:', result.isConfirmed);
            console.log('[StockAlertManager] isDismissed:', result.isDismissed);
            console.log('[StockAlertManager] URL editar:', alertaCritica.url_editar);
            
            if (result.isConfirmed) {
                // Redirigir a edición de producto
                console.log(`[StockAlertManager] ✅ Redirigiendo a ${alertaCritica.url_editar}`);
                window.location.href = alertaCritica.url_editar;
            } else if (result.isDismissed) {
                console.log('[StockAlertManager] ❌ Alerta cerrada sin confirmar');
                // Marcar como revisada
                this.markAsReviewed(alertaCritica.id);
            }
        });
    }

    /**
     * Marca una alerta como revisada
     * @param {number} alertaId - ID de la alerta
     */
    async markAsReviewed(alertaId) {
        try {
            const csrfToken = this.getCSRFToken();
            
            const response = await fetch(`/api/stock/alertas/${alertaId}/revisar/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                console.log(`[StockAlertManager] Alerta ${alertaId} marcada como revisada`);
            } else {
                console.error(`[StockAlertManager] Error al marcar alerta ${alertaId} como revisada`);
            }
        } catch (error) {
            console.error('[StockAlertManager] Error al marcar alerta como revisada:', error);
        }
    }

    /**
     * Obtiene el token CSRF de Django
     * @returns {string} Token CSRF
     */
    getCSRFToken() {
        // Intentar obtener del meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Intentar obtener del input hidden
        const inputTag = document.querySelector('[name=csrfmiddlewaretoken]');
        if (inputTag) {
            return inputTag.value;
        }
        
        // Intentar obtener de las cookies
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        
        if (cookieValue) {
            return cookieValue.split('=')[1];
        }
        
        console.warn('[StockAlertManager] No se pudo obtener el token CSRF');
        return '';
    }

    /**
     * Limpia el historial de alertas mostradas
     */
    clearHistory() {
        this.lastAlertIds.clear();
        console.log('[StockAlertManager] Historial de alertas limpiado');
    }
}

// Inicializar al cargar el DOM
document.addEventListener('DOMContentLoaded', () => {
    // Solo inicializar en páginas relevantes
    // PRIORIDAD: Mostrar principalmente en ventas (donde se generan las alertas)
    // También en: dashboard, productos, compras
    const relevantPages = ['/venta', '/', '/dashboard', '/producto', '/compra'];
    const currentPath = window.location.pathname;
    
    // Verificar si la ruta actual contiene alguna de las páginas relevantes
    const isRelevantPage = relevantPages.some(page => {
        if (page === '/') {
            return currentPath === '/' || currentPath === '/dashboard/';
        }
        return currentPath.includes(page);
    });
    
    if (isRelevantPage) {
        console.log('[StockAlertManager] Página relevante detectada, inicializando...');
        const alertManager = new StockAlertManager();
        alertManager.init();
        
        // Guardar en window para debugging y control manual
        window.stockAlertManager = alertManager;
        
        console.log('[StockAlertManager] Sistema de alertas activo. Usa window.stockAlertManager para control manual.');
    } else {
        console.log('[StockAlertManager] Página no relevante, no se inicializa el sistema de alertas');
        console.log('[StockAlertManager] Ruta actual:', currentPath);
    }
});

// Limpiar polling al salir de la página
window.addEventListener('beforeunload', () => {
    if (window.stockAlertManager) {
        window.stockAlertManager.stopPolling();
    }
});
