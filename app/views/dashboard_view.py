from django.http import HttpResponse

from app.views.layout import Layout


class DashboardView:
    """Vista del Dashboard"""

    @staticmethod
    def index(user, request_path, stats, productos_bajo_stock, ultimas_ventas, ultimas_compras, kpis=None):
        """Vista principal del dashboard mejorada"""

        # Tarjetas de estadísticas principales
        main_stats = f"""
        <div class="stats-primary-grid">
            <div class="stat-card-primary bg-gradient-purple">
                <div class="stat-card-content">
                    <div class="stat-card-info">
                        <p>Productos</p>
                        <h2>{stats['total_productos']}</h2>
                    </div>
                    <div class="stat-card-icon"><i class="fas fa-box"></i></div>
                </div>
            </div>
            
            <div class="stat-card-primary bg-gradient-pink">
                <div class="stat-card-content">
                    <div class="stat-card-info">
                        <p>Ventas del Mes</p>
                        <h2>${stats['ventas_mes']:,.2f}</h2>
                    </div>
                    <div class="stat-card-icon"><i class="fas fa-dollar-sign"></i></div>
                </div>
            </div>
            
            <div class="stat-card-primary bg-gradient-cyan">
                <div class="stat-card-content">
                    <div class="stat-card-info">
                        <p>Compras del Mes</p>
                        <h2>${stats['compras_mes']:,.2f}</h2>
                    </div>
                    <div class="stat-card-icon"><i class="fas fa-shopping-cart"></i></div>
                </div>
            </div>
            
            <div class="stat-card-primary bg-gradient-green">
                <div class="stat-card-content">
                    <div class="stat-card-info">
                        <p>Clientes</p>
                        <h2>{stats['total_clientes']}</h2>
                    </div>
                    <div class="stat-card-icon"><i class="fas fa-users"></i></div>
                </div>
            </div>
        </div>
        """

        # Tarjetas de estadísticas secundarias
        secondary_stats = f"""
        <div class="stats-secondary-grid">
            <div class="stat-card-secondary border-purple">
                <p>Categorías</p>
                <h3>{stats['total_categorias']}</h3>
            </div>
            
            <div class="stat-card-secondary border-pink">
                <p>Proveedores</p>
                <h3>{stats['total_proveedores']}</h3>
            </div>
            
            <div class="stat-card-secondary border-blue">
                <p>Almacenes</p>
                <h3>{stats['total_almacenes']}</h3>
            </div>
            
            <div class="stat-card-secondary border-green">
                <p>Total Ventas</p>
                <h3>{stats['total_ventas']}</h3>
            </div>
            
            <div class="stat-card-secondary border-orange">
                <p>Total Compras</p>
                <h3>{stats['total_compras']}</h3>
            </div>
            
            <div class="stat-card-secondary border-cyan">
                <p>Movimientos Inventario</p>
                <h3>{stats['total_movimientos']}</h3>
            </div>
        </div>
        """

        # Productos con stock bajo
        stock_rows = ""
        if productos_bajo_stock:
            for producto in productos_bajo_stock:
                badge_class = "stock-danger" if producto["stock_actual"] < 5 else "stock-warning"
                stock_rows += f"""
                <tr>
                    <td>{producto['nombre']}</td>
                    <td>{producto.get('categoria', 'N/A')}</td>
                    <td>
                        <span class="stock-badge {badge_class}">
                            {producto['stock_actual']} unidades
                        </span>
                    </td>
                    <td>
                        <a href="/productos/{producto['id']}/editar/" class="btn btn-info btn-sm">
                            Ver Producto
                        </a>
                    </td>
                </tr>
                """
        else:
            stock_rows = '<tr><td colspan="4" class="empty-message"><i class="fas fa-check-circle"></i> Todos los productos tienen stock suficiente</td></tr>'

        productos_stock_section = f"""
        <div class="card mb-30">
            <div class="card-header">
                <span><i class="fas fa-exclamation-triangle"></i> Productos con Stock Bajo</span>
                <a href="/productos/" class="btn btn-secondary">Ver Todos</a>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th>Categoría</th>
                            <th>Stock Actual</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {stock_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

        # Últimas ventas
        ventas_rows = ""
        if ultimas_ventas:
            for venta in ultimas_ventas:
                estado_badge = {
                    "pendiente": '<span class="badge badge-warning">Pendiente</span>',
                    "completada": '<span class="badge badge-success">Completada</span>',
                    "cancelada": '<span class="badge badge-danger">Cancelada</span>',
                }.get(venta.get("estado", "pendiente"), venta.get("estado", "pendiente"))

                ventas_rows += f"""
                <tr>
                    <td>#{venta['id']}</td>
                    <td>{venta.get('cliente_nombre', 'N/A')}</td>
                    <td>${venta['total']:,.2f}</td>
                    <td>{estado_badge}</td>
                    <td>{venta['fecha']}</td>
                    <td>
                        <a href="/ventas/{venta['id']}/ver/" class="btn btn-info btn-sm">
                            Ver
                        </a>
                    </td>
                </tr>
                """
        else:
            ventas_rows = '<tr><td colspan="6" class="empty-message"><i class="fas fa-chart-line"></i> No hay ventas registradas</td></tr>'

        ultimas_ventas_section = f"""
        <div class="card mb-30">
            <div class="card-header">
                <span><i class="fas fa-credit-card"></i> Últimas Ventas</span>
                <a href="/ventas/" class="btn btn-primary">Ver Todas</a>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Cliente</th>
                            <th>Total</th>
                            <th>Estado</th>
                            <th>Fecha</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ventas_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

        # Últimas compras
        compras_rows = ""
        if ultimas_compras:
            for compra in ultimas_compras:
                estado_badge = {
                    "pendiente": '<span class="badge badge-warning">Pendiente</span>',
                    "recibida": '<span class="badge badge-success">Recibida</span>',
                    "cancelada": '<span class="badge badge-danger">Cancelada</span>',
                }.get(compra.get("estado", "pendiente"), compra.get("estado", "pendiente"))

                compras_rows += f"""
                <tr>
                    <td>#{compra['id']}</td>
                    <td>{compra.get('proveedor_nombre', 'N/A')}</td>
                    <td>${compra['total']:,.2f}</td>
                    <td>{estado_badge}</td>
                    <td>{compra['fecha']}</td>
                    <td>
                        <a href="/compras/{compra['id']}/ver/" class="btn btn-info btn-sm">
                            Ver
                        </a>
                    </td>
                </tr>
                """
        else:
            compras_rows = '<tr><td colspan="6" class="empty-message"><i class="fas fa-shopping-cart"></i> No hay compras registradas</td></tr>'

        ultimas_compras_section = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-shopping-bag"></i> Últimas Compras</span>
                <a href="/compras/" class="btn btn-primary">Ver Todas</a>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Proveedor</th>
                            <th>Total</th>
                            <th>Estado</th>
                            <th>Fecha</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {compras_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

        # Bienvenida personalizada
        welcome_card = f"""
        <div class="welcome-banner">
            <h1>Bienvenido, {user.nombre_completo}</h1>
            <p>Rol: {user.rol} | Dashboard del Sistema de Inventario</p>
        </div>
        """

        # KPIs Profesionales con Gráficas (Fase 5)
        kpi_section = ""
        if kpis:
            # Chart.js CDN
            chartjs_cdn = '\u003cscript src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"\u003e\u003c/script\u003e'
            
            # KPI Cards
            kpi_cards = f"""
            \u003c!-- KPIs Profesionales para Contadores --\u003e
            \u003cdiv class="kpi-section"\u003e
                \u003ch2 class="section-title"\u003e\u003ci class="fas fa-chart-bar"\u003e\u003c/i\u003e KPIs Profesionales\u003c/h2\u003e
                
                \u003cdiv class="kpi-cards-grid"\u003e
                    \u003c!-- Margen Bruto --\u003e
                    \u003cdiv class="kpi-card {"kpi-positive" if kpis['margen_bruto']['tendencia'] == 'up' else 'kpi-negative'}"\u003e
                        \u003cdiv class="kpi-header"\u003e
                            \u003cspan class="kpi-icon"\u003e\u003ci class="fas fa-chart-line"\u003e\u003c/i\u003e\u003c/span\u003e
                            \u003cspan class="kpi-title"\u003eMargen Bruto Hoy\u003c/span\u003e
                        \u003c/div\u003e
                        \u003cdiv class="kpi-value"\u003e${kpis['margen_bruto']['margen_hoy']:,.2f}\u003c/div\u003e
                        \u003cdiv class="kpi-trend {"trend-up" if kpis['margen_bruto']['tendencia'] == 'up' else 'trend-down'}"\u003e
                            \u003ci class="fas fa-arrow-{kpis['margen_bruto']['tendencia']}"\u003e\u003c/i\u003e
                            {abs(kpis['margen_bruto']['cambio_pct'])}% vs ayer
                        \u003c/div\u003e
                    \u003c/div\u003e
                    
                    \u003c!-- Ticket Promedio --\u003e
                    \u003cdiv class="kpi-card"\u003e
                        \u003cdiv class="kpi-header"\u003e
                            \u003cspan class="kpi-icon"\u003e\u003ci class="fas fa-receipt"\u003e\u003c/i\u003e\u003c/span\u003e
                            \u003cspan class="kpi-title"\u003eTicket Promedio\u003c/span\u003e
                        \u003c/div\u003e
                        \u003cdiv class="kpi-value"\u003e${kpis['ticket_promedio']['ticket_promedio']:,.2f}\u003c/div\u003e
                        \u003cdiv class="kpi-info"\u003e{kpis['ticket_promedio']['cantidad_ventas']} ventas este mes\u003c/div\u003e
                    \u003c/div\u003e
                    
                    \u003c!-- Stock Bajo Alert --\u003e
                    \u003cdiv class="kpi-card {"kpi-alert" if kpis['stock_bajo']['count'] > 0 else 'kpi-success'}"\u003e
                        \u003cdiv class="kpi-header"\u003e
                            \u003cspan class="kpi-icon"\u003e\u003ci class="fas fa-exclamation-triangle"\u003e\u003c/i\u003e\u003c/span\u003e
                            \u003cspan class="kpi-title"\u003eAlerta Stock Bajo\u003c/span\u003e
                        \u003c/div\u003e
                        \u003cdiv class="kpi-value"\u003e{kpis['stock_bajo']['count']}\u003c/div\u003e
                        \u003cdiv class="kpi-info"\u003eproductos requieren atención\u003c/div\u003e
                    \u003c/div\u003e
                    
                    \u003c!-- Total Ventas del Mes --\u003e
                    \u003cdiv class="kpi-card kpi-highlight"\u003e
                        \u003cdiv class="kpi-header"\u003e
                            \u003cspan class="kpi-icon"\u003e\u003ci class="fas fa-dollar-sign"\u003e\u003c/i\u003e\u003c/span\u003e
                            \u003cspan class="kpi-title"\u003eVentas del Mes\u003c/span\u003e
                        \u003c/div\u003e
                        \u003cdiv class="kpi-value"\u003e${kpis['ventas_mes']['total_mes']:,.2f}\u003c/div\u003e
                        \u003cdiv class="kpi-info"\u003eTotal acumulado\u003c/div\u003e
                    \u003c/div\u003e
                \u003c/div\u003e
            \u003c/div\u003e
            """
            
            # Gráficas
            import json
            charts_section = f"""
            \u003cdiv class="charts-container"\u003e
                \u003c!-- Ventas del Mes --\u003e
                \u003cdiv class="chart-card"\u003e
                    \u003ch3\u003e\u003ci class="fas fa-chart-area"\u003e\u003c/i\u003e Evolución de Ventas - Mes Actual\u003c/h3\u003e
                    \u003ccanvas id="ventasMesChart"\u003e\u003c/canvas\u003e
                \u003c/div\u003e
                
                \u003c!-- Top Productos --\u003e
                \u003cdiv class="chart-card"\u003e
                    \u003ch3\u003e\u003ci class="fas fa-trophy"\u003e\u003c/i\u003e Top 3 Productos (Última Semana)\u003c/h3\u003e
                    \u003ccanvas id="topProductosChart"\u003e\u003c/canvas\u003e
                \u003c/div\u003e
            \u003c/div\u003e
            
            {chartjs_cdn}
            \u003cscript\u003e
            // Ventas del Mes - Line Chart
            const ventasCtx = document.getElementById('ventasMesChart');
            if (ventasCtx) {{
                new Chart(ventasCtx, {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(kpis['ventas_mes']['labels'])},
                        datasets: [{{
                            label: 'Ventas Diarias',
                            data: {json.dumps(kpis['ventas_mes']['data'])},
                            borderColor: 'rgb(99, 102, 241)',
                            backgroundColor: 'rgba(99, 102, 241, 0.1)',
                            tension: 0.4,
                            fill: true
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                padding: 12,
                                titleColor: '#fff',
                                bodyColor: '#fff',
                                callbacks: {{
                                    label: function(context) {{
                                        return 'Ventas: $' + context.parsed.y.toLocaleString('es-CO', {{minimumFractionDigits: 2}});
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{
                                    callback: function(value) {{
                                        return '$' + value.toLocaleString('es-CO');
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            }}
            
            // Top Productos - Bar Chart
            const productosCtx = document.getElementById('topProductosChart');
            if (productosCtx) {{
                const topProductos = {json.dumps(kpis['top_productos'])};
                
                new Chart(productosCtx, {{
                    type: 'bar',
                    data: {{
                        labels: topProductos.map(p => p.nombre),
                        datasets: [{{
                            label: 'Cantidad Vendida',
                            data: topProductos.map(p => p.cantidad),
                            backgroundColor: [
                                'rgba(239, 68, 68, 0.8)',
                                'rgba(59, 130, 246, 0.8)',
                                'rgba(251, 191, 36, 0.8)'
                            ],
                            borderWidth: 0
                        }}]
                    }},
                    options: {{
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                padding: 12,
                                callbacks: {{
                                    afterLabel: function(context) {{
                                        const producto = topProductos[context.dataIndex];
                                        return 'Ingresos: $' + producto.ingresos.toLocaleString('es-CO', {{minimumFractionDigits: 2}});
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{
                                beginAtZero: true,
                                ticks: {{
                                    stepSize: 1
                                }}
                            }}
                        }}
                    }}
                }});
            }}
            \u003c/script\u003e
            
            \u003cstyle\u003e
            .kpi-section {{
                margin: 2rem 0;
                padding: 1.5rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 16px;
                color: white;
            }}
            .section-title {{
                margin: 0 0 1.5rem 0;
                font-size: 1.5rem;
                font-weight: 600;
            }}
            .kpi-cards-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
            }}
            .kpi-card {{
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                color: #333;
                transition: transform 0.2s;
            }}
            .kpi-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            }}
            .kpi-header {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 1rem;
                font-weight: 600;
                color: #666;
            }}
            .kpi-icon {{
                font-size: 1.2rem;
            }}
            .kpi-value {{
                font-size: 2rem;
                font-weight: 700;
                color: #1f2937;
                margin-bottom: 0.5rem;
            }}
            .kpi-trend, .kpi-info {{
                font-size: 0.9rem;
                font-weight: 500;
            }}
            .trend-up {{
                color: #10b981;
            }}
            .trend-down {{
                color: #ef4444;
            }}
            .kpi-positive {{
                border-left: 4px solid #10b981;
            }}
            .kpi-negative {{
                border-left: 4px solid #ef4444;
            }}
            .kpi-alert {{
                border-left: 4px solid #f59e0b;
            }}
            .kpi-success {{
                border-left: 4px solid #10b981;
            }}
            .kpi-highlight {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .kpi-highlight .kpi-header,
            .kpi-highlight .kpi-value,
            .kpi-highlight .kpi-info {{
                color: white;
            }}
            .charts-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
                gap: 2rem;
                margin: 2rem 0;
            }}
            .chart-card {{
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .chart-card h3 {{
                margin: 0 0 1.5rem 0;
                color: #1f2937;
                font-size: 1.1rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            \u003c/style\u003e
            """
            
            kpi_section = kpi_cards + charts_section
            
            # Fase 2: Gráficas Avanzadas con Tabs
            charts_advanced = f"""
            <!-- Gráficas Avanzadas (Fase 2) -->
            <div class="charts-advanced-section">
                <h2 class="section-title-advanced">
                    <i class="fas fa-chart-pie"></i> Análisis Financiero Avanzado
                </h2>
                
                <!-- Tab Navigation -->
                <div class="tab-navigation">
                    <button class="tab-btn active" data-tab="flujo-caja">
                        <i class="fas fa-money-bill-wave"></i> Flujo de Caja
                    </button>
                    <button class="tab-btn" data-tab="rotacion" disabled title="Próximamente">
                        <i class="fas fa-sync-alt"></i> Rotación Inventario
                    </button>
                    <button class="tab-btn" data-tab="pareto" disabled title="Próximamente">
                        <i class="fas fa-users"></i> Análisis Clientes
                    </button>
                </div>
                
                <!-- Tab Content: Flujo de Caja -->
                <div class="tab-content active" id="tab-flujo-caja">
                    <div class="chart-card-large">
                        <h3>
                            <i class="fas fa-chart-line"></i> 
                            Flujo de Caja Mensual (Últimos 6 Meses)
                        </h3>
                        
                        <!-- Resumen de Flujo de Caja -->
                        <div class="cash-flow-summary">
                            <div class="summary-item positive">
                                <span>Total Ingresos:</span>
                                <strong>${kpis['flujo_caja']['total_ingresos']:,.2f}</strong>
                            </div>
                            <div class="summary-item negative">
                                <span>Total Egresos:</span>
                                <strong>${kpis['flujo_caja']['total_egresos']:,.2f}</strong>
                            </div>
                            <div class="summary-item {"positive" if kpis['flujo_caja']['total_neto'] > 0 else "negative"}">
                                <span>Flujo Neto:</span>
                                <strong>${kpis['flujo_caja']['total_neto']:,.2f}</strong>
                            </div>
                        </div>
                        
                        <canvas id="flujoCajaChart"></canvas>
                    </div>
                </div>
                
                <!-- Placeholder tabs (para futuro) -->
                <div class="tab-content" id="tab-rotacion">
                    <div class="placeholder-content">
                        <i class="fas fa-sync-alt fa-3x"></i>
                        <p>Próximamente: Rotación de Inventario por Categoría</p>
                        <small>Fase 2.2 - Optimización de Capital de Trabajo</small>
                    </div>
                </div>
                
                <div class="tab-content" id="tab-pareto">
                    <div class="placeholder-content">
                        <i class="fas fa-users fa-3x"></i>
                        <p>Próximamente: Análisis de Concentración de Clientes</p>
                        <small>Fase 2.3 - Análisis de Pareto (80/20)</small>
                    </div>
                </div>
            </div>
            
            <!-- JavaScript para Tabs y Flujo de Caja -->
            <script>
            // Tab switching (seguro, sin innerHTML)
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.addEventListener('click', function() {{
                    if (this.disabled) return;
                    
                    // Remove active class
                    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                    
                    // Add active to current (usando dataset, seguro)
                    this.classList.add('active');
                    const tabId = 'tab-' + this.dataset.tab;
                    const tabContent = document.getElementById(tabId);
                    if (tabContent) {{
                        tabContent.classList.add('active');
                    }}
                }});
            }});
            
            // Flujo de Caja Chart
            const flujoCajaCtx = document.getElementById('flujoCajaChart');
            if (flujoCajaCtx) {{
                // Datos seguros desde backend (solo números y strings controlados)
                const flujoCajaData = {json.dumps(kpis['flujo_caja'])};
                
                new Chart(flujoCajaCtx, {{
                    type: 'bar',
                    data: {{
                        labels: flujoCajaData.labels,
                        datasets: [
                            {{
                                label: 'Ingresos',
                                data: flujoCajaData.ingresos,
                                backgroundColor: 'rgba(34, 197, 94, 0.8)',
                                borderColor: 'rgba(34, 197, 94, 1)',
                                borderWidth: 1
                            }},
                            {{
                                label: 'Egresos',
                                data: flujoCajaData.egresos,
                                backgroundColor: 'rgba(239, 68, 68, 0.8)',
                                borderColor: 'rgba(239, 68, 68, 1)',
                                borderWidth: 1
                            }},
                            {{
                                type: 'line',
                                label: 'Flujo Neto',
                                data: flujoCajaData.flujo_neto,
                                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                                borderColor: 'rgba(99, 102, 241, 1)',
                                borderWidth: 2,
                                fill: false,
                                tension: 0.4,
                                yAxisID: 'y'
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        interaction: {{
                            mode: 'index',
                            intersect: false
                        }},
                        plugins: {{
                            legend: {{ 
                                position: 'top',
                                labels: {{
                                    usePointStyle: true,
                                    padding: 15
                                }}
                            }},
                            tooltip: {{
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                padding: 12,
                                titleColor: '#fff',
                                bodyColor: '#fff',
                                callbacks: {{
                                    label: function(context) {{
                                        const label = context.dataset.label || '';
                                        const value = context.parsed.y.toLocaleString('es-CO', {{
                                            minimumFractionDigits: 2,
                                            maximumFractionDigits: 2
                                        }});
                                        return label + ': $' + value;
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{
                                    callback: function(value) {{
                                        return '$' + value.toLocaleString('es-CO');
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            }}
            </script>
            
            <style>
            .charts-advanced-section {{
                margin: 2rem 0;
                padding: 1.5rem;
                background: white;
                border-radius: 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            
            .section-title-advanced {{
                margin: 0 0 1.5rem 0;
                font-size: 1.5rem;
                font-weight: 600;
                color: #1f2937;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .tab-navigation {{
                display: flex;
                gap: 1rem;
                margin-bottom: 1.5rem;
                border-bottom: 2px solid #e5e7eb;
                flex-wrap: wrap;
            }}
            
            .tab-btn {{
                background: none;
                border: none;
                padding: 0.75rem 1.5rem;
                font-size: 1rem;
                font-weight: 600;
                color: #6b7280;
                cursor: pointer;
                border-bottom: 3px solid transparent;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .tab-btn:hover:not(:disabled) {{
                color: #667eea;
                background: #f3f4f6;
            }}
            
            .tab-btn.active {{
                color: #667eea;
                border-bottom-color: #667eea;
            }}
            
            .tab-btn:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            
            .tab-content {{
                display: none;
                animation: fadeIn 0.3s;
            }}
            
            .tab-content.active {{
                display: block;
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}
            
            .chart-card-large {{
                background: white;
                padding: 2rem;
                border-radius: 12px;
            }}
            
            .chart-card-large h3 {{
                margin: 0 0 1.5rem 0;
                color: #1f2937;
                font-size: 1.2rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .cash-flow-summary {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                margin: 1.5rem 0;
                padding: 1.5rem;
                background: #f9fafb;
                border-radius: 8px;
            }}
            
            .summary-item {{
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }}
            
            .summary-item span {{
                font-size: 0.9rem;
                color: #6b7280;
                font-weight: 500;
            }}
            
            .summary-item strong {{
                font-size: 1.5rem;
                font-weight: 700;
            }}
            
            .summary-item.positive strong {{
                color: #22c55e;
            }}
            
            .summary-item.negative strong {{
                color: #ef4444;
            }}
            
            .placeholder-content {{
                text-align: center;
                padding: 4rem 2rem;
                color: #9ca3af;
            }}
            
            .placeholder-content i {{
                margin-bottom: 1rem;
                color: #d1d5db;
            }}
            
            .placeholder-content p {{
                font-size: 1.2rem;
                font-weight: 600;
                margin: 1rem 0 0.5rem 0;
                color: #6b7280;
            }}
            
            .placeholder-content small {{
                font-size: 0.9rem;
                color: #9ca3af;
            }}
            </style>
            """
        else:
            charts_advanced = ""

        content = (
            welcome_card
            + main_stats
            + kpi_section
            + charts_advanced
            + secondary_stats
            + productos_stock_section
            + ultimas_ventas_section
            + ultimas_compras_section
        )

        return HttpResponse(Layout.render("Dashboard", user, "dashboard", content))
