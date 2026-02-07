/**
 * Gestor de gráficas de KPI de productos con Chart.js
 * Componente 1: KPI de Productos
 * 
 * Separación de métricas:
 * - VENTAS: Top vendidos, Rentabilidad, ABC Pareto (análisis financiero)
 * - INVENTARIO: Rotación (gestión operativa)
 */

class KPIChartsManager {
    constructor() {
        this.charts = {};
        this.data = null;
        this.config = {
            updateInterval: 900000, // 15 minutos (mismo que cache del backend)
            apiEndpoint: '/api/kpi/productos/',
            defaultDias: 7,
            defaultLimit: 5
        };
    }

    /**
     * Inicializa el gestor de gráficas
     */
    async init() {
        console.log('[KPICharts] Inicializando gráficas de KPI...');
        
        // Verificar que Chart.js esté cargado
        if (typeof Chart === 'undefined') {
            console.error('[KPICharts] Chart.js no está cargado');
            return;
        }
        
        await this.loadData();
        this.renderCharts();
        this.startAutoUpdate();
        
        console.log('[KPICharts] Gráficas inicializadas correctamente');
    }

    /**
     * Carga datos desde la API
     */
    async loadData() {
        try {
            const url = `${this.config.apiEndpoint}?dias=${this.config.defaultDias}&limit=${this.config.defaultLimit}`;
            console.log(`[KPICharts] Cargando datos desde: ${url}`);
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.data = await response.json();
            console.log('[KPICharts] Datos cargados:', this.data);
            
        } catch (error) {
            console.error('[KPICharts] Error al cargar datos:', error);
            // Datos vacíos por defecto
            this.data = {
                ventas: {
                    top_vendidos: [],
                    rentabilidad: [],
                    abc_analysis: { productos: [], resumen: {} }
                },
                inventario: {
                    rotacion: []
                }
            };
        }
    }

    /**
     * Renderiza todas las gráficas
     */
    renderCharts() {
        this.renderTopVendidos();
        this.renderRotacion();
        this.renderRentabilidad();
        // ABC Analysis es opcional, se renderiza si existe el canvas
        if (document.getElementById('chartABCAnalysis')) {
            this.renderABCAnalysis();
            this.renderABCTable();  // Tabla detallada de productos ABC
        }
    }

