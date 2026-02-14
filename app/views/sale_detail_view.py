from django.http import HttpResponse
from django.middleware.csrf import get_token

from app.views.layout import Layout


class SaleDetailView:
    @staticmethod
    def index(user, details, request):
        """Vista de lista de detalles de ventas"""

        csrf_token = get_token(request)

        # Tabla de detalles
        rows = ""
        if details:
            for idx, detail in enumerate(details, 1):
                rows += f"""
                <tr>
                    <td class="d-none d-md-table-cell">{idx}</td>
                    <td class="d-none d-md-table-cell">{detail.get('numero_factura', 'N/A')}</td>
                    <td class="d-none d-md-table-cell">{detail['cliente_nombre']}</td>
                    <td class="d-none d-md-table-cell">{detail['fecha_venta']}</td>
                    <td>{detail['producto_nombre']}</td>
                    <td>{detail['cantidad']}</td>
                    <td>$ {detail['precio_unitario']:.2f}</td>
                    <td>$ {detail['subtotal']:.2f}</td>
                    <td>
                        <a href="/items-venta/{detail['id']}/ver/" class="btn btn-info btn-sm">
                            <i class="fas fa-eye"></i> Ver
                        </a>
                        <a href="/items-venta/{detail['id']}/editar/" class="btn btn-warning btn-sm">
                            <i class="fas fa-edit"></i> Editar
                        </a>
                        <button type="button" class="btn btn-danger btn-sm" 
                                onclick="confirmDeleteAction('/items-venta/{detail['id']}/eliminar/', '{csrf_token}', 'Detalle #{detail['id']}');">
                            <i class="fas fa-trash"></i> Eliminar
                        </button>
                    </td>
                </tr>
                """

            table_content = f"""
            <div class="table-container">
                <table>
                <thead>
                    <tr>
                        <th class="d-none d-md-table-cell">#</th>
                        <th class="d-none d-md-table-cell">N° Factura</th>
                        <th class="d-none d-md-table-cell">Cliente</th>
                        <th class="d-none d-md-table-cell">Fecha</th>
                        <th>Producto</th>
                        <th>Cantidad</th>
                        <th>Precio Unit.</th>
                        <th>Subtotal</th>
                        <th>Acciones</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
                </table>
            </div>
            """
        else:
            table_content = """
            <div class="empty-state">
                <i class="fas fa-file-invoice icon-4xl"></i>
                <h3>No hay detalles de ventas registrados</h3>
                <p>Comienza agregando el primer detalle</p>
            </div>
            """

        content = f"""
        <div class="card">
            <div class="card-header">
                <span>Gestión de Detalles de Ventas</span>
                <a href="/items-venta/crear/" class="btn btn-primary"><i class="fas fa-plus"></i> Nuevo Detalle</a>
            </div>
            {table_content}
        </div>
        """

        return Layout.render("Detalles de Ventas", user, "items-venta", content)

    @staticmethod
    def create(user, sales, products, request, error=None):
        """Vista de formulario para crear detalle de venta"""

        csrf_token = get_token(request)

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

        # Select de ventas
        sale_options = '<option value="">Seleccione una venta</option>'
        for sale in sales:
            sale_options += f'<option value="{sale["id"]}">{sale.get("numero_factura", "Sin factura")} - {sale["cliente_nombre"]} ({sale["fecha"]})</option>'

        # Select de productos
        product_options = '<option value="">Seleccione un producto</option>'
        for product in products:
            product_options += f'<option value="{product["id"]}" data-price="{product["precio_venta"]}">{product["nombre"]} - $ {product["precio_venta"]:.2f}</option>'

        content = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-file-invoice"></i> Crear Nuevo Detalle de Venta</span>
                <a href="/items-venta/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/items-venta/crear/" class="p-20" id="detailForm" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Venta *</label>
                        <select name="venta_id" class="form-select"
                                data-rules="required"
                                data-label="Venta">
                            {sale_options}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Producto *</label>
                        <select name="producto_id" id="producto" class="form-select"
                                data-rules="required"
                                data-label="Producto">
                            {product_options}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Cantidad *</label>
                        <input type="number" name="cantidad" id="cantidad" value="1" min="1" class="form-input"
                               data-rules="required|numeric|min:1"
                               data-label="Cantidad">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Precio Unitario *</label>
                        <input type="number" name="precio_unitario" id="precio_unitario" step="0.01" min="0" class="form-input"
                               data-rules="required|min:0"
                               data-label="Precio Unitario">
                    </div>
                </div>
                
                <div class="total-summary">
                    <p>
                        Subtotal: $ <span id="subtotal">0.00</span>
                    </p>
                </div>
                
                <div class="form-actions-end mt-30">
                    <a href="/items-venta/" class="btn btn-secondary"><i class="fas fa-times"></i> Cancelar</a>
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Guardar Detalle</button>
                </div>
            </form>
        </div>
        
        <script src="/static/js/detail-calculator.js"></script>
        {error_script}
        """

        return Layout.render("Nuevo Detalle de Venta", user, "items-venta", content)

    @staticmethod
    def edit(user, detail, products, request, error=None):
        """Vista de formulario para editar detalle de venta"""

        csrf_token = get_token(request)

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

        # Select de productos
        product_options = ""
        for product in products:
            selected = "selected" if product["id"] == detail["producto_id"] else ""
            product_options += f'<option value="{product["id"]}" data-price="{product["precio_venta"]}" {selected}>{product["nombre"]} - $ {product["precio_venta"]:.2f}</option>'

        content = f"""
        <div class="card">
            <div class="card-header">
                <span><i class="fas fa-edit"></i> Editar Detalle de Venta</span>
                <a href="/items-venta/" class="btn btn-secondary">← Volver</a>
            </div>
            <form method="POST" action="/items-venta/{detail['id']}/editar/" class="p-20" id="detailForm" data-validate>
                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Venta</label>
                        <input type="text" value="{detail.get('numero_factura', 'Sin factura')}" disabled
                               class="form-input-disabled">
                        <small class="form-hint">La venta no se puede cambiar</small>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Producto *</label>
                        <select name="producto_id" id="producto" class="form-select"
                                data-rules="required"
                                data-label="Producto">
                            {product_options}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Cantidad *</label>
                        <input type="number" name="cantidad" id="cantidad" value="{detail['cantidad']}" min="1" class="form-input"
                               data-rules="required|numeric|min:1"
                               data-label="Cantidad">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Precio Unitario *</label>
                        <input type="number" name="precio_unitario" id="precio_unitario" value="{detail['precio_unitario']}" step="0.01" min="0" class="form-input"
                               data-rules="required|min:0"
                               data-label="Precio Unitario">
                    </div>
                </div>
                
                <div class="total-summary">
                    <p>
                        Subtotal: $ <span id="subtotal">{detail['subtotal']:.2f}</span>
                    </p>
                </div>
                
                <div class="form-actions-end mt-30">
                    <a href="/items-venta/" class="btn btn-secondary"><i class="fas fa-times"></i> Cancelar</a>
                    <button type="submit" class="btn btn-primary"><i class="fas fa-save"></i> Actualizar Detalle</button>
                </div>
            </form>
        </div>
        
        <script src="/static/js/detail-calculator.js"></script>
        {error_script}
        """

        return Layout.render("Editar Detalle de Venta", user, "items-venta", content)

    @staticmethod
    def view(user, detail):
        """Vista de detalle específico de venta"""

        estado_badge = {
            "pendiente": '<span class="badge badge-warning">Pendiente</span>',
            "completada": '<span class="badge badge-success">Completada</span>',
            "cancelada": '<span class="badge badge-cancelada">Cancelada</span>',
        }.get(detail.get("venta_estado", ""), detail.get("venta_estado", ""))

        content = f"""
        <div class="card">
            <div class="card-header">
                <span>Detalle de Venta #{detail['id']}</span>
                <a href="/items-venta/" class="btn btn-secondary">← Volver</a>
            </div>
            
            <div class="p-20">
                <div class="detail-info-section">
                    <h3>Información de la Venta</h3>
                    <div class="info-grid">
                        <div>
                            <p class="info-box-label">N° Factura</p>
                            <p class="info-box-value">{detail.get('numero_factura', 'Sin factura')}</p>
                        </div>
                        <div>
                            <p class="info-box-label">Cliente</p>
                            <p class="info-box-value">{detail['cliente_nombre']}</p>
                            <p class="form-hint">{detail.get('cliente_documento', '')}</p>
                        </div>
                        <div>
                            <p class="info-box-label">Fecha</p>
                            <p class="info-box-value">{detail['fecha_venta']}</p>
                        </div>
                        <div>
                            <p class="info-box-label">Tipo de Pago</p>
                            <p class="info-box-value">{detail.get('tipo_pago', 'N/A').capitalize()}</p>
                        </div>
                        <div>
                            <p class="info-box-label">Estado</p>
                            <p class="info-box-value">{estado_badge}</p>
                        </div>
                        <div>
                            <p class="info-box-label">Total Venta</p>
                            <p class="info-box-value text-success-lg">$ {detail['venta_total']:.2f}</p>
                        </div>
                    </div>
                </div>
                
                <h3>Detalle del Producto</h3>
                <div class="info-grid">
                    <div class="info-box-white">
                        <p class="info-box-label">Producto</p>
                        <p class="info-box-value">{detail['producto_nombre']}</p>
                    </div>
                    
                    <div class="info-box-white">
                        <p class="info-box-label">Cantidad</p>
                        <p class="info-box-value">{detail['cantidad']} unidades</p>
                    </div>
                    
                    <div class="info-box-white">
                        <p class="info-box-label">Precio Unitario</p>
                        <p class="info-box-value">$ {detail['precio_unitario']:.2f}</p>
                    </div>
                    
                    <div class="info-box-white">
                        <p class="info-box-label">Subtotal</p>
                        <p class="info-box-value text-success-lg">$ {detail['subtotal']:.2f}</p>
                    </div>
                </div>
                
                <div class="mt-30 d-flex gap-10">
                    <a href="/items-venta/{detail['id']}/editar/" class="btn btn-warning"><i class="fas fa-edit"></i> Editar Detalle</a>
                    <a href="/items-venta/" class="btn btn-secondary">Volver al Listado</a>
                </div>
            </div>
        </div>
        """

        return Layout.render("Ver Detalle de Venta", user, "items-venta", content)
