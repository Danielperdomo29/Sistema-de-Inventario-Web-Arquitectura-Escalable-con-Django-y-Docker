

from app.views.layout import Layout


class SaleView:
    """Vista de Ventas"""

    @staticmethod
    def _get_dian_button(sale):
        factura = sale.get("factura_dian")
        if factura and factura.archivo_pdf and factura.archivo_pdf.name:
            # Usar la URL del FileField
            pdf_url = factura.archivo_pdf.url
            return f'<a href="{pdf_url}" target="_blank" class="btn btn-success no-underline" title="{factura.numero_factura}"><i class="fas fa-file-pdf"></i> PDF</a>'
        else:
            return f'<a href="/dian/generar/{sale["id"]}/" class="btn btn-info no-underline"><i class="fas fa-bolt"></i> Generar</a>'

    @staticmethod
    def _get_delete_button(sale, csrf_token):
        csrf_input = f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">'

        if hasattr(sale, "factura_dian") or sale.get("numero_factura", "").startswith("FE"):
            # Simple check for dictionary or object
            is_factura = sale.get("factura_dian") if isinstance(sale, dict) else getattr(sale, "factura_dian", None)
            if is_factura:
                return f"""
                <form action="/ventas/{sale['id']}/eliminar/" method="POST" style="display:inline;">
                    {csrf_input}
                    <button type="submit" class="btn btn-danger no-underline"
                        data-confirm-message="La venta tiene Factura DIAN. Se procederá a ANULARLA en lugar de eliminarla. ¿Continuar?"
                        onclick="return confirmDelete(event, this);">Anular</button>
                </form>
                """

        return f"""
        <form action="/ventas/{sale['id']}/eliminar/" method="POST" style="display:inline;">
            {csrf_input}
            <button type="submit" class="btn btn-danger no-underline" onclick="return confirmDelete(event, this);">Eliminar</button>
        </form>
        """

    @staticmethod
    def _get_filter_form(params):
        """Genera la barra de filtros estilo iOS unificada"""
        fecha_desde = params.get("fecha_desde", "")
        fecha_hasta = params.get("fecha_hasta", "")
        cliente = params.get("cliente", "")
        producto = params.get("producto", "")
        factura = params.get("factura", "")

        return f"""
        <style>
            .sales-filter-bar {{
                display: flex;
                flex-wrap: nowrap; /* Forzar una sola línea */
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                background: rgba(255, 255, 255, 0.8);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border-radius: 36px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.05);
                margin-bottom: 24px;
                font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
                overflow-x: auto; /* Scroll horizontal */
                -webkit-overflow-scrolling: touch;
                scrollbar-width: none; /* Ocultar scrollbar en Firefox */
                -ms-overflow-style: none; /* Ocultar scrollbar en IE/Edge */
            }}
            /* Ocultar scrollbar en navegadores WebKit (Chrome, Safari) */
            .sales-filter-bar::-webkit-scrollbar {{
                display: none;
            }}
            .sales-filter-bar .filter-icon {{
                display: flex;
                align-items: center;
                justify-content: center;
                width: 32px;
                height: 32px;
                background: #007AFF;
                border-radius: 50%;
                color: white;
                font-size: 14px;
                margin-right: 4px;
                flex-shrink: 0;
            }}
            .sales-filter-bar .filter-item {{
                display: flex;
                align-items: center;
                background: rgba(242, 242, 247, 0.8);
                border-radius: 20px;
                padding: 0 12px;
                height: 36px;
                border: 1px solid transparent;
                transition: all 0.15s ease;
                flex-shrink: 0; /* Evitar que se encojan demasiado */
                min-width: 140px; /* Tamaño mínimo razonable */
            }}
            .sales-filter-bar .filter-item:focus-within {{
                background: white;
                border-color: #007AFF;
                box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
            }}
            .sales-filter-bar .filter-item i {{
                color: #8E8E93;
                font-size: 14px;
                margin-right: 8px;
                width: 16px;
                text-align: center;
            }}
            .sales-filter-bar .filter-input {{
                width: 100%;
                border: none;
                background: transparent;
                font-size: 14px;
                color: #1C1C1E;
                outline: none;
                font-family: inherit;
                padding: 0;
                line-height: 1.4;
            }}
            .sales-filter-bar .filter-input::placeholder {{
                color: #8E8E93;
                font-weight: 400;
            }}
            .sales-filter-bar .filter-btn {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
                height: 36px;
                padding: 0 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 500;
                border: none;
                cursor: pointer;
                transition: all 0.15s ease;
                white-space: nowrap;
                text-decoration: none;
                flex-shrink: 0;
            }}
            .sales-filter-bar .filter-btn-primary {{
                background: #007AFF;
                color: white;
                box-shadow: 0 4px 8px rgba(0, 122, 255, 0.15);
            }}
            .sales-filter-bar .filter-btn-primary:hover {{
                background: #005BBF;
                transform: scale(0.98);
            }}
            .sales-filter-bar .filter-btn-clear {{
                background: transparent;
                color: #8E8E93;
                border: 1px solid rgba(142, 142, 147, 0.2);
            }}
            .sales-filter-bar .filter-btn-clear:hover {{
                background: rgba(142, 142, 147, 0.1);
                color: #1C1C1E;
            }}
            /* Indicador visual de scroll en móviles */
            @media (max-width: 768px) {{
                .sales-filter-bar {{
                    border-radius: 20px;
                    padding-right: 24px; /* Espacio extra al final para indicar que hay más */
                    margin-bottom: 20px;
                }}
            }}

            /* Responsive Header Actions */
            .header-actions-mobile {{
                display: flex;
                flex-direction: column;
                gap: 16px;
                margin-bottom: 24px;
            }}
            .btn-action-responsive {{
                width: 100%;
                text-align: center;
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 8px;
                padding: 10px 16px;
            }}
            @media (min-width: 768px) {{
                .header-actions-mobile {{
                    flex-direction: row;
                    justify-content: space-between;
                    align-items: center;
                }}
                .btn-action-responsive {{
                    width: auto;
                }}
            }}
        </style>
        <form id="filter-form" method="GET" action="/ventas/" class="sales-filter-bar">
            <div class="filter-icon">
                <i class="fas fa-sliders-h"></i>
            </div>
            <div class="filter-item">
                <i class="far fa-calendar-alt"></i>
                <input type="date" name="fecha_desde" placeholder="Desde" class="filter-input" value="{fecha_desde}" autocomplete="off">
            </div>
            <div class="filter-item">
                <i class="far fa-calendar-alt"></i>
                <input type="date" name="fecha_hasta" placeholder="Hasta" class="filter-input" value="{fecha_hasta}" autocomplete="off">
            </div>
            <div class="filter-item">
                <i class="far fa-user"></i>
                <input type="text" name="cliente" class="filter-input" placeholder="Cliente" value="{cliente}" autocomplete="off">
            </div>
            <div class="filter-item">
                <i class="fas fa-box-open"></i>
                <input type="text" name="producto" class="filter-input" placeholder="Producto" value="{producto}" autocomplete="off">
            </div>
            <div class="filter-item">
                <i class="fas fa-file-invoice"></i>
                <input type="text" name="factura" class="filter-input" placeholder="# Factura" value="{factura}" autocomplete="off">
            </div>
            <button type="submit" class="filter-btn filter-btn-primary">
                <i class="fas fa-search"></i>
                <span>Filtrar</span>
            </button>
            <a href="/ventas/" class="filter-btn filter-btn-clear">
                <i class="fas fa-times"></i>
                <span>Limpiar</span>
            </a>
        </form>
        """

    @staticmethod
    def render_rows(user, sales, request):
        """Genera solo las filas de la tabla (para AJAX y uso interno)"""
        if not sales:
            return '<tr><td colspan="9" class="text-center">No hay ventas registradas.</td></tr>'

        # Mapeo de estados a badges
        estado_badges = {
            "pendiente": '<span class="badge badge-warning">Pendiente</span>',
            "completada": '<span class="badge badge-success">Completada</span>',
            "cancelada": '<span class="badge badge-cancelada">Cancelada</span>',
            "anulada": '<span class="badge badge-danger">Anulada</span>',
        }

        from django.middleware.csrf import get_token

        csrf_token = get_token(request)

        rows = ""
        for sale in sales:
            badge = estado_badges.get(sale["estado"], sale["estado"])

            # Safe access to fields
            date_val = sale.get("fecha", "")
            # Clean date format if needed

            rows += f"""
            <tr>
                <td>{sale['numero_factura']}</td>
                <td class="d-none d-md-table-cell">{date_val}</td>
                <td>{sale['cliente_nombre']}</td>
                <td class="d-none d-md-table-cell">{sale.get('cliente_documento') or 'N/A'}</td>
                <td>
                    <div class="font-bold" style="color: #2c3e50;">Total: ${sale['total']:,.2f}</div>
                    <div style="font-size: 0.8rem; color: #6c757d;">Total sin IVA: ${(sale['total'] - sale.get('iva', 0)):,.2f}</div>
                    <div style="font-size: 0.8rem; color: #6c757d;">IVA: ${sale.get('iva', 0):,.2f}</div>
                </td>
                <td>{badge}</td>
                <td class="d-none d-md-table-cell">{sale['tipo_pago'].capitalize()}</td>
                <td>
                    {SaleView._get_dian_button(sale)}
                </td>
                <td>
                    <div class="d-flex gap-2">
                        <a href="/ventas/{sale['id']}/editar/" class="btn btn-warning btn-sm no-underline" title="Editar"><i class="fas fa-edit"></i></a>
                        {SaleView._get_delete_button(sale, csrf_token)}
                    </div>
                </td>
            </tr>
            """
        return rows

    @staticmethod
    def index(user, sales, request):
        """Renderiza la página de listado de ventas"""

        # Obtener parámetros GET para rellenar el formulario
        params = request.GET.dict()
        filter_form = SaleView._get_filter_form(params)

        rows = SaleView.render_rows(user, sales, request)

        table_content = f"""
        <div class="header-actions-mobile">
            <h1 class="h3 mb-0 text-gray-800">Gestión de Ventas</h1>
            <a href="/ventas/crear/" class="btn btn-primary no-underline btn-action-responsive">
                <i class="fas fa-plus"></i> Nueva Venta
            </a>
        </div>

        {filter_form}

        <div class="card shadow mb-4">
            <div class="card-body">
                <div class="table-container">
                    <table class="table table-hover" id="sales-table">
                        <thead class="bg-light">
                            <tr>
                                <th>Factura</th>
                                <th class="d-none d-md-table-cell">Fecha</th>
                                <th>Cliente</th>
                                <th class="d-none d-md-table-cell">Documento</th>
                                <th>Total</th>
                                <th>Estado</th>
                                <th class="d-none d-md-table-cell">Tipo Pago</th>
                                <th>DIAN</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody id="sales-table-body">
                            {rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Script para manejo AJAX del filtro -->
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const filterForm = document.getElementById('filter-form');
            const tableBody = document.getElementById('sales-table-body');

            filterForm.addEventListener('submit', function(e) {{
                e.preventDefault();

                // Validación: al menos un campo debe estar lleno
                let hasValue = false;
                const inputs = filterForm.querySelectorAll('.filter-input');
                inputs.forEach(input => {{
                    if (input.value.trim() !== '') hasValue = true;
                }});

                if (!hasValue) {{
                    if (typeof Swal !== 'undefined') {{
                        Swal.fire({{
                            icon: 'warning',
                            title: 'Filtros Vacíos',
                            text: 'Por favor, ingresa al menos un criterio (fecha, cliente, producto o factura) para realizar la búsqueda.',
                            confirmButtonColor: '#007AFF',
                            confirmButtonText: 'Entendido',
                            customClass: {{
                                popup: 'rounded-xl shadow-lg border-0'
                            }}
                        }});
                    }} else {{
                        alert('Por favor ingresa al menos un criterio para filtrar.');
                    }}
                    return; // Detener envío
                }}

                // Mostrar estado de carga
                tableBody.style.opacity = '0.5';

                const formData = new FormData(this);
                const params = new URLSearchParams(formData).toString();

                fetch(`${{this.action}}?${{params}}`, {{
                    headers: {{
                        'X-Requested-With': 'XMLHttpRequest'
                    }}
                }})
                .then(response => response.text())
                .then(html => {{
                    tableBody.innerHTML = html;
                    tableBody.style.opacity = '1';
                }})
                .catch(error => {{
                    console.error('Error:', error);
                    tableBody.style.opacity = '1';
                    if (typeof Swal !== 'undefined') {{
                        Swal.fire('Error', 'Error al filtrar. Por favor intente de nuevo.', 'error');
                    }}
                }});

                // Actualizar URL sin recargar
                window.history.pushState({{}}, '', `?${{params}}`);
            }});
        }});
        </script>
        """

        return Layout.render("Gestión de Ventas", user, "ventas", table_content)

    @staticmethod
    def create(user, clients, products, request, error=None):
        """Vista del formulario de crear venta"""

        # Obtener token CSRF
        from django.middleware.csrf import get_token

        csrf_token = get_token(request)

        # Generar opciones de clientes
        client_options = '<option value="">Seleccione un cliente</option>'
        for client in clients:
            client_options += (
                f'<option value="{client["id"]}">{client["nombre"]} - {client.get("documento", "S/N")}</option>'
            )

        import json

        # Generar opciones de productos para el selector
        product_options = '<option value="">Seleccione un producto</option>'
        products_list = []
        for product in products:
            product_options += (
                f'<option value="{product["id"]}">{product["nombre"]} - ${product["precio_venta"]}</option>'
            )
            products_list.append(
                {
                    "id": product["id"],
                    "nombre": product["nombre"],
                    "precio": float(product["precio_venta"]),
                    "stock": product["stock_actual"],
                    "iva_porcentaje": float(product.get("iva_porcentaje", 19.00)),
                    "iva_tipo": product.get("iva_tipo", "GRAVADO"),
                    "descuento": float(product.get("descuento", 0.00)),
                }
            )
        products_json = json.dumps(products_list)

        # SweetAlert2 for server-side errors
        error_script = ""
        if error:
            error_script = f"""
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                Swal.fire({{
                    icon: 'error',
                    title: 'Error de Validación',
                    text: '{error}',
                    confirmButtonColor: '#3085d6'
                }});
            }});
            </script>
            """

        # Fecha actual
        from datetime import date

        fecha_actual = date.today().strftime("%Y-%m-%d")

        # Librería Tom Select (Buscador Predictivo)
        header_links = """
        <link href="https://cdn.jsdelivr.net/npm/tom-select@2.2.2/dist/css/tom-select.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/tom-select@2.2.2/dist/js/tom-select.complete.min.js"></script>
        <style>
            .ts-control { border-radius: 8px !important; padding: 10px !important; border: 1px solid #ced4da !important; }
            .ts-dropdown { border-radius: 8px !important; box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important; }
        </style>
        """

        content = f"""
        {header_links}
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-shopping-cart"></i> Crear Nueva Venta</span>
                <a href="/ventas/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/ventas/crear/" id="saleForm" class="p-20" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                <input type="hidden" name="details" id="details">

                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Cliente *</label>
                        <select name="cliente_id" class="form-select"
                                data-rules="required"
                                data-label="Cliente">
                            {client_options}
                        </select>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Fecha *</label>
                        <input type="date" name="fecha" value="{fecha_actual}" class="form-input"
                               data-rules="required"
                               data-label="Fecha">
                    </div>

                    <div>
                        <label class="form-label">Tipo de Pago</label>
                        <select name="tipo_pago" class="form-select">
                            <option value="efectivo">Efectivo</option>
                            <option value="tarjeta">Tarjeta</option>
                            <option value="transferencia">Transferencia</option>
                        </select>
                    </div>

                    <div>
                        <label class="form-label">Estado</label>
                        <select name="estado" class="form-select">
                            <option value="completada">Completada</option>
                            <option value="pendiente">Pendiente</option>
                        </select>
                    </div>
                </div>

                <div class="mb-20">
                    <label class="form-label">Notas</label>
                    <textarea name="notas" rows="2" class="form-textarea"></textarea>
                </div>

                <hr class="form-divider">

                <h3 class="mb-15">Productos</h3>
                <div class="product-input-grid">
                    <select id="productSelect" class="form-select">
                        {product_options}
                    </select>
                    <input type="number" id="quantityInput" placeholder="Cantidad" min="1" value="1" class="form-input">
                    <button type="button" onclick="addProduct()" class="btn btn-primary">Agregar</button>
                </div>

                <div class="table-container">
                    <table id="productsTable" class="table table-hover d-none mb-4" style="width: 100%;">
                        <thead class="bg-light">
                            <tr>
                                <th>Producto</th>
                                <th>Precio Base</th>
                                <th>Cant</th>
                                <th>Desc %</th>
                                <th>Subtotal (Base)</th>
                                <th class="d-none d-md-table-cell">IVA %</th>
                                <th>Total</th>
                                <th>Acción</th>
                            </tr>
                        </thead>
                        <tbody id="productsBody"></tbody>
                    </table>
                </div>

                <!-- Nuevo Panel de Resumen Vertical (DIAN) -->
                <div class="row justify-content-end mt-4">
                    <div class="col-md-5 col-lg-4">
                        <div class="card shadow-sm border-0" style="background-color: #f8f9fa; border-radius: 12px;">
                            <div class="card-body p-4">
                                <h6 class="font-weight-bold text-uppercase mb-4 text-muted border-bottom pb-2">
                                    <i class="fas fa-calculator mr-2"></i> Resumen de Factura
                                </h6>

                                <div class="d-flex justify-content-between mb-3 align-items-center">
                                    <span class="text-secondary font-weight-medium">Subtotal (Bruto)</span>
                                    <span id="resumen-subtotal" class="font-weight-bold text-dark">$ 0.00</span>
                                </div>

                                <div class="d-flex justify-content-between mb-3 align-items-center">
                                    <span class="text-secondary font-weight-medium">Descuentos</span>
                                    <span id="resumen-descuentos" class="text-danger font-weight-bold">- $ 0.00</span>
                                </div>

                                <div class="d-flex justify-content-between mb-3 align-items-center border-top pt-3">
                                    <span class="text-dark font-weight-bold">Base Gravable (Sin IVA)</span>
                                    <span id="resumen-base" class="font-weight-bold text-dark h5 mb-0">$ 0.00</span>
                                </div>

                                <div id="resumen-impuestos" class="mt-3">
                                    <div class="d-flex justify-content-between mb-3 align-items-center">
                                        <span class="text-secondary font-weight-medium">IVA Total</span>
                                        <span id="resumen-iva" class="font-weight-bold text-dark">$ 0.00</span>
                                    </div>
                                </div>

                                <div class="border-top border-primary pt-3 mt-3" style="border-top-width: 3px !important;">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="h5 font-weight-bold text-primary mb-0">TOTAL A PAGAR</span>
                                        <span class="h3 font-weight-bold text-primary mb-0" id="resumen-total">$ 0.00</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                </div>

                <div class="form-actions mt-30">
                    <button type="submit" class="btn btn-primary" data-original-text="Guardar Venta"><i class="fas fa-save"></i> Guardar Venta</button>
                    <a href="/ventas/" class="btn btn-secondary no-underline">Cancelar</a>
                </div>
            </form>
        </div>

        <script src="/static/js/product-manager.js?v=4"></script>
        <script>
            // Inicializar el gestor de productos con los datos del servidor
            const products = {products_json};
            manager = new ProductManager(products);

            // Inicializar Buscador Predictivo (FASE 4)
            new TomSelect("#productSelect", {{
                create: false,
                sortField: {{
                    field: "text",
                    direction: "asc"
                }},
                placeholder: "Buscar producto por nombre o código..."
            }});
        </script>
        {error_script}
        """

        return Layout.render("Crear Venta", user, "ventas", content)

    @staticmethod
    def edit(user, sale, details, clients, products, request, error=None):
        """Vista del formulario de editar venta"""

        # Obtener token CSRF
        from django.middleware.csrf import get_token

        csrf_token = get_token(request)

        # Generar opciones de clientes
        client_options = '<option value="">Seleccione un cliente</option>'
        for client in clients:
            selected = "selected" if client["id"] == sale.get("cliente_id") else ""
            client_options += f'<option value="{client["id"]}" {selected}>{client["nombre"]} - {client.get("documento", "S/N")}</option>'

        import json

        # Generar opciones de productos
        product_options = '<option value="">Seleccione un producto</option>'
        products_list = []
        for product in products:
            product_options += (
                f'<option value="{product["id"]}">{product["nombre"]} - ${product["precio_venta"]}</option>'
            )
            products_list.append(
                {
                    "id": product["id"],
                    "nombre": product["nombre"],
                    "precio": float(product["precio_venta"]),
                    "stock": product["stock_actual"],
                    "iva_porcentaje": float(product.get("iva_porcentaje", 19.00)),
                    "iva_tipo": product.get("iva_tipo", "GRAVADO"),
                    "descuento": float(product.get("descuento", 0.00)),
                }
            )
        products_json = json.dumps(products_list)

        # Preparar detalles existentes
        existing_details = []
        for detail in details:
            existing_details.append(
                {
                    "producto_id": detail["producto_id"],
                    "nombre": detail["producto_nombre"],
                    "precio_unitario_base": float(detail["precio_unitario"]),
                    "cantidad": detail["cantidad"],
                    "descuento_pct": float(detail.get("descuento_tasa", 0) or 0),
                    "valor_descuento": float(detail.get("descuento_valor", 0) or 0),
                    "subtotal_base": float(detail.get("subtotal_sin_iva", 0) or 0),
                    "iva_tasa": float(detail.get("iva_tasa", 19) or 19),
                    "iva_valor": float(detail.get("iva_valor", 0) or 0),
                    "subtotal": float(detail["subtotal"]),
                }
            )

        # SweetAlert2 for server-side errors
        error_script = ""
        if error:
            error_script = f"""
            <script>
            document.addEventListener('DOMContentLoaded', function() {{
                Swal.fire({{
                    icon: 'error',
                    title: 'Error de Validación',
                    text: '{error}',
                    confirmButtonColor: '#3085d6'
                }});
            }});
            </script>
            """

        # Librería Tom Select (Buscador Predictivo)
        header_links = """
        <link href="https://cdn.jsdelivr.net/npm/tom-select@2.2.2/dist/css/tom-select.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/tom-select@2.2.2/dist/js/tom-select.complete.min.js"></script>
        <style>
            .ts-control { border-radius: 8px !important; padding: 10px !important; border: 1px solid #ced4da !important; }
            .ts-dropdown { border-radius: 8px !important; box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important; }
        </style>
        """

        content = f"""
        {header_links}
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-edit"></i> Editar Venta - {sale['numero_factura']}</span>
                <a href="/ventas/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/ventas/{sale['id']}/editar/" id="saleForm" class="p-20" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                <input type="hidden" name="details" id="details">
                <input type="hidden" name="numero_factura" value="{sale['numero_factura']}">

                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Cliente *</label>
                        <select name="cliente_id" class="form-select"
                                data-rules="required"
                                data-label="Cliente">
                            {client_options}
                        </select>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Fecha *</label>
                        <input type="date" name="fecha" value="{sale['fecha'].strftime('%Y-%m-%d') if hasattr(sale['fecha'], 'strftime') else sale['fecha'][:10]}" class="form-input"
                               data-rules="required"
                               data-label="Fecha">
                    </div>

                    <div>
                        <label class="form-label">Tipo de Pago</label>
                        <select name="tipo_pago" class="form-select">
                            <option value="efectivo" {'selected' if sale.get('tipo_pago') == 'efectivo' else ''}>Efectivo</option>
                            <option value="tarjeta" {'selected' if sale.get('tipo_pago') == 'tarjeta' else ''}>Tarjeta</option>
                            <option value="transferencia" {'selected' if sale.get('tipo_pago') == 'transferencia' else ''}>Transferencia</option>
                        </select>
                    </div>

                    <div>
                        <label class="form-label">Estado</label>
                        <select name="estado" class="form-select">
                            <option value="completada" {'selected' if sale.get('estado') == 'completada' else ''}>Completada</option>
                            <option value="pendiente" {'selected' if sale.get('estado') == 'pendiente' else ''}>Pendiente</option>
                            <option value="cancelada" {'selected' if sale.get('estado') == 'cancelada' else ''}>Cancelada</option>
                        </select>
                    </div>
                </div>

                <div class="mb-20">
                    <label class="form-label">Notas</label>
                    <textarea name="notas" rows="2" class="form-textarea">{sale.get('notas', '')}</textarea>
                </div>

                <hr class="form-divider">

                <h3 class="mb-15">Productos</h3>
                <div class="product-input-grid">
                    <select id="productSelect" class="form-select">
                        {product_options}
                    </select>
                    <input type="number" id="quantityInput" placeholder="Cantidad" min="1" value="1" class="form-input">
                    <button type="button" onclick="addProduct()" class="btn btn-primary">Agregar</button>
                </div>

                <div class="table-container">
                    <table id="productsTable" class="table table-hover d-none mb-4" style="width: 100%;">
                        <thead class="bg-light">
                            <tr>
                                <th>Producto</th>
                                <th>Precio Base</th>
                                <th>Cant</th>
                                <th>Desc %</th>
                                <th>Subtotal (Base)</th>
                                <th class="d-none d-md-table-cell">IVA %</th>
                                <th>Total</th>
                                <th>Acción</th>
                            </tr>
                        </thead>
                        <tbody id="productsBody"></tbody>
                    </table>
                </div>

                <!-- Nuevo Panel de Resumen Vertical (DIAN) -->
                <div class="row justify-content-end mt-4">
                    <div class="col-md-5 col-lg-4">
                        <div class="card shadow-sm border-0" style="background-color: #f8f9fa; border-radius: 12px;">
                            <div class="card-body p-4">
                                <h6 class="font-weight-bold text-uppercase mb-4 text-muted border-bottom pb-2">
                                    <i class="fas fa-calculator mr-2"></i> Resumen de Factura
                                </h6>

                                <div class="d-flex justify-content-between mb-3 align-items-center">
                                    <span class="text-secondary font-weight-medium">Subtotal (Bruto)</span>
                                    <span id="resumen-subtotal" class="font-weight-bold text-dark">$ 0.00</span>
                                </div>

                                <div class="d-flex justify-content-between mb-3 align-items-center">
                                    <span class="text-secondary font-weight-medium">Descuentos</span>
                                    <span id="resumen-descuentos" class="text-danger font-weight-bold">- $ 0.00</span>
                                </div>

                                <div class="d-flex justify-content-between mb-3 align-items-center border-top pt-3">
                                    <span class="text-dark font-weight-bold">Base Gravable (Sin IVA)</span>
                                    <span id="resumen-base" class="font-weight-bold text-dark h5 mb-0">$ 0.00</span>
                                </div>

                                <div id="resumen-impuestos" class="mt-3">
                                    <div class="d-flex justify-content-between mb-3 align-items-center">
                                        <span class="text-secondary font-weight-medium">IVA Total</span>
                                        <span id="resumen-iva" class="font-weight-bold text-dark">$ 0.00</span>
                                    </div>
                                </div>

                                <div class="border-top border-primary pt-3 mt-3" style="border-top-width: 3px !important;">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="h5 font-weight-bold text-primary mb-0">TOTAL A PAGAR</span>
                                        <span class="h3 font-weight-bold text-primary mb-0" id="resumen-total">$ 0.00</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="form-actions mt-30">
                    <button type="submit" class="btn btn-primary" data-original-text="Actualizar Venta"><i class="fas fa-save"></i> Actualizar Venta</button>
                    <a href="/ventas/" class="btn btn-secondary no-underline">Cancelar</a>
                </div>
            </form>
        </div>

        <script src="/static/js/product-manager.js?v=4"></script>
        <script>
            // Inicializar el gestor de productos con los datos del servidor
            const products = {products_json};
            const existingDetails = {json.dumps(existing_details)};
            manager = new ProductManager(products, existingDetails);
            manager.render();

            // Inicializar Buscador Predictivo (FASE 4)
            new TomSelect("#productSelect", {{
                create: false,
                sortField: {{
                    field: "text",
                    direction: "asc"
                }},
                placeholder: "Buscar producto por nombre o código..."
            }});
        </script>
        {error_script}
        """

        return Layout.render("Editar Venta", user, "ventas", content)

    @staticmethod
    def view(user, sale, details):
        """Vista de detalle de una venta"""


        estado_class = {"pendiente": "warning", "completada": "success", "cancelada": "danger"}.get(
            sale["estado"], "secondary"
        )

        # Detalles de productos
        details_rows = ""
        if details:
            for idx, detail in enumerate(details, 1):
                details_rows += f"""
                <tr>
                    <td>{idx}</td>
                    <td>{detail['producto_nombre']}</td>
                    <td>{detail['cantidad']}</td>
                    <td>S/ {detail['precio_unitario']:.2f}</td>
                    <td>S/ {detail['subtotal']:.2f}</td>
                </tr>
                """
        else:
            details_rows = '<tr><td colspan="5" class="text-center text-muted">Sin productos</td></tr>'

        content = f"""
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1 class="h3 mb-0">Detalle de Venta #{sale['id']}</h1>
            <div>
                <a href="/ventas/{sale['id']}/editar/" class="btn btn-warning">
                    <i class="fas fa-edit"></i> Editar
                </a>
                <a href="/ventas/" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> Volver
                </a>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6 mb-4">
                <div class="card shadow-sm">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">Información de la Venta</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-2">
                            <strong>N° Factura:</strong> {sale.get('numero_factura', 'N/A')}
                        </div>
                        <div class="mb-2">
                            <strong>Cliente:</strong> {sale['cliente_nombre']}
                        </div>
                        <div class="mb-2">
                            <strong>Fecha:</strong> {sale['fecha']}
                        </div>
                        <div class="mb-2">
                            <strong>Estado:</strong>
                            <span class="badge bg-{estado_class}">{sale['estado']}</span>
                        </div>
                        <div class="mb-2">
                            <strong>Tipo de Pago:</strong> {sale.get('tipo_pago', 'N/A')}
                        </div>
                        <div class="mb-2">
                            <strong>Usuario:</strong> {sale.get('vendedor', 'N/A')}
                        </div>
                        <div class="mb-2">
                            <strong>Notas:</strong> {sale.get('notas', 'Sin notas')}
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-6 mb-4">
                <div class="card shadow-sm">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0">Totales</h5>
                    </div>
                    <div class="card-body">
                         <div class="mb-3 text-center">
                            {SaleView._get_dian_button(sale)}
                        </div>
                        <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                            <span class="h4 mb-0">Total:</span>
                            <span class="h3 mb-0 text-success">S/ {sale['total']:.2f}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card shadow-sm">
            <div class="card-header bg-light">
                <h5 class="mb-0">Productos</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead class="table-light">
                            <tr>
                                <th width="50">#</th>
                                <th>Producto</th>
                                <th width="100">Cantidad</th>
                                <th width="120">P. Unitario</th>
                                <th width="120">Subtotal</th>
                            </tr>
                        </thead>
                        <tbody>
                            {details_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        """

        from app.views.layout import Layout

        return Layout.render("Detalle de Venta", user, "ventas", content)