    /**
     * [VENTAS] Gráfica de Top 5 Productos Más Vendidos
     */
    renderTopVendidos() {
        const ctx = document.getElementById('chartTopVendidos');
        if (!ctx) {
            console.warn('[KPICharts] Canvas chartTopVendidos no encontrado');
            return;
        }

        const data = this.data?.ventas?.top_vendidos || [];
        
        // Destruir gráfica anterior si existe
        if (this.charts.topVendidos) {
            this.charts.topVendidos.destroy();
        }
        
        this.charts.topVendidos = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(p => p.nombre),
                datasets: [{
                    label: 'Unidades Vendidas',
                    data: data.map(p => p.cantidad || p.unidades_vendidas || 0),
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',   // Verde - 1er lugar
                        'rgba(23, 162, 184, 0.8)',  // Cyan - 2do lugar
                        'rgba(0, 123, 255, 0.8)',   // Azul - 3er lugar
                        'rgba(108, 117, 125, 0.8)', // Gris - 4to lugar
                        'rgba(52, 58, 64, 0.8)'     // Gris oscuro - 5to lugar
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(23, 162, 184, 1)',
                        'rgba(0, 123, 255, 1)',
                        'rgba(108, 117, 125, 1)',
                        'rgba(52, 58, 64, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                indexAxis: 'y',  // Barras horizontales
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Top 5 Productos Más Vendidos (Última Semana)',
                        font: { size: 16, weight: 'bold' },
                        color: '#333'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const product = data[context.dataIndex];
                                const labels = [
                                    `Unidades: ${product.cantidad || product.unidades_vendidas || 0}`,
                                    `Ganancia: $${(product.ganancia || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })}`
                                ];
                                if (product.codigo) {
                                    labels.push(`Código: ${product.codigo}`);
                                }
                                if (product.porcentaje_total) {
                                    labels.push(`${product.porcentaje_total}% del total`);
                                }
                                return labels;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: 'rgba(0, 0, 0, 0.05)' }
                    },
                    y: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * [INVENTARIO] Gráfica de Rotación de Inventario
     */
    renderRotacion() {
        const ctx = document.getElementById('chartRotacion');
        if (!ctx) {
            console.warn('[KPICharts] Canvas chartRotacion no encontrado');
            return;
        }

        const data = this.data?.inventario?.rotacion || [];
        
        if (this.charts.rotacion) {
            this.charts.rotacion.destroy();
        }
        
        this.charts.rotacion = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(p => p.nombre),
                datasets: [{
                    label: 'Días de Rotación',
                    data: data.map(p => p.rotacion_dias),
                    backgroundColor: data.map(p => {
                        if (p.rotacion_dias < 30) return 'rgba(40, 167, 69, 0.8)';  // Verde - Rápida
                        if (p.rotacion_dias < 60) return 'rgba(255, 193, 7, 0.8)';  // Amarillo - Media
                        return 'rgba(220, 53, 69, 0.8)';  // Rojo - Lenta
                    }),
                    borderColor: data.map(p => {
                        if (p.rotacion_dias < 30) return 'rgba(40, 167, 69, 1)';
                        if (p.rotacion_dias < 60) return 'rgba(255, 193, 7, 1)';
                        return 'rgba(220, 53, 69, 1)';
                    }),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Rotación de Inventario (Días Promedio)',
                        font: { size: 16, weight: 'bold' },
                        color: '#333'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const product = data[context.dataIndex];
                                return [
                                    `Rotación: ${product.rotacion_dias} días`,
                                    `Clasificación: ${product.clasificacion}`,
                                    `Stock actual: ${product.stock_actual}`,
                                    `Ventas (30d): ${product.ventas_30d}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 },
                        grid: { color: 'rgba(0, 0, 0, 0.05)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * [VENTAS] Gráfica de Rentabilidad de Productos
     */
    renderRentabilidad() {
        const ctx = document.getElementById('chartRentabilidad');
        if (!ctx) {
            console.warn('[KPICharts] Canvas chartRentabilidad no encontrado');
            return;
        }

        const data = this.data?.ventas?.rentabilidad || [];
        
        if (this.charts.rentabilidad) {
            this.charts.rentabilidad.destroy();
        }
        
        this.charts.rentabilidad = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(p => p.nombre),
                datasets: [{
                    label: 'Margen (%)',
                    data: data.map(p => p.margen_porcentaje),
                    backgroundColor: 'rgba(40, 167, 69, 0.8)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    title: {
                        display: true,
                        text: 'Top 5 Productos Más Rentables (Margen %)',
                        font: { size: 16, weight: 'bold' },
                        color: '#333'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const product = data[context.dataIndex];
                                return [
                                    `Margen: ${product.margen_porcentaje}%`,
                                    `Ganancia total: $${product.ganancia_total.toLocaleString('es-ES', { minimumFractionDigits: 2 })}`,
                                    `Unidades vendidas: ${product.unidades_vendidas}`,
                                    `Precio venta: $${product.precio_venta.toLocaleString('es-ES', { minimumFractionDigits: 2 })}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: { color: 'rgba(0, 0, 0, 0.05)' }
                    },
                    x: {
                        grid: { display: false }
                    }
                }
            }
        });
    }

    /**
     * [VENTAS] Gráfica de Análisis ABC (Pareto) - OPCIONAL
     * Incluye tooltips informativos sobre cada categoría
     */
    renderABCAnalysis() {
        const ctx = document.getElementById('chartABCAnalysis');
        if (!ctx) return;

        const resumen = this.data?.ventas?.abc_analysis?.resumen || {};
        
        if (this.charts.abcAnalysis) {
            this.charts.abcAnalysis.destroy();
        }
        
        const cantidadA = resumen.clase_a?.cantidad || 0;
        const cantidadB = resumen.clase_b?.cantidad || 0;
        const cantidadC = resumen.clase_c?.cantidad || 0;
        
        // Informacion descriptiva de cada categoria ABC
        const abcInfo = {
            A: {
                titulo: 'Categoria A - ALTO VALOR',
                descripcion: 'Productos mas importantes y criticos para el negocio',
                productos: '10% - 20% del inventario',
                ingresos: '70% - 80% de los ingresos',
                gestion: [
                    'Gestion estricta y prioritaria',
                    'Control de inventario continuo',
                    'Pronosticos de demanda precisos',
                    'Puntos de reorden bajos y seguridad alta',
                    'Atencion gerencial frecuente'
                ]
            },
            B: {
                titulo: 'Categoria B - VALOR MEDIO',
                descripcion: 'Productos importantes, pero menos criticos que los A',
                productos: '20% - 30% del inventario',
                ingresos: '15% - 25% de los ingresos',
                gestion: [
                    'Gestion intermedia',
                    'Revisiones periodicas (semanal/mensual)',
                    'Pronosticos de demanda moderados'
                ]
            },
            C: {
                titulo: 'Categoria C - BAJO VALOR',
                descripcion: 'Productos numerosos pero con impacto financiero pequeno',
                productos: '60% - 70% del inventario',
                ingresos: '5% - 10% de los ingresos',
                gestion: [
                    'Gestion simplificada',
                    'Revisiones esporadicas (trimestral)',
                    'Pedidos en grandes cantidades para ahorrar costos',
                    'Puntos de reorden altos'
                ]
            }
        };
        
        this.charts.abcAnalysis = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: [
                    `Clase A (${resumen.clase_a?.porcentaje || 0}% ganancias)`,
                    `Clase B (${resumen.clase_b?.porcentaje || 0}% ganancias)`,
                    `Clase C (${resumen.clase_c?.porcentaje || 0}% ganancias)`
                ],
                datasets: [{
                    data: [cantidadA, cantidadB, cantidadC],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.8)',   // Verde para A
                        'rgba(255, 193, 7, 0.8)',   // Amarillo para B
                        'rgba(220, 53, 69, 0.8)'    // Rojo para C
                    ],
                    borderColor: [
                        'rgba(40, 167, 69, 1)',
                        'rgba(255, 193, 7, 1)',
                        'rgba(220, 53, 69, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Analisis ABC de Productos (Principio de Pareto)',
                        font: { size: 16, weight: 'bold' },
                        color: '#333'
                    },
                    tooltip: {
                        // Tooltip mas grande para mostrar info completa
                        bodyFont: { size: 12 },
                        titleFont: { size: 13, weight: 'bold' },
                        padding: 12,
                        boxPadding: 6,
                        callbacks: {
                            title: function(tooltipItems) {
                                const index = tooltipItems[0].dataIndex;
                                const categorias = ['A', 'B', 'C'];
                                const info = abcInfo[categorias[index]];
                                return info.titulo;
                            },
                            label: function(context) {
                                const index = context.dataIndex;
                                const categorias = ['A', 'B', 'C'];
                                const info = abcInfo[categorias[index]];
                                const value = context.raw;
                                const total = cantidadA + cantidadB + cantidadC;
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                
                                return [
                                    `${info.descripcion}`,
                                    ``,
                                    `Productos en tu inventario: ${value} (${percentage}%)`,
                                    `Rango tipico productos: ${info.productos}`,
                                    `Rango tipico ingresos: ${info.ingresos}`,
                                    ``
                                ];
                            },
                            afterLabel: function(context) {
                                const index = context.dataIndex;
                                const categorias = ['A', 'B', 'C'];
                                const info = abcInfo[categorias[index]];
                                
                                return [
                                    'Recomendaciones:',
                                    ...info.gestion.map(g => `  - ${g}`)
                                ];
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * [VENTAS] Tabla detallada de productos ABC (Top 10)
     * Muestra los productos con su clasificacion y ganancia
     */
    renderABCTable() {
        const container = document.getElementById('abcTableContent');
        if (!container) {
            console.warn('[KPICharts] Contenedor abcTableContent no encontrado');
            return;
        }

        const productos = this.data?.ventas?.abc_analysis?.productos || [];
        
        if (productos.length === 0) {
            container.innerHTML = '<p style="color: #888; text-align: center;">No hay datos de productos disponibles</p>';
            return;
        }

        // Tomar top 10 productos
        const top10 = productos.slice(0, 10);
        
        // Colores por clasificacion
        const colores = {
            'A': { bg: '#d4edda', text: '#155724', badge: '#28a745' },
            'B': { bg: '#fff3cd', text: '#856404', badge: '#ffc107' },
            'C': { bg: '#f8d7da', text: '#721c24', badge: '#dc3545' }
        };
        
        let tableHTML = `
            <div style="display: flex; justify-content: center; width: 100%;">
            <table style="width: 100%; max-width: 800px; border-collapse: collapse; font-size: 0.85rem; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
                <thead>
                    <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                        <th style="padding: 12px 10px; text-align: left; font-weight: 600;">Producto</th>
                        <th style="padding: 12px 10px; text-align: left; font-weight: 600;">Código</th>
                        <th style="padding: 12px 10px; text-align: right; font-weight: 600;">Ganancia</th>
                        <th style="padding: 12px 10px; text-align: center; font-weight: 600;">% Acum.</th>
                        <th style="padding: 12px 10px; text-align: center; font-weight: 600;">Clase</th>
                    </tr>
                </thead>
                <tbody>`
        
        top10.forEach((producto, index) => {
            const color = colores[producto.clasificacion] || colores['C'];
            const ganancia = producto.ganancia_total || 0;
            const pctAcum = producto.porcentaje_acumulado || 0;
            
            tableHTML += `
                <tr style="border-bottom: 1px solid #e9ecef; background: ${index % 2 === 0 ? '#fff' : '#fafbfc'};">
                    <td style="padding: 10px; font-weight: 500;">${producto.nombre || '-'}</td>
                    <td style="padding: 10px; color: #666;">${producto.codigo || '-'}</td>
                    <td style="padding: 10px; text-align: right; font-weight: 600; color: #28a745;">$${ganancia.toLocaleString('es-CO', {minimumFractionDigits: 0})}</td>
                    <td style="padding: 10px; text-align: center; color: #666;">${pctAcum.toFixed(1)}%</td>
                    <td style="padding: 10px; text-align: center;">
                        <span style="display: inline-block; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; background: ${color.badge}; color: white;">
                            Clase ${producto.clasificacion}
                        </span>
                    </td>
                </tr>
            `;
        });
        
        tableHTML += '</tbody></table></div>';
        
        // Agregar leyenda de clasificacion
        tableHTML += `
            <div style="margin-top: 1rem; display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; font-size: 0.8rem;">
                <span><strong style="color: #28a745;">A</strong> = Alto valor (80% ganancias)</span>
                <span><strong style="color: #ffc107;">B</strong> = Valor medio (15% ganancias)</span>
                <span><strong style="color: #dc3545;">C</strong> = Bajo valor (5% ganancias)</span>
            </div>
        `;
        
        container.innerHTML = tableHTML;
    }

    /**
     * Actualiza las graficas automaticamente
     */
    startAutoUpdate() {
        setInterval(async () => {
            console.log('[KPICharts] Actualizando datos automáticamente...');
            await this.loadData();
            this.updateCharts();
        }, this.config.updateInterval);
    }

    /**
     * Actualiza todas las gráficas con nuevos datos
     */
    updateCharts() {
        // Destruir gráficas existentes
        Object.keys(this.charts).forEach(key => {
            if (this.charts[key]) {
                this.charts[key].destroy();
            }
        });
        
        // Renderizar de nuevo
        this.renderCharts();
    }

    /**
     * Exporta datos a Excel (requiere biblioteca externa)
     */
    exportToExcel() {
        if (typeof XLSX === 'undefined') {
            console.warn('[KPICharts] Biblioteca XLSX no está cargada');
            alert('Función de exportación no disponible');
            return;
        }
        
        const worksheet = XLSX.utils.json_to_sheet(this.data.ventas.top_vendidos);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Top Productos");
        XLSX.writeFile(workbook, `kpi_productos_${new Date().toISOString().split('T')[0]}.xlsx`);
    }
}

// Auto-inicializar en dashboard
document.addEventListener('DOMContentLoaded', () => {
    const isDashboard = window.location.pathname === '/' || window.location.pathname.includes('/dashboard');
    
    if (isDashboard) {
        console.log('[KPICharts] Dashboard detectado, inicializando...');
        const kpiManager = new KPIChartsManager();
        kpiManager.init();
        
        // Exponer globalmente para debugging y botones
        window.kpiChartsManager = kpiManager;
        
        // Botón de actualización manual
        const refreshBtn = document.getElementById('refreshKPI');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', async () => {
                console.log('[KPICharts] Actualización manual solicitada');
                await kpiManager.loadData();
                kpiManager.updateCharts();
            });
        }
        
        // Botón de exportación
        const exportBtn = document.getElementById('exportKPI');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                kpiManager.exportToExcel();
            });
        }
    }
});
